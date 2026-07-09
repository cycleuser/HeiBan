"""
HeiBan - Markdown to Office Document Generator
Supports Markdown → PPTX / DOCX / XLSX / HTML with pure XML OOXML generation.

Inspired by @office-open architecture.
"""

__version__ = "0.4.0"
__author__ = "HeiBan Contributors"

# Legacy exports (backward compatible)
from .converter import MarkdownToSlideConverter

try:
    from .gui import MainWindow
except ImportError:
    MainWindow = None  # type: ignore

# New unified exports
from heiban.markdown import MarkdownParser, MarkdownDocument, parse_markdown
from heiban.docx import generate_docx
from heiban.pptx import generate_pptx
from heiban.xlsx import generate_xlsx

__all__ = [
    # Legacy
    "MarkdownToSlideConverter",
    "MainWindow",
    # New
    "MarkdownParser",
    "MarkdownDocument",
    "parse_markdown",
    "generate_docx",
    "generate_pptx",
    "generate_xlsx",
    "__version__",
]
