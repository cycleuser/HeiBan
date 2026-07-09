"""Markdown AST — format-agnostic intermediate representation.

These dataclasses represent structured markdown content that can be rendered
to DOCX, PPTX, XLSX, or HTML.  Inspired by office-open's pure-JSON API:
everything is plain data — no constructors needed beyond dataclass defaults.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Union


class ListKind(str, Enum):
    ORDERED = "ordered"
    UNORDERED = "unordered"


@dataclass
class TextRun:
    """A styled run of inline text."""

    text: str = ""
    bold: bool = False
    italic: bool = False
    underline: bool = False
    strikethrough: bool = False
    code: bool = False
    link: Optional[str] = None  # URL for hyperlink
    color: Optional[str] = None  # hex color e.g. "#ff0000"
    size: Optional[int] = None  # font size in half-points (e.g. 24 = 12pt)
    highlight: Optional[str] = None  # highlight color


@dataclass
class Inline:
    """A paragraph's inline content — sequence of text runs, code spans, images, math."""

    runs: List[TextRun] = field(default_factory=list)
    images: List["InlineImage"] = field(default_factory=list)
    math: List[str] = field(default_factory=list)  # inline LaTeX strings


@dataclass
class InlineImage:
    """An inline image within a paragraph."""

    src: str = ""  # file path, URL, or base64 data URI
    alt: str = ""
    width: Optional[int] = None  # EMU
    height: Optional[int] = None  # EMU


# --- Block-level nodes ---

@dataclass
class Heading:
    """A heading (level 1-6)."""

    level: int = 1
    content: Inline = field(default_factory=Inline)


@dataclass
class Paragraph:
    """A plain paragraph."""

    content: Inline = field(default_factory=Inline)
    alignment: Optional[str] = None  # left, center, right, justify


@dataclass
class CodeBlock:
    """A fenced code block."""

    language: str = ""
    code: str = ""
    highlights: List[int] = field(default_factory=list)  # line numbers to highlight


@dataclass
class TableCell:
    """A single table cell."""

    content: Inline = field(default_factory=Inline)
    colspan: int = 1
    rowspan: int = 1
    header: bool = False
    alignment: Optional[str] = None


@dataclass
class TableRow:
    """A table row."""

    cells: List[TableCell] = field(default_factory=list)
    header: bool = False


@dataclass
class Table:
    """A markdown table."""

    rows: List[TableRow] = field(default_factory=list)
    alignment: List[Optional[str]] = field(default_factory=list)  # per-column align
    caption: str = ""


@dataclass
class ListItem:
    """A single list item (may contain nested blocks)."""

    content: Inline = field(default_factory=Inline)
    nested: List["Block"] = field(default_factory=list)


@dataclass
class MdList:
    """A bullet or numbered list."""

    kind: ListKind = ListKind.UNORDERED
    items: List[ListItem] = field(default_factory=list)
    start: int = 1  # for ordered lists
    tight: bool = False


@dataclass
class BlockQuote:
    """A block quote."""

    blocks: List["Block"] = field(default_factory=list)


@dataclass
class ImageBlock:
    """A standalone (block-level) image."""

    src: str = ""
    alt: str = ""
    width: Optional[int] = None
    height: Optional[int] = None
    title: str = ""


@dataclass
class MathBlock:
    """Display math ($$...$$)."""

    latex: str = ""


@dataclass
class MermaidBlock:
    """A Mermaid diagram."""

    diagram: str = ""
    theme: str = "default"


@dataclass
class HorizontalRule:
    """A horizontal rule / thematic break."""

    pass


# --- Union type for block-level nodes ---

Block = Union[
    Heading,
    Paragraph,
    CodeBlock,
    Table,
    MdList,
    BlockQuote,
    ImageBlock,
    MathBlock,
    MermaidBlock,
    HorizontalRule,
]


@dataclass
class MarkdownDocument:
    """Top-level markdown document — the full AST."""

    title: str = ""
    blocks: List[Block] = field(default_factory=list)
    front_matter: dict = field(default_factory=dict)
