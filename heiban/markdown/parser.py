"""Markdown parser — converts markdown text into an AST of MarkdownDocument.

Uses markdown-it-py for tokenization then walks the token stream to produce
our format-agnostic AST nodes.
"""

import re
from typing import List, Optional

from markdown_it import MarkdownIt
from markdown_it.token import Token
from markdown_it.rules_block import StateBlock

from heiban.markdown.ast_nodes import (
    Block,
    BlockQuote,
    CodeBlock,
    Heading,
    HorizontalRule,
    ImageBlock,
    Inline,
    InlineImage,
    ListItem,
    MarkdownDocument,
    MathBlock,
    MdList,
    MermaidBlock,
    Paragraph,
    Table,
    TableCell,
    TableRow,
    TextRun,
    ListKind,
)

# Regex to protect math before markdown-it processing
_MATH_DISPLAY_RE = re.compile(r"\$\$([\s\S]*?)\$\$")
_MATH_INLINE_RE = re.compile(r"\$(.*?)\$")
_CODE_FENCE_RE = re.compile(r"```[\s\S]*?```")


class MarkdownParser:
    """Parse markdown text into a MarkdownDocument AST.

    Usage::

        parser = MarkdownParser()
        doc = parser.parse(markdown_text)
        # doc.blocks → list of Heading, Paragraph, Table, CodeBlock, etc.
    """

    def __init__(self, options: Optional[dict] = None):
        self._options = options or {}
        self._md = MarkdownIt("commonmark")
        # Enable GFM-like features
        self._md.enable(["table", "strikethrough"])

    def parse(self, text: str) -> MarkdownDocument:
        """Parse markdown text into a document AST."""
        if not text.strip():
            return MarkdownDocument()

        # Extract front matter
        front_matter = {}
        body = text
        if text.startswith("---"):
            end = text.find("---", 3)
            if end != -1:
                front_text = text[3:end].strip()
                body = text[end + 3 :].strip()
                for line in front_text.split("\n"):
                    if ":" in line:
                        key, _, val = line.partition(":")
                        front_matter[key.strip()] = val.strip()

        title = front_matter.get("title", "")

        # Protect math blocks
        math_blocks: List[str] = []
        body = _MATH_DISPLAY_RE.sub(lambda m: self._stash(math_blocks, m.group(1)), body)

        # Tokenize with markdown-it
        tokens = self._md.parse(body, {})
        blocks = self._tokens_to_blocks(tokens, math_blocks)

        return MarkdownDocument(title=title, blocks=blocks, front_matter=front_matter)

    def _stash(self, stash: List[str], text: str) -> str:
        stash.append(text)
        return f"\x00MATH{len(stash) - 1}\x00"

    def _unstash_math(self, stash: List[str], text: str) -> str:
        def _replacer(m):
            idx = m.group(1)
            # Could be inline math idx or part of a display math marker
            return ""
        return re.sub(r"\x00MATH(\d+)\x00", lambda m: f"${stash[int(m.group(1))]}$", text)

    def _tokens_to_blocks(self, tokens: List[Token], math_stash: List[str]) -> List[Block]:
        """Walk token stream and produce Block nodes."""
        blocks: List[Block] = []
        i = 0
        while i < len(tokens):
            token = tokens[i]
            if token.type == "heading_open":
                block, i = self._parse_heading(tokens, i)
            elif token.type == "paragraph_open":
                block, i = self._parse_paragraph(tokens, i, math_stash)
            elif token.type == "fence":
                block = self._parse_fence(token)
                i += 1
            elif token.type == "table_open":
                block, i = self._parse_table(tokens, i, math_stash)
            elif token.type in ("bullet_list_open", "ordered_list_open"):
                block, i = self._parse_list(tokens, i, math_stash)
            elif token.type == "blockquote_open":
                block, i = self._parse_blockquote(tokens, i, math_stash)
            elif token.type == "hr":
                block = HorizontalRule()
                i += 1
            elif token.type == "html_block":
                block = self._parse_html_block(token.content)
                i += 1
            else:
                i += 1
                continue

            if block is not None:
                blocks.append(block)

        return blocks

    # --- Heading ---

    def _parse_heading(self, tokens: List[Token], start: int):
        tag = tokens[start].tag  # h1-h6
        level = int(tag[1])
        inline_tokens = []
        i = start + 1
        while i < len(tokens) and tokens[i].type != "heading_close":
            inline_tokens.append(tokens[i])
            i += 1
        content = self._tokens_to_inline(inline_tokens)
        return Heading(level=level, content=content), i + 1

    # --- Paragraph ---

    def _parse_paragraph(self, tokens: List[Token], start: int, math_stash: List[str]):
        inline_tokens = []
        i = start + 1
        while i < len(tokens) and tokens[i].type != "paragraph_close":
            inline_tokens.append(tokens[i])
            i += 1
        content = self._tokens_to_inline(inline_tokens, math_stash)
        # Check if this paragraph is an image-only paragraph (block image)
        if len(content.images) == 1 and len(content.runs) == 0:
            img = content.images[0]
            return ImageBlock(src=img.src, alt=img.alt, width=img.width, height=img.height), i + 1
        # Check if this is a math display block
        if len(content.math) == 1 and len(content.runs) == 0:
            return MathBlock(latex=content.math[0]), i + 1
        return Paragraph(content=content), i + 1

    # --- Fence (code block) ---

    def _parse_fence(self, token: Token) -> Block:
        info = token.info.strip() if token.info else ""
        lang = info.split()[0] if info else ""
        code = token.content

        # Check for Mermaid
        if lang.lower() == "mermaid":
            return MermaidBlock(diagram=code)

        return CodeBlock(language=lang, code=code)

    # --- Table ---

    def _parse_table(self, tokens: List[Token], start: int, math_stash: List[str]):
        rows: List[TableRow] = []
        alignments: List[Optional[str]] = []
        i = start

        while i < len(tokens) and tokens[i].type != "table_close":
            token = tokens[i]
            if token.type == "thead_open":
                i += 1
                while i < len(tokens) and tokens[i].type != "thead_close":
                    if tokens[i].type == "tr_open":
                        row, i = self._parse_table_row(tokens, i, math_stash, header=True)
                        rows.append(row)
                    else:
                        i += 1
                i += 1  # skip thead_close
            elif token.type == "tbody_open":
                i += 1
                while i < len(tokens) and tokens[i].type != "tbody_close":
                    if tokens[i].type == "tr_open":
                        row, i = self._parse_table_row(tokens, i, math_stash)
                        rows.append(row)
                    else:
                        i += 1
                i += 1
            else:
                i += 1

        # Detect column alignments from the table's style info
        # markdown-it stores this in token.attrGet("style") on td/th
        return Table(rows=rows, alignment=alignments), i + 1

    def _parse_table_row(
        self, tokens: List[Token], start: int, math_stash: List[str], header: bool = False
    ):
        cells: List[TableCell] = []
        i = start + 1  # skip tr_open
        while i < len(tokens) and tokens[i].type != "tr_close":
            token = tokens[i]
            if token.type in ("td_open", "th_open"):
                inline_tokens = []
                i += 1
                while i < len(tokens) and tokens[i].type not in ("td_close", "th_close"):
                    inline_tokens.append(tokens[i])
                    i += 1
                content = self._tokens_to_inline(inline_tokens, math_stash)
                is_header = token.type == "th_open" or header

                # Parse style for alignment
                style = token.attrGet("style") or ""
                align = None
                if "text-align:center" in style:
                    align = "center"
                elif "text-align:right" in style:
                    align = "right"
                elif "text-align:left" in style:
                    align = "left"

                cells.append(TableCell(content=content, header=is_header, alignment=align))
            i += 1
        return TableRow(cells=cells, header=header), i + 1

    # --- List ---

    def _parse_list(self, tokens: List[Token], start: int, math_stash: List[str]):
        kind = ListKind.UNORDERED if tokens[start].type == "bullet_list_open" else ListKind.ORDERED
        items: List[ListItem] = []
        i = start + 1  # skip list_open

        while i < len(tokens) and tokens[i].type not in ("bullet_list_close", "ordered_list_close"):
            token = tokens[i]
            if token.type == "list_item_open":
                item, i = self._parse_list_item(tokens, i, math_stash)
                items.append(item)
            else:
                i += 1
        return MdList(kind=kind, items=items), i + 1

    def _parse_list_item(self, tokens: List[Token], start: int, math_stash: List[str]):
        inline_tokens: List[Token] = []
        nested_blocks: List[Block] = []
        i = start + 1  # skip list_item_open

        while i < len(tokens) and tokens[i].type != "list_item_close":
            token = tokens[i]
            if token.type == "paragraph_open":
                # Collect inline content from paragraph
                j = i + 1
                while j < len(tokens) and tokens[j].type != "paragraph_close":
                    inline_tokens.append(tokens[j])
                    j += 1
                i = j + 1
            elif token.type in ("bullet_list_open", "ordered_list_open"):
                # Nested list
                nested_list, i = self._parse_list(tokens, i, math_stash)
                nested_blocks.append(nested_list)
            elif token.type == "blockquote_open":
                bq, i = self._parse_blockquote(tokens, i, math_stash)
                nested_blocks.append(bq)
            elif token.type == "fence":
                nested_blocks.append(self._parse_fence(token))
                i += 1
            else:
                i += 1

        content = self._tokens_to_inline(inline_tokens, math_stash)
        # Strip list markers from start of text
        for run in content.runs:
            run.text = re.sub(r"^\[[ x]\]\s*", "", run.text)  # task list
        return ListItem(content=content, nested=nested_blocks), i + 1

    # --- Blockquote ---

    def _parse_blockquote(self, tokens: List[Token], start: int, math_stash: List[str]):
        inner_tokens: List[Token] = []
        i = start + 1  # skip blockquote_open
        depth = 1
        while i < len(tokens) and depth > 0:
            token = tokens[i]
            if token.type == "blockquote_open":
                depth += 1
            elif token.type == "blockquote_close":
                depth -= 1
                if depth == 0:
                    break
            inner_tokens.append(token)
            i += 1
        blocks = self._tokens_to_blocks(inner_tokens, math_stash)
        return BlockQuote(blocks=blocks), i + 1

    # --- HTML blocks (mermaid, etc.) ---

    def _parse_html_block(self, content: str) -> Optional[Block]:
        content = content.strip()
        if content.startswith('<pre class="mermaid">') or content.startswith('<div class="mermaid">'):
            # Extract mermaid content
            text = re.sub(r"<[^>]+>", "", content).strip()
            return MermaidBlock(diagram=text)
        return None

    # --- Inline parsing ---

    def _tokens_to_inline(
        self, tokens: List[Token], math_stash: Optional[List[str]] = None
    ) -> Inline:
        """Convert inline tokens to Inline (TextRun + InlineImage + inline math)."""
        inline = Inline()
        if not tokens:
            return inline

        # We need to restore math placeholders and then walk the token tree
        # For inline parsing, we can use the tokens directly

        i = 0
        while i < len(tokens):
            token = tokens[i]

            if token.type == "inline":
                # Nested inline — process children
                if token.children:
                    child_inline = self._tokens_to_inline(token.children, math_stash)
                    inline.runs.extend(child_inline.runs)
                    inline.images.extend(child_inline.images)
                    inline.math.extend(child_inline.math)
                i += 1

            elif token.type == "text":
                text = token.content
                if math_stash:
                    text = self._restore_math_in_text(text, math_stash, inline)
                if text:
                    inline.runs.append(TextRun(text=text))
                i += 1

            elif token.type == "code_inline":
                inline.runs.append(TextRun(text=token.content, code=True))
                i += 1

            elif token.type == "strong_open":
                bold_tokens = []
                i += 1
                while i < len(tokens) and tokens[i].type != "strong_close":
                    bold_tokens.append(tokens[i])
                    i += 1
                i += 1
                bold_inline = self._tokens_to_inline(bold_tokens, math_stash)
                for run in bold_inline.runs:
                    run.bold = True
                inline.runs.extend(bold_inline.runs)
                inline.images.extend(bold_inline.images)
                inline.math.extend(bold_inline.math)

            elif token.type == "em_open":
                em_tokens = []
                i += 1
                while i < len(tokens) and tokens[i].type != "em_close":
                    em_tokens.append(tokens[i])
                    i += 1
                i += 1
                em_inline = self._tokens_to_inline(em_tokens, math_stash)
                for run in em_inline.runs:
                    run.italic = True
                inline.runs.extend(em_inline.runs)
                inline.images.extend(em_inline.images)
                inline.math.extend(em_inline.math)

            elif token.type == "s_open":
                s_tokens = []
                i += 1
                while i < len(tokens) and tokens[i].type != "s_close":
                    s_tokens.append(tokens[i])
                    i += 1
                i += 1
                s_inline = self._tokens_to_inline(s_tokens, math_stash)
                for run in s_inline.runs:
                    run.strikethrough = True
                inline.runs.extend(s_inline.runs)

            elif token.type == "link_open":
                href = token.attrGet("href") or ""
                link_tokens = []
                i += 1
                while i < len(tokens) and tokens[i].type != "link_close":
                    link_tokens.append(tokens[i])
                    i += 1
                i += 1
                link_inline = self._tokens_to_inline(link_tokens, math_stash)
                for run in link_inline.runs:
                    run.link = href
                inline.runs.extend(link_inline.runs)

            elif token.type == "image":
                src = token.attrGet("src") or ""
                alt = token.content or ""
                title = token.attrGet("title") or ""
                inline.images.append(InlineImage(src=src, alt=alt or title))
                i += 1

            elif token.type == "hardbreak":
                inline.runs.append(TextRun(text="\n"))
                i += 1

            elif token.type == "softbreak":
                inline.runs.append(TextRun(text=" "))
                i += 1

            else:
                i += 1

        return inline

    def _restore_math_in_text(self, text: str, math_stash: List[str], inline: Inline) -> str:
        """Find math placeholders and restore them, adding to inline.math."""
        result = []
        last_end = 0
        for m in re.finditer(r"\x00MATH(\d+)\x00", text):
            # Add text before the math
            result.append(text[last_end : m.start()])
            idx = int(m.group(1))
            if idx < len(math_stash):
                inline.math.append(math_stash[idx])
                result.append(f"${math_stash[idx]}$")
            last_end = m.end()
        result.append(text[last_end:])
        return "".join(result)


# Convenience function
def parse_markdown(text: str) -> MarkdownDocument:
    """Parse markdown text into an AST."""
    return MarkdownParser().parse(text)
