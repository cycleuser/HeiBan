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
)
from PySide6.QtCore import Qt, QUrl, QMargins, QTimer
from PySide6.QtGui import QFont, QAction, QPageLayout, QPageSize
from PySide6.QtWebEngineWidgets import QWebEngineView

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
        self.setMinimumSize(1000, 700)

        self.create_menu_bar()

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)

        label = QLabel("输入Markdown内容（使用 --- 分隔幻灯片，```mermaid 创建图表）：")
        main_layout.addWidget(label)

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
        main_layout.addWidget(self.md_textedit)

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
        md_content = self.md_textedit.toPlainText()
        if not md_content.strip():
            return

        path, _ = QFileDialog.getSaveFileName(
            self, "保存PDF文件", "", "PDF Files (*.pdf);;All Files (*)"
        )

        if not path:
            return

        try:
            from PySide6.QtGui import QTextDocument, QPageLayout
            from PySide6.QtCore import QMarginsF
            from PySide6.QtPrintSupport import QPrinter

            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(10)
            self.progress_bar.setFormat("正在生成PDF...")

            # Generate print-friendly HTML
            html = self._generate_print_html(md_content)

            self.progress_bar.setValue(50)
            self.progress_bar.setFormat("正在渲染PDF...")

            # Create text document
            doc = QTextDocument()
            doc.setHtml(html)

            # Setup printer
            printer = QPrinter(QPrinter.HighResolution)
            printer.setOutputFormat(QPrinter.PdfFormat)
            printer.setOutputFileName(path)
            printer.setPageSize(QPageSize(QPageSize.PageSizeId.A4))
            printer.setPageOrientation(QPageLayout.Orientation.Landscape)
            printer.setPageMargins(QMarginsF(20, 20, 20, 20))

            # Print to PDF
            doc.print_(printer)

            self.progress_bar.setVisible(False)
            QMessageBox.information(self, "成功", f"PDF已导出到：\n{path}")

        except Exception as e:
            self.progress_bar.setVisible(False)
            QMessageBox.critical(self, "错误", f"导出失败：{e}")

    def _generate_print_html(self, md_content: str) -> str:
        """生成适合打印的HTML"""
        # Parse slides
        slides = self.converter.parse_markdown(md_content)

        # Generate print-friendly HTML
        is_dark = self.converter.code_theme == "dark"

        page_bg = "#000000" if is_dark else "#ffffff"
        page_text = "#f0f0f0" if is_dark else "#24292e"
        page_heading = "#4da6ff" if is_dark else "#005cc5"
        pre_bg = "#1a1a1a" if is_dark else "#f6f8fa"
        inline_code_bg = "#2d2d2d" if is_dark else "#e6f3ff"
        inline_code_text = "#ffcc66" if is_dark else "#d73a49"

        slides_html = []
        for i, slide in enumerate(slides):
            slide_content = self.converter.convert_markdown_to_html(slide)
            slides_html.append(f"""
    <div class="slide" style="page-break-after: always; padding: 40px; min-height: 90vh; box-sizing: border-box;">
        {slide_content.replace("            <section>", "").replace("            </section>", "")}
    </div>
""")

        html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>幻灯片</title>
    <style>
@page {{
    size: A4 landscape;
    margin: 0;
}}
* {{
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}}
body {{
    background: {page_bg};
    color: {page_text};
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif;
    font-size: 20px;
    line-height: 1.6;
}}
h1 {{
    font-size: 2.5em;
    color: {page_heading};
    margin-bottom: 0.5em;
}}
h2 {{
    font-size: 2em;
    color: {page_heading};
    margin-bottom: 0.5em;
}}
h3 {{
    font-size: 1.5em;
    color: {page_heading};
}}
ul, ol {{
    margin-left: 2em;
    margin-bottom: 1em;
}}
li {{
    margin: 0.5em 0;
}}
code {{
    background: {inline_code_bg};
    color: {inline_code_text};
    padding: 0.2em 0.4em;
    border-radius: 3px;
    font-family: 'Consolas', 'Monaco', monospace;
    font-size: 0.9em;
}}
pre {{
    background: {pre_bg};
    padding: 1em;
    border-radius: 8px;
    overflow-x: auto;
    margin: 1em 0;
}}
pre code {{
    background: transparent;
    padding: 0;
}}
table {{
    width: 100%;
    border-collapse: collapse;
    margin: 1em 0;
}}
th {{
    background: {page_heading};
    color: white;
    padding: 0.5em;
    text-align: left;
}}
td {{
    padding: 0.5em;
    border: 1px solid {"#333333" if is_dark else "#d1d9e0"};
}}
    </style>
</head>
<body>
{"".join(slides_html)}
</body>
</html>"""

        return html

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
