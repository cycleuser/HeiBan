"""DOCX write context — extends WriteContext with Word-specific state."""

from typing import Optional
from heiban.core.context import WriteContext
from heiban.core.relationships import RelationshipsBuilder


# OOXML Word namespaces
W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
R_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
MC_NS = "http://schemas.openxmlformats.org/markup-compatibility/2006"
W14_NS = "http://schemas.microsoft.com/office/word/2010/wordml"
WPC_NS = "http://schemas.microsoft.com/office/word/2010/wordprocessingCanvas"
WPS_NS = "http://schemas.microsoft.com/office/word/2010/wordprocessingShape"

# Content types
DOCUMENT_CT = "application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"
STYLES_CT = "application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"
SETTINGS_CT = "application/vnd.openxmlformats-officedocument.wordprocessingml.settings+xml"
FONT_TABLE_CT = "application/vnd.openxmlformats-officedocument.wordprocessingml.fontTable+xml"
THEME_CT = "application/vnd.openxmlformats-officedocument.theme+xml"
REL_CT = "application/vnd.openxmlformats-package.relationships+xml"
CORE_CT = "application/vnd.openxmlformats-package.core-properties+xml"


class DocxWriteContext(WriteContext):
    """Word-specific compilation context.

    Tracks numbering definitions, image counter, and other DOCX-specific
    state while compiling markdown AST → DOCX parts.
    """

    def __init__(self):
        super().__init__(media_dir="word/media", media_prefix="image")

        # Register standard content types
        self.register_default("rels", REL_CT)
        self.register_part("/word/document.xml", DOCUMENT_CT)
        self.register_part("/word/styles.xml", STYLES_CT)

        # Numbering instance counter
        self._num_id_counter: int = 1
        self._abstract_num_id_counter: int = 0

        # Image counter for generating relationship IDs
        self._image_counter: int = 0

        # Setup document-level relationships
        self.set_current_rels("word/_rels/document.xml.rels")
        self._doc_rels = self.current_rels

    def next_num_id(self) -> int:
        nid = self._num_id_counter
        self._num_id_counter += 1
        return nid

    def next_abstract_num_id(self) -> int:
        nid = self._abstract_num_id_counter
        self._abstract_num_id_counter += 1
        return nid

    def next_image_rId(self) -> str:
        """Generate the next image relationship ID."""
        self._image_counter += 1
        return f"rIdImage{self._image_counter}"

    def build_package_rels(self) -> str:
        """Build the root _rels/.rels file."""
        rels = RelationshipsBuilder()
        rels.add(
            "rId1",
            "http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument",
            "word/document.xml",
        )
        return rels.to_xml()

    def get_document_rels_xml(self) -> str:
        """Return the document-level .rels XML string."""
        return self._doc_rels.to_xml() if self._doc_rels else ""
