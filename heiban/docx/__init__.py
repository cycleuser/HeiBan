"""DOCX — Markdown to Word document conversion (pure XML OOXML generation)."""

from heiban.docx.generate import generate_docx
from heiban.docx.compiler import compile_docx, compile_docx_to_file
from heiban.docx.context import DocxWriteContext

__all__ = [
    "generate_docx",
    "compile_docx",
    "compile_docx_to_file",
    "DocxWriteContext",
]
