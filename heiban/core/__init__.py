"""HeiBan Core — shared OOXML infrastructure (OPC, XML, converters, context)."""

from heiban.core.xml_utils import (
    escape_xml,
    attr,
    elem,
    elem_empty,
    cdata,
    XMLBuilder,
)
from heiban.core.opc import OPCPacker, Zippable
from heiban.core.content_types import ContentTypesBuilder
from heiban.core.relationships import RelationshipsBuilder, REL_NS
from heiban.core.converters import (
    cm_to_emu,
    mm_to_emu,
    inches_to_emu,
    pt_to_emu,
    px_to_emu,
    cm_to_twip,
    mm_to_twip,
    inches_to_twip,
    pt_to_twip,
    emu_to_cm,
    emu_to_inches,
    emu_to_pt,
    twip_to_cm,
    twip_to_pt,
    EMU_PER_CM,
    EMU_PER_INCH,
    EMU_PER_PT,
    EMU_PER_MM,
    TWIP_PER_CM,
    TWIP_PER_INCH,
    TWIP_PER_PT,
)
from heiban.core.context import WriteContext
from heiban.core.media import MediaManager

__all__ = [
    # XML
    "escape_xml",
    "attr",
    "elem",
    "elem_empty",
    "cdata",
    "XMLBuilder",
    # OPC
    "OPCPacker",
    "Zippable",
    # Content Types
    "ContentTypesBuilder",
    # Relationships
    "RelationshipsBuilder",
    "REL_NS",
    # Converters
    "cm_to_emu",
    "mm_to_emu",
    "inches_to_emu",
    "pt_to_emu",
    "px_to_emu",
    "cm_to_twip",
    "mm_to_twip",
    "inches_to_twip",
    "pt_to_twip",
    "emu_to_cm",
    "emu_to_inches",
    "emu_to_pt",
    "twip_to_cm",
    "twip_to_pt",
    "EMU_PER_CM",
    "EMU_PER_INCH",
    "EMU_PER_PT",
    "EMU_PER_MM",
    "TWIP_PER_CM",
    "TWIP_PER_INCH",
    "TWIP_PER_PT",
    # Context
    "WriteContext",
    # Media
    "MediaManager",
]
