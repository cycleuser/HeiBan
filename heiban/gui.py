#!/usr/bin/env python3
"""
HeiBan GUI - PySide6图形界面
"""

import os
import sys
import tempfile
import webbrowser
import shutil
import threading
import http.server
from pathlib import Path
from typing import Optional

from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QFileDialog,
    QMessageBox,
    QGroupBox,
    QComboBox,
    QSpinBox,
    QProgressBar,
    QTabWidget,
    QPlainTextEdit,
    QCheckBox,
)
from PySide6.QtCore import Qt, QThread, Signal, QSize
from PySide6.QtGui import QFont

from .converter import MarkdownToSlideConverter


class ConversionThread(QThread):
    """转换线程"""

    finished = Signal(str)
    error = Signal(str)
    progress = Signal(int, str)

    def __init__(self, converter: MarkdownToSlideConverter, md_content: str, output_path: str):
        super().__init__()
        self.converter = converter
        self.md_content = md_content
        self.output_path = output_path

    def run(self):
        try:
            self.progress.emit(30, "正在转换markdown...")
            html = self.converter.generate_html(self.md_content, "幻灯片")

            self.progress.emit(60, "正在写入文件...")
            with open(self.output_path, "w", encoding="utf-8") as f:
                f.write(html)

            self.progress.emit(100, "完成！")
            self.finished.emit(self.output_path)
        except Exception as e:
            self.error.emit(str(e))


class MainWindow(QMainWindow):
    """主窗口"""

    def __init__(self):
        super().__init__()
        self.converter = MarkdownToSlideConverter()
        self.current_file: Optional[str] = None
        self.thread: Optional[ConversionThread] = None
        self.server_thread: Optional[threading.Thread] = None
        self.temp_dir: Optional[str] = None
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("HeiBan - Mermaid转HTML幻灯片")
        self.setMinimumSize(1000, 700)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)

        # 顶部设置区域
        settings_group = QGroupBox("输出设置")
        settings_layout = QHBoxLayout()

        # 幻灯片宽高比
        ratio_layout = QVBoxLayout()
        ratio_layout.addWidget(QLabel("宽高比"))
        ratio_combo = QComboBox()
        ratio_combo.addItems(["16:9 (宽屏)", "4:3 (普屏)", "21:9 (超宽)", "3:2 (标准)"])
        ratio_combo.currentIndexChanged.connect(self.on_ratio_changed)
        self.ratio_combo = ratio_combo
        ratio_layout.addWidget(ratio_combo)
        settings_layout.addLayout(ratio_layout)

        # 字体大小
        font_layout = QVBoxLayout()
        font_layout.addWidget(QLabel("字体大小"))
        font_spin = QSpinBox()
        font_spin.setRange(16, 40)
        font_spin.setValue(26)
        font_spin.valueChanged.connect(self.on_font_size_changed)
        self.font_spin = font_spin
        font_layout.addWidget(font_spin)
        settings_layout.addLayout(font_layout)

        # Mermaid主题
        theme_layout = QVBoxLayout()
        theme_layout.addWidget(QLabel("Mermaid主题"))
        theme_combo = QComboBox()
        theme_combo.addItems(["default", "neutral", "dark", "base"])
        theme_combo.currentIndexChanged.connect(self.on_theme_changed)
        self.theme_combo = theme_combo
        theme_layout.addWidget(theme_combo)
        settings_layout.addLayout(theme_layout)

        # 代码高亮主题
        code_theme_layout = QVBoxLayout()
        code_theme_layout.addWidget(QLabel("代码高亮"))
        code_theme_combo = QComboBox()
        code_theme_combo.addItems(["dark (暗色)", "light (亮色)"])
        code_theme_combo.currentIndexChanged.connect(self.on_code_theme_changed)
        self.code_theme_combo = code_theme_combo
        code_theme_layout.addWidget(code_theme_combo)
        settings_layout.addLayout(code_theme_layout)

        settings_layout.addStretch()
        settings_group.setLayout(settings_layout)
        main_layout.addWidget(settings_group)

        # Tab区域
        tab_widget = QTabWidget()
        tab_widget.addTab(self.create_input_tab(), "Markdown输入")
        tab_widget.addTab(self.create_preview_tab(), "预览")
        main_layout.addWidget(tab_widget)

        # 底部按钮区域
        bottom_layout = QHBoxLayout()

        self.open_btn = QPushButton("打开Markdown文件")
        self.open_btn.clicked.connect(self.open_file)
        bottom_layout.addWidget(self.open_btn)

        self.save_btn = QPushButton("保存HTML文件")
        self.save_btn.clicked.connect(self.save_file)
        self.save_btn.setEnabled(False)
        bottom_layout.addWidget(self.save_btn)

        self.convert_btn = QPushButton("转换为HTML")
        self.convert_btn.clicked.connect(self.convert)
        self.convert_btn.setEnabled(False)
        bottom_layout.addWidget(self.convert_btn)

        self.preview_btn = QPushButton("浏览器预览")
        self.preview_btn.clicked.connect(self.preview)
        self.preview_btn.setEnabled(False)
        bottom_layout.addWidget(self.preview_btn)

        bottom_layout.addStretch()

        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximumWidth(200)
        self.progress_bar.setVisible(False)
        bottom_layout.addWidget(self.progress_bar)

        main_layout.addLayout(bottom_layout)

    def create_input_tab(self) -> QWidget:
        """创建输入Tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        label = QLabel(
            "输入Markdown内容（使用 --- / — / *** 分隔幻灯片，使用 ```mermaid 分隔图表）："
        )
        layout.addWidget(label)

        self.md_textedit = QPlainTextEdit()
        self.md_textedit.setPlaceholderText("""示例格式：

# 第1章 标题

## 第一页内容

- 列表项1
- 列表项2

```
#include <stdio.h>
int main() { return 0; }
```

---

## 第二页内容

```mermaid
flowchart LR
    A --> B
```

""")
        self.md_textedit.textChanged.connect(self.on_text_changed)
        layout.addWidget(self.md_textedit)

        return widget

    def create_preview_tab(self) -> QWidget:
        """创建预览Tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        label = QLabel("转换后的HTML代码预览：")
        layout.addWidget(label)

        self.preview_textedit = QPlainTextEdit()
        self.preview_textedit.setReadOnly(True)
        self.preview_textedit.setFont(QFont("Courier New", 9))
        layout.addWidget(self.preview_textedit)

        return widget

    def on_ratio_changed(self, index: int):
        ratios = ["16:9", "4:3", "21:9", "3:2"]
        if index < len(ratios):
            self.converter.set_aspect_ratio(ratios[index])

    def on_font_size_changed(self, value: int):
        self.converter.font_size = value

    def on_theme_changed(self, index: int):
        themes = ["default", "neutral", "dark", "base"]
        if index < len(themes):
            self.converter.mermaid_theme = themes[index]

    def on_code_theme_changed(self, index: int):
        self.converter.code_theme = "dark" if index == 0 else "light"

    def on_text_changed(self):
        has_content = bool(self.md_textedit.toPlainText().strip())
        self.convert_btn.setEnabled(has_content)
        self.save_btn.setEnabled(has_content)
        self.preview_btn.setEnabled(has_content)

    def open_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "打开Markdown文件",
            "",
            "Markdown Files (*.md *.markdown);;All Files (*)",
        )
        if path:
            try:
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                self.md_textedit.setPlainText(content)
                self.current_file = path
                self.setWindowTitle(f"HeiBan - {Path(path).name}")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"无法打开文件：{e}")

    def save_file(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "保存HTML文件", "", "HTML Files (*.html);;All Files (*)"
        )
        if path:
            try:
                md_content = self.md_textedit.toPlainText()
                html = self.converter.generate_html(md_content, "幻灯片")
                with open(path, "w", encoding="utf-8") as f:
                    f.write(html)
                QMessageBox.information(self, "成功", f"已保存到：{path}")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"无法保存文件：{e}")

    def convert(self):
        md_content = self.md_textedit.toPlainText()
        if not md_content.strip():
            QMessageBox.warning(self, "警告", "请先输入内容")
            return

        # 更新预览
        html = self.converter.generate_html(md_content, "幻灯片")
        self.preview_textedit.setPlainText(html)

        # 显示进度
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(30)
        self.progress_bar.setFormat("转换中... %p%")

        # 模拟进度并转换
        self.thread = ConversionThread(self.converter, md_content, "output.html")
        self.thread.progress.connect(self.on_progress)
        self.thread.finished.connect(self.on_conversion_finished)
        self.thread.error.connect(self.on_conversion_error)
        self.thread.start()

    def on_progress(self, value: int, message: str):
        self.progress_bar.setValue(value)
        self.progress_bar.setFormat(f"{message}... %p%")

    def on_conversion_finished(self, path: str):
        self.progress_bar.setVisible(False)
        QMessageBox.information(self, "成功", f"转换完成！\n文件已保存到：{path}")

    def on_conversion_error(self, error: str):
        self.progress_bar.setVisible(False)
        QMessageBox.critical(self, "错误", f"转换失败：{error}")

    def preview(self):
        md_content = self.md_textedit.toPlainText()
        if not md_content.strip():
            return

        # 生成自包含HTML
        html = self.converter.generate_html(md_content, "预览")

        # 创建临时目录和文件
        self.temp_dir = tempfile.mkdtemp()
        temp_html = os.path.join(self.temp_dir, "preview.html")

        # 写入HTML
        with open(temp_html, "w", encoding="utf-8") as f:
            f.write(html)

        # 停止之前的服务器
        self._stop_server()

        # 启动HTTP服务器
        self.server_thread = threading.Thread(
            target=self._run_server, args=(self.temp_dir,), daemon=True
        )
        self.server_thread.start()

        # 打开浏览器
        webbrowser.open("http://localhost:8765/preview.html")

        QMessageBox.information(
            self, "预览", "已在浏览器中打开预览页面\n服务器运行在 http://localhost:8765"
        )

    def _run_server(self, temp_dir: str):
        """运行HTTP服务器"""
        os.chdir(temp_dir)
        try:
            http.server.HTTPServer(
                ("localhost", 8765), http.server.SimpleHTTPRequestHandler
            ).serve_forever()
        except Exception:
            pass  # 服务器停止时忽略错误

    def _stop_server(self):
        """停止服务器"""
        import socket

        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect(("localhost", 8765))
            sock.close()
        except Exception:
            pass

    def closeEvent(self, event):
        """关闭窗口时清理"""
        self._stop_server()
        if self.temp_dir and os.path.exists(self.temp_dir):
            try:
                shutil.rmtree(self.temp_dir)
            except Exception:
                pass
        event.accept()


def run_gui():
    """运行GUI"""
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    run_gui()
