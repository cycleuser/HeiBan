#!/usr/bin/env python3
"""
HeiBan GUI - PySide6图形界面
支持导出: HTML, PDF, PPTX
"""

import os
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Optional

from PySide6.QtCore import QThread, QTimer, QUrl, Signal
from PySide6.QtGui import QAction
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from .converter import MarkdownToSlideConverter


class ExportWorker(QThread):
    """后台导出工作线程"""
    finished = Signal(str)
    error = Signal(str)

    def __init__(self, export_func, *args, **kwargs):
        super().__init__()
        self.export_func = export_func
        self.args = args
        self.kwargs = kwargs

    def run(self):
        try:
            result = self.export_func(*self.args, **self.kwargs)
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))


class MainWindow(QMainWindow):
    """主窗口"""

    def __init__(self):
        super().__init__()
        self.converter = MarkdownToSlideConverter()
        self.v2_converter = None
        self.current_file: Optional[str] = None
        self.temp_dir: Optional[str] = None
        self._export_worker: Optional[ExportWorker] = None
        self.init_ui()

    def _get_v2_converter(self):
        """懒加载 v2 转换器"""
        if self.v2_converter is None:
            try:
                from .v2.converter import MarkdownToSlideConverterV2
                self.v2_converter = MarkdownToSlideConverterV2()
                self.v2_converter.theme = "black"
                self.v2_converter.aspect_ratio = "16:9"
            except ImportError as e:
                QMessageBox.warning(self, "错误", f"v2 转换器不可用: {e}")
                return None
        return self.v2_converter

    def init_ui(self):
        self.setWindowTitle("HeiBan - Markdown 转 HTML 幻灯片")
        self.setMinimumSize(1200, 800)

        self.create_menu_bar()

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)

        tab_widget = QTabWidget()
        tab_widget.addTab(self.create_input_tab(), "Markdown 输入")
        tab_widget.addTab(self.create_preview_tab(), "HTML 预览")
        main_layout.addWidget(tab_widget)

        bottom_layout = QHBoxLayout()

        self.open_btn = QPushButton("打开 Markdown")
        self.open_btn.clicked.connect(self.open_file)
        bottom_layout.addWidget(self.open_btn)

        self.save_btn = QPushButton("保存 HTML")
        self.save_btn.clicked.connect(self.save_file)
        self.save_btn.setEnabled(False)
        bottom_layout.addWidget(self.save_btn)

        self.pdf_btn = QPushButton("导出 PDF")
        self.pdf_btn.clicked.connect(self.export_pdf)
        self.pdf_btn.setEnabled(False)
        bottom_layout.addWidget(self.pdf_btn)

        self.pptx_btn = QPushButton("导出 PPTX")
        self.pptx_btn.setStyleSheet(
            "QPushButton { background-color: #4CAF50; color: white; font-weight: bold; padding: 5px 15px; border-radius: 3px; }"
            "QPushButton:hover { background-color: #45a049; }"
            "QPushButton:disabled { background-color: #cccccc; color: #666666; }"
        )
        self.pptx_btn.clicked.connect(self.export_pptx)
        self.pptx_btn.setEnabled(False)
        bottom_layout.addWidget(self.pptx_btn)

        bottom_layout.addStretch()

        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximumWidth(200)
        self.progress_bar.setVisible(False)
        bottom_layout.addWidget(self.progress_bar)

        main_layout.addLayout(bottom_layout)

        self.statusBar().showMessage("就绪")

    def create_input_tab(self) -> QWidget:
        """创建输入Tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        label = QLabel("输入 Markdown 内容（使用 --- 分隔幻灯片，```mermaid 创建图表）：")
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
            v2 = self._get_v2_converter()
            if v2:
                if self.current_file:
                    v2.image_base_path = Path(self.current_file).parent
                html = v2.convert(md_content, "预览", use_cdn=True)
            else:
                html = self.converter.generate_html(md_content, "预览", use_cdn=True)

            if self.temp_dir:
                try:
                    shutil.rmtree(self.temp_dir)
                except Exception:
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

        open_action = QAction("打开 Markdown", self)
        open_action.triggered.connect(self.open_file)
        file_menu.addAction(open_action)

        save_action = QAction("保存 HTML", self)
        save_action.triggered.connect(self.save_file)
        file_menu.addAction(save_action)

        file_menu.addSeparator()

        pdf_action = QAction("导出 PDF", self)
        pdf_action.triggered.connect(self.export_pdf)
        file_menu.addAction(pdf_action)

        pptx_action = QAction("导出 PPTX (PowerPoint)", self)
        pptx_action.triggered.connect(self.export_pptx)
        file_menu.addAction(pptx_action)

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

        reveal_theme_menu = settings_menu.addMenu("reveal.js 主题 (PPTX/PDF)")
        for rtheme in ["black", "white", "league", "beige", "sky", "night", "moon", "blood", "solarized"]:
            action = QAction(rtheme, self)
            action.triggered.connect(lambda checked, t=rtheme: self.set_reveal_theme(t))
            reveal_theme_menu.addAction(action)

    def on_ratio_menu_changed(self, text: str):
        ratio = text.split()[0]
        self.converter.set_aspect_ratio(ratio)
        v2 = self._get_v2_converter()
        if v2:
            v2.set_aspect_ratio(ratio)

    def set_font_size(self, size: int):
        self.converter.font_size = size
        v2 = self._get_v2_converter()
        if v2:
            v2.font_size = size

    def set_mermaid_theme(self, theme: str):
        self.converter.mermaid_theme = theme

    def set_code_theme(self, theme: str):
        self.converter.code_theme = theme

    def set_reveal_theme(self, theme: str):
        v2 = self._get_v2_converter()
        if v2:
            v2.theme = theme

    def on_text_changed(self):
        has_content = bool(self.md_textedit.toPlainText().strip())
        self.save_btn.setEnabled(has_content)
        self.pdf_btn.setEnabled(has_content)
        self.pptx_btn.setEnabled(has_content)

    def open_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "打开Markdown文件",
            "",
            "Markdown Files (*.md *.markdown);;All Files (*)",
        )
        if path:
            try:
                with open(path, encoding="utf-8") as f:
                    content = f.read()
                self.md_textedit.setPlainText(content)
                self.current_file = path
                self.setWindowTitle(f"HeiBan - {Path(path).name}")
                self.statusBar().showMessage(f"已打开: {path}")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"无法打开文件：{e}")

    def save_file(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "保存HTML文件", "", "HTML Files (*.html);;All Files (*)"
        )
        if path:
            try:
                md_content = self.md_textedit.toPlainText()
                v2 = self._get_v2_converter()
                if v2:
                    html = v2.convert(md_content, "幻灯片")
                else:
                    html = self.converter.generate_html(md_content, "幻灯片")
                with open(path, "w", encoding="utf-8") as f:
                    f.write(html)
                self.statusBar().showMessage(f"HTML 已保存: {path}")
                QMessageBox.information(self, "成功", f"已保存到：{path}")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"无法保存文件：{e}")

    def export_pdf(self):
        """导出 PDF"""
        md_content = self.md_textedit.toPlainText()
        if not md_content.strip():
            return

        path, _ = QFileDialog.getSaveFileName(
            self, "保存PDF文件", "", "PDF Files (*.pdf);;All Files (*)"
        )
        if not path:
            return

        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(10)
        self.statusBar().showMessage("正在导出 PDF...")

        try:
            from .pdf_exporter import PDFExporter

            v2 = self._get_v2_converter()
            if v2:
                if self.current_file:
                    v2.image_base_path = Path(self.current_file).parent
                html_content = v2.convert(md_content, "幻灯片", use_cdn=True)
            else:
                html_content = self.converter.generate_html(md_content, "幻灯片", use_cdn=True)

            exporter = PDFExporter()
            exporter.landscape = True

            def do_export():
                return exporter.export_html_content(html_content, path)

            self._export_worker = ExportWorker(do_export)
            self._export_worker.finished.connect(self._on_pdf_export_done)
            self._export_worker.error.connect(self._on_export_error)
            self._export_worker.start()

        except Exception as e:
            self.progress_bar.setVisible(False)
            QMessageBox.critical(self, "错误", f"导出失败：{e}")

    def _on_pdf_export_done(self, result_path: str):
        self.progress_bar.setVisible(False)
        self.statusBar().showMessage(f"PDF 已导出: {result_path}")
        QMessageBox.information(self, "成功", f"PDF 已导出到：\n{result_path}")

    def export_pptx(self):
        """导出 PPTX"""
        md_content = self.md_textedit.toPlainText()
        if not md_content.strip():
            return

        path, _ = QFileDialog.getSaveFileName(
            self, "保存PPTX文件", "", "PowerPoint Files (*.pptx);;All Files (*)"
        )
        if not path:
            return

        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(10)
        self.statusBar().showMessage("正在导出 PPTX...")

        try:
            from .pptx_exporter import PPTXExporter
            from .v2.md_parser import MarkdownSlideParser

            v2 = self._get_v2_converter()
            theme = v2.theme if v2 else "black"
            ratio = v2.aspect_ratio if v2 else "16:9"

            parser = MarkdownSlideParser()
            slides = parser.parse(md_content)

            exporter = PPTXExporter()
            exporter.theme = theme
            exporter.aspect_ratio = ratio

            def do_export():
                return exporter.export(slides, path)

            self._export_worker = ExportWorker(do_export)
            self._export_worker.finished.connect(self._on_pptx_export_done)
            self._export_worker.error.connect(self._on_export_error)
            self._export_worker.start()

        except Exception as e:
            self.progress_bar.setVisible(False)
            QMessageBox.critical(self, "错误", f"导出失败：{e}")

    def _on_pptx_export_done(self, result_path: str):
        self.progress_bar.setVisible(False)
        self.statusBar().showMessage(f"PPTX 已导出: {result_path}")
        QMessageBox.information(self, "成功", f"PPTX 已导出到：\n{result_path}")

    def _on_export_error(self, error_msg: str):
        self.progress_bar.setVisible(False)
        self.statusBar().showMessage("导出失败")
        QMessageBox.critical(self, "错误", f"导出失败：{error_msg}")

    def _on_pdf_load_finished(self, ok: bool):
        """HTML加载完成后的回调 (QWebEngineView PDF)"""
        if not ok:
            self.progress_bar.setVisible(False)
            QMessageBox.critical(self, "错误", "幻灯片加载失败")
            return

        try:
            self.progress_bar.setValue(50)
            self.progress_bar.setFormat("正在渲染...")

            QTimer.singleShot(5000, self._generate_pdf)

        except Exception as e:
            self.progress_bar.setVisible(False)
            QMessageBox.critical(self, "错误", f"PDF生成失败：{e}")

    def _generate_pdf(self):
        """使用 QWebEngineView 生成 PDF (fallback)"""
        try:
            from PySide6.QtCore import QMarginsF
            from PySide6.QtGui import QPageLayout, QPageSize

            self.progress_bar.setValue(70)
            self.progress_bar.setFormat("正在生成PDF...")

            if not hasattr(self, "pdf_view") or not self.pdf_view:
                self.progress_bar.setVisible(False)
                return

            page = self.pdf_view.page()
            layout = QPageLayout(
                QPageSize(QPageSize.PageSizeId.A4),
                QPageLayout.Orientation.Landscape,
                QMarginsF(0, 0, 0, 0),
            )
            page.printToPdf(lambda data: self._on_pdf_generated(data), layout)

        except Exception as e:
            self.progress_bar.setVisible(False)
            QMessageBox.critical(self, "错误", f"PDF生成失败：{e}")

    def _on_pdf_generated(self, data: bytes):
        """QWebEngineView PDF 生成完成回调"""
        try:
            if not data:
                self.progress_bar.setVisible(False)
                QMessageBox.critical(self, "错误", "PDF数据为空")
                return

            with open(self.pdf_path, "wb") as f:
                f.write(data)

            self.progress_bar.setVisible(False)
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
        except Exception:
            pass

    def closeEvent(self, event):  # noqa: N802
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
    app.setStyle("Fusion")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    run_gui()
