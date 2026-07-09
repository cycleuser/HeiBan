"""PPTX write context — extends WriteContext with PowerPoint-specific state."""

from typing import Dict, List, Optional, Tuple
from heiban.core.context import WriteContext
from heiban.core.relationships import RelationshipsBuilder


# OOXML Presentation namespaces
P_NS = "http://schemas.openxmlformats.org/presentationml/2006/main"
A_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"
R_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"

# Content types
PRESENTATION_CT = "application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml"
SLIDE_CT = "application/vnd.openxmlformats-officedocument.presentationml.slide+xml"
SLIDE_MASTER_CT = "application/vnd.openxmlformats-officedocument.presentationml.slideMaster+xml"
SLIDE_LAYOUT_CT = "application/vnd.openxmlformats-officedocument.presentationml.slideLayout+xml"
THEME_CT = "application/vnd.openxmlformats-officedocument.theme+xml"
NOTES_SLIDE_CT = "application/vnd.openxmlformats-officedocument.presentationml.notesSlide+xml"
NOTES_MASTER_CT = "application/vnd.openxmlformats-officedocument.presentationml.notesMaster+xml"
IMAGE_CT = "application/vnd.openxmlformats-officedocument.image"


class PptxWriteContext(WriteContext):
    """PowerPoint-specific compilation context.

    Tracks slides, slide layouts, themes, and media references.
    """

    # Standard slide dimensions (16:9 in EMU)
    SLIDE_WIDTH = 12192000   # ~13.33 inches
    SLIDE_HEIGHT = 6858000   # ~7.5 inches

    def __init__(self):
        super().__init__(media_dir="ppt/media", media_prefix="image")

        # Register content types
        self.register_default("rels", "application/vnd.openxmlformats-package.relationships+xml")
        self.register_part("/ppt/presentation.xml", PRESENTATION_CT)
        self.register_part("/ppt/slideMasters/slideMaster1.xml", SLIDE_MASTER_CT)
        self.register_part("/ppt/slideLayouts/slideLayout1.xml", SLIDE_LAYOUT_CT)
        self.register_part("/ppt/theme/theme1.xml", THEME_CT)

        # Slide tracking
        self._slide_count: int = 0
        self._slide_rels: Dict[int, RelationshipsBuilder] = {}

        # Setup presentation-level relationships
        self.set_current_rels("ppt/_rels/presentation.xml.rels")
        self._pres_rels = self.current_rels

        # Add standard relationships
        self._pres_rels.add_slide_master("rIdSm1", "slideMasters/slideMaster1.xml")
        # We don't add slide refs yet — they're added as slides are created

        # Setup slide master relationships
        sm_rels = RelationshipsBuilder()
        sm_rels.add_slide_layout("rIdSl1", "../slideLayouts/slideLayout1.xml")
        sm_rels.add_theme("rIdTh1", "../theme/theme1.xml")
        self._rels["ppt/slideMasters/_rels/slideMaster1.xml.rels"] = sm_rels

        # Setup slide layout relationships
        sl_rels = RelationshipsBuilder()
        sl_rels.add_slide_master("rIdSm1", "../slideMasters/slideMaster1.xml")
        self._rels["ppt/slideLayouts/_rels/slideLayout1.xml.rels"] = sl_rels

    def next_slide(self, title: str = "") -> int:
        """Start a new slide. Returns the slide number (0-based)."""
        self._slide_count += 1
        slide_num = self._slide_count
        slide_path = f"ppt/slides/slide{slide_num}.xml"
        rels_path = f"ppt/slides/_rels/slide{slide_num}.xml.rels"

        # Register slide
        self.register_part(f"/{slide_path}", SLIDE_CT)

        # Add slide relationship to presentation
        rId = f"rIdSlide{slide_num}"
        self._pres_rels.add_slide(rId, f"slides/slide{slide_num}.xml")

        # Create slide-level relationships
        slide_rels = RelationshipsBuilder()
        slide_rels.add_slide_layout("rIdSl1", f"../slideLayouts/slideLayout1.xml")
        self._rels[rels_path] = slide_rels

        self.set_current_rels(rels_path)
        return slide_num

    def get_slide_count(self) -> int:
        return self._slide_count

    def build_package_rels(self) -> str:
        """Build root _rels/.rels for PPTX."""
        rels = RelationshipsBuilder()
        rels.add(
            "rId1",
            "http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument",
            "ppt/presentation.xml",
        )
        return rels.to_xml()
