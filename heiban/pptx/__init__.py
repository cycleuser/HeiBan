"""PPTX — Markdown to PowerPoint conversion (pure XML OOXML generation)."""

from heiban.pptx.generate import generate_pptx
from heiban.pptx.compiler import compile_pptx, compile_pptx_to_file
from heiban.pptx.context import PptxWriteContext

__all__ = [
    "generate_pptx",
    "compile_pptx",
    "compile_pptx_to_file",
    "PptxWriteContext",
]
