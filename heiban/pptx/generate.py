"""PPTX generation — high-level API for converting Markdown → .pptx files."""

from pathlib import Path
from typing import Optional, Union

from heiban.markdown.parser import MarkdownParser
from heiban.markdown.ast_nodes import MarkdownDocument
from heiban.pptx.compiler import compile_pptx, compile_pptx_to_file


def generate_pptx(
    markdown: Union[str, MarkdownDocument],
    output: Optional[str] = None,
) -> bytes:
    """Convert markdown text (or AST) to a .pptx file.

    The markdown is split into slides at `---` (horizontal rule) boundaries.

    Args:
        markdown: Markdown string or pre-parsed MarkdownDocument.
        output: Optional output path. If provided, saves the file.

    Returns:
        The .pptx file as bytes.

    Usage::

        pptx_bytes = generate_pptx("# Title\\n\\n---\\n\\n## Slide 2\\n\\nContent")
        generate_pptx(markdown_str, output="slides.pptx")
    """
    if isinstance(markdown, MarkdownDocument):
        doc = markdown
    else:
        parser = MarkdownParser()
        doc = parser.parse(markdown)

    if output:
        compile_pptx_to_file(doc, output)
        return Path(output).read_bytes()

    return compile_pptx(doc)
