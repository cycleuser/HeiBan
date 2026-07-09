"""DOCX generation — high-level API for converting Markdown → .docx files."""

from pathlib import Path
from typing import Optional, Union

from heiban.markdown.parser import MarkdownParser
from heiban.markdown.ast_nodes import MarkdownDocument
from heiban.docx.compiler import compile_docx, compile_docx_to_file


def generate_docx(
    markdown: Union[str, MarkdownDocument],
    output: Optional[str] = None,
) -> bytes:
    """Convert markdown text (or AST) to a .docx file.

    Args:
        markdown: Markdown string or pre-parsed MarkdownDocument.
        output: Optional output path. If provided, saves the file.

    Returns:
        The .docx file as bytes.

    Usage::

        # From markdown string
        docx_bytes = generate_docx("# Hello\\n\\nSome **bold** text")

        # Save to file
        generate_docx(markdown_str, output="output.docx")

        # From pre-parsed AST
        doc = parser.parse(markdown_str)
        docx_bytes = generate_docx(doc)
    """
    if isinstance(markdown, MarkdownDocument):
        doc = markdown
    else:
        parser = MarkdownParser()
        doc = parser.parse(markdown)

    if output:
        compile_docx_to_file(doc, output)
        return Path(output).read_bytes()

    return compile_docx(doc)
