#!/usr/bin/env python3
"""
HeiBan GUI - PySide6图形界面
"""

import os
import sys
import tempfile
import webbrowser
import shutil
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
    QMenuBar,
    QMenu,
    QToolBar,
)
from PySide6.QtCore import Qt, QThread, Signal, QSize, QUrl
from PySide6.QtGui import QFont, QAction
from PySide6.QtWebEngineWidgets import QWebEngineView

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
        self.temp_dir: Optional[str] = None
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("HeiBan - Mermaid转HTML幻灯片")
        self.setMinimumSize(1000, 700)

        self.create_menu_bar()

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)

        tab_widget = QTabWidget()
        tab_widget.addTab(self.create_input_tab(), "Markdown输入")
        tab_widget.addTab(self.create_preview_tab(), "预览")
        main_layout.addWidget(tab_widget)

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

        self.pdf_btn = QPushButton("导出PDF")
        self.pdf_btn.clicked.connect(self.export_pdf)
        self.pdf_btn.setEnabled(False)
        bottom_layout.addWidget(self.pdf_btn)

        bottom_layout.addStretch()

        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximumWidth(200)
        self.progress_bar.setVisible(False)
        bottom_layout.addWidget(self.progress_bar)

        main_layout.addLayout(bottom_layout)

    def create_menu_bar(self):
        menubar = self.menuBar()

        file_menu = menubar.addMenu("文件")

        open_action = QAction("打开Markdown", self)
        open_action.triggered.connect(self.open_file)
        file_menu.addAction(open_action)

        save_action = QAction("保存HTML", self)
        save_action.triggered.connect(self.save_file)
        file_menu.addAction(save_action)

        settings_menu = menubar.addMenu("设置")

        ratio_menu = settings_menu.addMenu("宽高比")
        ratio_actions = ["16:9 (宽屏)", "4:3 (普屏)", "21:9 (超宽)", "3:2 (标准)"]
        for action_text in ratio_actions:
            action = QAction(action_text, self)
            action.triggered.connect(
                lambda checked, text=action_text: self.on_ratio_menu_changed(text)
            )
            ratio_menu.addAction(action)

        font_menu = settings_menu.addMenu("字体大小")
        for size in range(16, 41, 2):
            action = QAction(f"{size}px", self)
            action.triggered.connect(lambda checked, s=size: self.set_font_size(s))
            font_menu.addAction(action)

        theme_menu = settings_menu.addMenu("Mermaid主题")
        themes = ["default", "neutral", "dark", "base"]
        for theme in themes:
            action = QAction(theme, self)
            action.triggered.connect(lambda checked, t=theme: self.set_mermaid_theme(t))
            theme_menu.addAction(action)

        code_theme_menu = settings_menu.addMenu("代码高亮主题")
        code_themes = ["dark (暗色)", "light (亮色)"]
        for code_theme in code_themes:
            action = QAction(code_theme, self)
            action.triggered.connect(
                lambda checked, ct=code_theme: self.set_code_theme(ct.split()[0])
            )
            code_theme_menu.addAction(action)

    def on_ratio_menu_changed(self, text: str):
        ratio = text.split()[0]
        self.converter.set_aspect_ratio(ratio)

    def set_font_size(self, size: int):
        self.converter.font_size = size

    def set_mermaid_theme(self, theme: str):
        self.converter.mermaid_theme = theme

    def set_code_theme(self, theme: str):
        self.converter.code_theme = theme

    def create_input_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)

        label = QLabel("输入Markdown内容（使用 --- 分隔幻灯片，```mermaid 创建图表）：")
        layout.addWidget(label)

        self.md_textedit = QPlainTextEdit()
        self.md_textedit.setPlaceholderText("""# 示例标题

## 第一页

- 列表项1
- 列表项2

```python
print("Hello World")
```

---

## 第二页

```mermaid
flowchart LR
    A --> B
```
""")
        self.md_textedit.textChanged.connect(self.on_text_changed)
        layout.addWidget(self.md_textedit)

        return widget

    def create_preview_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)

        self.web_view = QWebEngineView()
        layout.addWidget(self.web_view)

        refresh_btn = QPushButton("刷新预览")
        refresh_btn.clicked.connect(self.refresh_preview)
        layout.addWidget(refresh_btn)

        return widget

    def refresh_preview(self):
        md_content = self.md_textedit.toPlainText()
        if not md_content.strip():
            return

        try:
            html = self.converter.generate_html(md_content, "预览", use_cdn=False)

            if self.temp_dir:
                try:
                    shutil.rmtree(self.temp_dir)
                except:
                    pass

            self.temp_dir = tempfile.mkdtemp()
            temp_html = os.path.join(self.temp_dir, "preview.html")

            with open(temp_html, "w", encoding="utf-8") as f:
                f.write(html)

            self.web_view.setUrl(QUrl.fromLocalFile(temp_html))
        except Exception as e:
            QMessageBox.warning(self, "预览错误", f"生成预览失败: {e}")

    def on_text_changed(self):
        has_content = bool(self.md_textedit.toPlainText().strip())
        self.convert_btn.setEnabled(has_content)
        self.save_btn.setEnabled(has_content)
        self.preview_btn.setEnabled(has_content)
        self.pdf_btn.setEnabled(has_content)

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

        self.refresh_preview()

        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(30)
        self.progress_bar.setFormat("转换中... %p%")

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

        html = self.converter.generate_html(md_content, "预览")

        self.temp_dir = tempfile.mkdtemp()
        temp_html = os.path.join(self.temp_dir, "preview.html")

        with open(temp_html, "w", encoding="utf-8") as f:
            f.write(html)

        webbrowser.open(f"file://{temp_html}")

    def export_pdf(self):
        md_content = self.md_textedit.toPlainText()
        if not md_content.strip():
            return

        path, _ = QFileDialog.getSaveFileName(
            self, "保存PDF文件", "", "PDF Files (*.pdf);;All Files (*)"
        )

        if not path:
            return

        try:
            html = self.converter.generate_html(md_content, "幻灯片", use_cdn=False)

            print_html = html.replace("<!DOCTYPE html>", "<!DOCTYPE html>\n<!-- PDF Print Mode -->")

            print_html = print_html.replace(
                "Reveal.initialize({",
                "Reveal.initialize({ hash: false, embedded: true, printWidth: 1200,",
            )

            self.temp_dir = tempfile.mkdtemp()
            temp_html = os.path.join(self.temp_dir, "print.html")

            with open(temp_html, "w", encoding="utf-8") as f:
                f.write(print_html)

            msg = QMessageBox(self)
            msg.setWindowTitle("导出PDF")
            msg.setText(
                "PDF导出方法：\n\n1. 浏览器将打开幻灯片\n2. 按 Cmd+P (Mac) 或 Ctrl+P (Windows)\n3. 选择'保存为PDF'\n4. 在打印设置中选择'纵向'\n5. 勾选'背景图形'选项"
            )
            msg.addButton("打开浏览器", QMessageBox.AcceptRole)
            msg.addButton("取消", QMessageBox.RejectRole)

            if msg.exec() == QMessageBox.AcceptRole:
                webbrowser.open(f"file://{temp_html}?print-pdf")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"导出失败：{e}")

    def closeEvent(self, event):
        """关闭窗口时清理"""
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
