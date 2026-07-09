"""XLSX generation — high-level API for converting Markdown → .xlsx files."""

from pathlib import Path
from typing import Optional, Union

from heiban.markdown.parser import MarkdownParser
from heiban.markdown.ast_nodes import MarkdownDocument
from heiban.xlsx.compiler import compile_xlsx, compile_xlsx_to_file


def generate_xlsx(
    markdown: Union[str, MarkdownDocument],
    output: Optional[str] = None,
) -> bytes:
    """Convert markdown text (or AST) to an .xlsx file.

    Each table in the markdown becomes a worksheet. Non-table content
    is placed in a "Content" worksheet.

    Args:
        markdown: Markdown string or pre-parsed MarkdownDocument.
        output: Optional output path. If provided, saves the file.

    Returns:
        The .xlsx file as bytes.

    Usage::

        xlsx_bytes = generate_xlsx("# Report\\n\\n| A | B |\\n|---|---|\\n| 1 | 2 |")
        generate_xlsx(markdown_str, output="data.xlsx")
    """
    if isinstance(markdown, MarkdownDocument):
        doc = markdown
    else:
        parser = MarkdownParser()
        doc = parser.parse(markdown)

    if output:
        compile_xlsx_to_file(doc, output)
        return Path(output).read_bytes()

    return compile_xlsx(doc)
