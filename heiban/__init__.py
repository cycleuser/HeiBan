"""
HeiBan - Mermaid转HTML幻灯片生成器
基于PySide6的GUI工具
"""

__version__ = "0.1.40"
__author__ = "HeiBan Contributors"

from .converter import MarkdownToSlideConverter
from .gui import MainWindow

__all__ = ["MarkdownToSlideConverter", "MainWindow", "__version__"]
