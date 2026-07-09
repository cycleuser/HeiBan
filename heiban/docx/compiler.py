"""DOCX compiler — orchestrates MarkdownDocument → DOCX compilation.

Implements the compile → pack pipeline inspired by @office-open/docx.
"""

from typing import Dict, Optional

from heiban.core.opc import OPCPacker
from heiban.core.content_types import ContentTypesBuilder
from heiban.core.relationships import RelationshipsBuilder
from heiban.markdown.ast_nodes import MarkdownDocument
from heiban.docx.context import DocxWriteContext
from heiban.docx.parts.styles import build_styles_xml
from heiban.docx.parts.document import build_document_xml


def compile_docx(doc: MarkdownDocument) -> bytes:
    """Compile a MarkdownDocument to a complete .docx file (bytes).

    Args:
        doc: The parsed markdown document AST.

    Returns:
        The .docx file as bytes (ready to write to disk).
    """
    ctx = DocxWriteContext()

    # Build each part
    document_xml = build_document_xml(doc, ctx)
    styles_xml = build_styles_xml()

    # Collect relationships
    doc_rels_xml = ctx.get_document_rels_xml()
    package_rels_xml = ctx.build_package_rels()

    # Collect content types
    content_types_xml = ctx.collect_content_types()

    # Collect media
    media_files = ctx.collect_media()

    # Assemble the ZIP
    packer = OPCPacker()
    packer.add_xml("[Content_Types].xml", content_types_xml)
    packer.add_xml("_rels/.rels", package_rels_xml)
    packer.add_xml("word/document.xml", document_xml)
    packer.add_xml("word/styles.xml", styles_xml)
    packer.add_xml("word/_rels/document.xml.rels", doc_rels_xml)

    for path, data in media_files.items():
        packer.add(path, data)

    return packer.pack()


def compile_docx_to_file(doc: MarkdownDocument, filepath: str):
    """Compile a MarkdownDocument and save as a .docx file.

    Args:
        doc: The parsed markdown document AST.
        filepath: Output file path (e.g. 'output.docx').
    """
    data = compile_docx(doc)
    with open(filepath, "wb") as f:
        f.write(data)
