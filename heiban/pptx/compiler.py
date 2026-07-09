"""PPTX compiler — orchestrates MarkdownDocument → PPTX compilation.

Splits the markdown document into slides (by `---` horizontal rules or
headings), then compiles each slide to XML and assembles the ZIP package.
"""

from typing import Dict, List, Optional

from heiban.core.opc import OPCPacker
from heiban.markdown.ast_nodes import (
    Block,
    Heading,
    HorizontalRule,
    MarkdownDocument,
)
from heiban.pptx.context import PptxWriteContext
from heiban.pptx.parts.theme import (
    build_theme_xml,
    build_slide_master_xml,
    build_slide_layout_xml,
    build_presentation_xml,
)
from heiban.pptx.parts.slide import build_slide_xml


def compile_pptx(doc: MarkdownDocument) -> bytes:
    """Compile a MarkdownDocument to a complete .pptx file (bytes).

    The document is split into slides at HorizontalRule (---) boundaries.
    Each section becomes a slide.

    Args:
        doc: The parsed markdown document AST.

    Returns:
        The .pptx file as bytes.
    """
    ctx = PptxWriteContext()

    # Split blocks into slides
    slides = _split_into_slides(doc.blocks)

    # Build slide XMLs
    slide_xmls: Dict[str, str] = {}
    for i, slide_blocks in enumerate(slides):
        slide_num = i + 1
        slug = f"ppt/slides/slide{slide_num}.xml"
        slide_xmls[slug] = build_slide_xml(slide_blocks, slide_num, ctx)

    # Build static parts
    theme_xml = build_theme_xml()
    master_xml = build_slide_master_xml()
    layout_xml = build_slide_layout_xml()
    pres_xml = build_presentation_xml(ctx.get_slide_count())

    # Collect relationships
    all_rels = ctx.get_rels()
    package_rels_xml = ctx.build_package_rels()

    # Content types
    content_types_xml = ctx.collect_content_types()

    # Media
    media_files = ctx.collect_media()

    # Assemble ZIP
    packer = OPCPacker()
    packer.add_xml("[Content_Types].xml", content_types_xml)
    packer.add_xml("_rels/.rels", package_rels_xml)
    packer.add_xml("ppt/presentation.xml", pres_xml)
    packer.add_xml("ppt/presProps.xml", _empty_pres_props())
    packer.add_xml("ppt/viewProps.xml", _empty_view_props())
    packer.add_xml("ppt/tableStyles.xml", _empty_table_styles())
    packer.add_xml("ppt/slideMasters/slideMaster1.xml", master_xml)
    packer.add_xml("ppt/slideLayouts/slideLayout1.xml", layout_xml)
    packer.add_xml("ppt/theme/theme1.xml", theme_xml)

    # Add slide XMLs
    for path, xml_str in slide_xmls.items():
        packer.add_xml(path, xml_str)

    # Add relationships
    for rels_path, rels_xml in all_rels.items():
        packer.add_xml(rels_path, rels_xml)

    # Add media
    for path, data in media_files.items():
        packer.add(path, data)

    return packer.pack()


def compile_pptx_to_file(doc: MarkdownDocument, filepath: str):
    """Compile and save as .pptx."""
    data = compile_pptx(doc)
    with open(filepath, "wb") as f:
        f.write(data)


def _split_into_slides(blocks: List[Block]) -> List[List[Block]]:
    """Split blocks into slides at HorizontalRule boundaries.

    If no HorizontalRules are found, puts all blocks on one slide.
    Consecutive HRs are merged.
    """
    if not blocks:
        return [[]]

    slides: List[List[Block]] = []
    current: List[Block] = []

    for block in blocks:
        if isinstance(block, HorizontalRule):
            if current:
                slides.append(current)
                current = []
        else:
            current.append(block)

    if current:
        slides.append(current)

    if not slides:
        slides = [[]]

    return slides


def _empty_pres_props() -> str:
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:presentationPr xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"/>"""


def _empty_view_props() -> str:
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:viewPr xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"
          xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">
  <p:normalViewPr>
    <p:restoredLeft sz="0"/>
    <p:restoredTop sz="0"/>
  </p:normalViewPr>
  <p:slideViewPr/>
</p:viewPr>"""


def _empty_table_styles() -> str:
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<a:tblStyleLst xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"/>"""
