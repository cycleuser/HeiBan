#!/usr/bin/env python3
"""
HeiBan GUI - PySide6图形界面
"""

import os
import sys
import tempfile
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
    QProgressBar,
    QPlainTextEdit,
    QMenuBar,
    QTabWidget,
)
from PySide6.QtCore import Qt, QUrl, QMargins, QTimer
from PySide6.QtGui import QFont, QAction, QPageLayout, QPageSize
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtPrintSupport import QPrinter

from .converter import MarkdownToSlideConverter


class MainWindow(QMainWindow):
    """主窗口"""

    def __init__(self):
        super().__init__()
        self.converter = MarkdownToSlideConverter()
        self.current_file: Optional[str] = None
        self.temp_dir: Optional[str] = None
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("HeiBan - Mermaid转HTML幻灯片")
        self.setMinimumSize(1200, 800)

        self.create_menu_bar()

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)

        # Tab widget for input and preview
        tab_widget = QTabWidget()
        tab_widget.addTab(self.create_input_tab(), "Markdown输入")
        tab_widget.addTab(self.create_preview_tab(), "HTML预览")
        main_layout.addWidget(tab_widget)

        # Bottom buttons
        bottom_layout = QHBoxLayout()

        self.open_btn = QPushButton("打开Markdown文件")
        self.open_btn.clicked.connect(self.open_file)
        bottom_layout.addWidget(self.open_btn)

        self.save_btn = QPushButton("保存HTML文件")
        self.save_btn.clicked.connect(self.save_file)
        self.save_btn.setEnabled(False)
        bottom_layout.addWidget(self.save_btn)

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

    def create_input_tab(self) -> QWidget:
        """创建输入Tab"""
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
        """创建预览Tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        self.web_view = QWebEngineView()
        layout.addWidget(self.web_view)

        preview_btn = QPushButton("刷新预览")
        preview_btn.clicked.connect(self.refresh_preview)
        layout.addWidget(preview_btn)

        return widget

    def refresh_preview(self):
        """刷新HTML预览"""
        md_content = self.md_textedit.toPlainText()
        if not md_content.strip():
            return

        try:
            html = self.converter.generate_html(md_content, "预览")

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

    def on_text_changed(self):
        has_content = bool(self.md_textedit.toPlainText().strip())
        self.save_btn.setEnabled(has_content)
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

    def export_pdf(self):
        """导出PDF - 使用reveal.js的print-pdf模式"""
        md_content = self.md_textedit.toPlainText()
        if not md_content.strip():
            return

        path, _ = QFileDialog.getSaveFileName(
            self, "保存PDF文件", "", "PDF Files (*.pdf);;All Files (*)"
        )

        if not path:
            return

        try:
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(10)
            self.progress_bar.setFormat("正在生成HTML...")

            # 生成HTML
            html = self.converter.generate_html(md_content, "幻灯片")

            # 添加打印专用样式
            print_style = """
<style>
@media print {
    .reveal .slides section {
        page-break-after: always !important;
        page-break-inside: avoid !important;
    }
    .reveal .slides section:last-child {
        page-break-after: avoid !important;
    }
    html, body {
        background-color: %s !important;
        -webkit-print-color-adjust: exact !important;
        color-adjust: exact !important;
    }
    .reveal {
        background-color: %s !important;
    }
    .reveal-viewport {
        background-color: %s !important;
    }
}
</style>
"""

            # 根据主题设置背景色
            is_dark = self.converter.code_theme == "dark"
            bg_color = "#000000" if is_dark else "#ffffff"
            print_style = print_style % (bg_color, bg_color, bg_color)

            # 插入打印样式到head中
            html = html.replace("</head>", print_style + "</head>")

            # 保存临时HTML文件
            if not self.temp_dir:
                self.temp_dir = tempfile.mkdtemp()
            temp_html = os.path.join(self.temp_dir, "slides.html")

            with open(temp_html, "w", encoding="utf-8") as f:
                f.write(html)

            self.progress_bar.setValue(30)
            self.progress_bar.setFormat("正在加载幻灯片...")

            # 创建可见的WebView（避免segmentation fault）
            self.pdf_view = QWebEngineView()
            self.pdf_view.setWindowTitle("正在生成PDF...")
            self.pdf_view.resize(1200, 800)
            self.pdf_view.show()

            # 使用reveal.js的print-pdf模式
            pdf_url = QUrl.fromLocalFile(temp_html)
            pdf_url.setQuery("print-pdf")

            self.pdf_view.setUrl(pdf_url)
            self.pdf_path = path

            # 等待加载完成后生成PDF
            self.pdf_view.loadFinished.connect(self._on_pdf_load_finished)

        except Exception as e:
            self.progress_bar.setVisible(False)
            QMessageBox.critical(self, "错误", f"导出失败：{e}")

    def _on_pdf_load_finished(self, ok: bool):
        """HTML加载完成后的回调"""
        if not ok:
            self.progress_bar.setVisible(False)
            QMessageBox.critical(self, "错误", "幻灯片加载失败")
            return

        try:
            self.progress_bar.setValue(50)
            self.progress_bar.setFormat("正在渲染JavaScript...")

            # 等待reveal.js、mermaid、highlight.js渲染完成
            # 增加等待时间到5秒
            QTimer.singleShot(5000, self._generate_pdf)

        except Exception as e:
            self.progress_bar.setVisible(False)
            QMessageBox.critical(self, "错误", f"PDF生成失败：{e}")

    def _generate_pdf(self):
        """生成PDF"""
        try:
            from PySide6.QtGui import QPageLayout
            from PySide6.QtCore import QMarginsF

            self.progress_bar.setValue(70)
            self.progress_bar.setFormat("正在生成PDF...")

            # 检查WebView是否还存在
            if not self.pdf_view:
                self.progress_bar.setVisible(False)
                return

            page = self.pdf_view.page()

            # 设置页面布局 - 横向A4，无边距
            layout = QPageLayout(
                QPageSize(QPageSize.PageSizeId.A4),
                QPageLayout.Orientation.Landscape,
                QMarginsF(0, 0, 0, 0),
            )

            # 生成PDF
            page.printToPdf(lambda data: self._on_pdf_generated(data), layout)

        except Exception as e:
            self.progress_bar.setVisible(False)
            QMessageBox.critical(self, "错误", f"PDF生成失败：{e}")

    def _on_pdf_generated(self, data: bytes):
        """PDF生成完成回调"""
        try:
            if not data:
                self.progress_bar.setVisible(False)
                QMessageBox.critical(self, "错误", "PDF数据为空")
                return

            # 保存PDF文件
            with open(self.pdf_path, "wb") as f:
                f.write(data)

            self.progress_bar.setVisible(False)

            # 延迟关闭WebView，避免崩溃
            QTimer.singleShot(500, self._cleanup_pdf_view)

            QMessageBox.information(self, "成功", f"PDF已导出到：\n{self.pdf_path}")

        except Exception as e:
            self.progress_bar.setVisible(False)
            QMessageBox.critical(self, "错误", f"保存失败：{e}")

    def _cleanup_pdf_view(self):
        """清理WebView"""
        try:
            if hasattr(self, "pdf_view") and self.pdf_view:
                self.pdf_view.close()
                self.pdf_view.deleteLater()
                self.pdf_view = None
        except:
            pass

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
