"""XLSX compiler — orchestrates MarkdownDocument → XLSX compilation.

Each markdown table becomes a worksheet. Non-table content is collected
into a "Content" worksheet.
"""

from typing import Dict, List

from heiban.core.opc import OPCPacker
from heiban.markdown.ast_nodes import (
    Block,
    CodeBlock,
    Heading,
    MarkdownDocument,
    Paragraph,
    Table,
)
from heiban.xlsx.context import XlsxWriteContext
from heiban.xlsx.parts.worksheet import build_worksheet_xml, build_workbook_xml


def compile_xlsx(doc: MarkdownDocument) -> bytes:
    """Compile a MarkdownDocument to a complete .xlsx file.

    Tables become individual worksheets. Non-table content (headings,
    paragraphs) is placed in a "Content" sheet.

    Args:
        doc: The parsed markdown document AST.

    Returns:
        The .xlsx file as bytes.
    """
    ctx = XlsxWriteContext()

    # Separate tables from other content
    tables: List[Table] = []
    other: List[Block] = []
    for block in doc.blocks:
        if isinstance(block, Table):
            tables.append(block)
        else:
            other.append(block)

    # Determine sheet layout
    sheet_specs: List[tuple] = []  # (name, blocks)
    for i, tbl in enumerate(tables):
        # Try to find a heading right before the table as the sheet name
        name = f"Table{i + 1}"
        sheet_specs.append((name, [tbl]))

    if other and not tables:
        sheet_specs.append(("Content", other))
    elif other:
        sheet_specs.append(("Content", other))

    if not sheet_specs:
        sheet_specs = [("Sheet1", [])]

    # Build worksheets
    worksheet_xmls: Dict[str, str] = {}
    sheet_names: List[str] = []
    for i, (name, blocks) in enumerate(sheet_specs):
        sheet_num = i + 1
        sheet_names.append(name)
        ctx.add_worksheet(sheet_num, name)
        slug = f"xl/worksheets/sheet{sheet_num}.xml"
        worksheet_xmls[slug] = build_worksheet_xml(name, blocks, ctx)

    # Build workbook
    wb_xml = build_workbook_xml(sheet_names)

    # Collect parts
    shared_strings_xml = ctx.build_shared_strings_xml()
    styles_xml = ctx.build_styles_xml()
    theme_xml = ctx.build_theme_xml()
    package_rels_xml = ctx.build_package_rels()
    all_rels = ctx.get_rels()
    content_types_xml = ctx.collect_content_types()
    media_files = ctx.collect_media()

    # Assemble ZIP
    packer = OPCPacker()
    packer.add_xml("[Content_Types].xml", content_types_xml)
    packer.add_xml("_rels/.rels", package_rels_xml)
    packer.add_xml("xl/workbook.xml", wb_xml)
    packer.add_xml("xl/styles.xml", styles_xml)
    packer.add_xml("xl/sharedStrings.xml", shared_strings_xml)
    packer.add_xml("xl/theme/theme1.xml", theme_xml)

    for path, xml_str in worksheet_xmls.items():
        packer.add_xml(path, xml_str)

    for rels_path, rels_xml in all_rels.items():
        packer.add_xml(rels_path, rels_xml)

    for path, data in media_files.items():
        packer.add(path, data)

    return packer.pack()


def compile_xlsx_to_file(doc: MarkdownDocument, filepath: str):
    """Compile and save as .xlsx."""
    data = compile_xlsx(doc)
    with open(filepath, "wb") as f:
        f.write(data)
