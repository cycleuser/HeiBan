"""
HeiBan - Markdown 转 HTML 幻灯片生成器
基于 PySide6 GUI，支持导出 HTML / PDF / PPTX
"""

__version__ = "0.3.0"
__author__ = "HeiBan Contributors"

from .converter import MarkdownToSlideConverter
from .gui import MainWindow

__all__ = [
    "MarkdownToSlideConverter",
    "MainWindow",
    "__version__",
]
