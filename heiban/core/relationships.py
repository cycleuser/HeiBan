"""Relationships (.rels) builder.

Every OPC part can have a .rels file that maps relationship ids (rId1, rId2, …)
to target parts.  This module builds those XML documents.
"""

from typing import Dict, List, Optional, Tuple
from heiban.core.xml_utils import escape_xml

REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"


class RelationshipsBuilder:
    """Builds a .rels XML document.

    Each relationship has an id (rId), type (URI), target (relative path), and
    optional TargetMode ("External").
    """

    def __init__(self):
        self._rels: List[Tuple[str, str, str, Optional[str]]] = []
        # (id, type_uri, target, target_mode_or_none)

    def add(self, rId: str, type_uri: str, target: str, target_mode: Optional[str] = None):
        """Add a relationship."""
        self._rels.append((rId, type_uri, target, target_mode))

    def add_image(self, rId: str, target: str) -> str:
        """Add an image relationship (common shorthand)."""
        self.add(
            rId,
            "http://schemas.openxmlformats.org/officeDocument/2006/relationships/image",
            target,
        )
        return rId

    def add_hyperlink(self, rId: str, url: str) -> str:
        """Add an external hyperlink relationship."""
        self.add(
            rId,
            "http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink",
            url,
            target_mode="External",
        )
        return rId

    def add_chart(self, rId: str, target: str) -> str:
        self.add(
            rId,
            "http://schemas.openxmlformats.org/officeDocument/2006/relationships/chart",
            target,
        )
        return rId

    def add_worksheet(self, rId: str, target: str) -> str:
        self.add(
            rId,
            "http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet",
            target,
        )
        return rId

    def add_theme(self, rId: str, target: str) -> str:
        self.add(
            rId,
            "http://schemas.openxmlformats.org/officeDocument/2006/relationships/theme",
            target,
        )
        return rId

    def add_styles(self, rId: str, target: str) -> str:
        self.add(
            rId,
            "http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles",
            target,
        )
        return rId

    def add_shared_strings(self, rId: str, target: str) -> str:
        self.add(
            rId,
            "http://schemas.openxmlformats.org/officeDocument/2006/relationships/sharedStrings",
            target,
        )
        return rId

    def add_slide(self, rId: str, target: str) -> str:
        self.add(
            rId,
            "http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide",
            target,
        )
        return rId

    def add_slide_layout(self, rId: str, target: str) -> str:
        self.add(
            rId,
            "http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout",
            target,
        )
        return rId

    def add_slide_master(self, rId: str, target: str) -> str:
        self.add(
            rId,
            "http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster",
            target,
        )
        return rId

    def add_notes_slide(self, rId: str, target: str) -> str:
        self.add(
            rId,
            "http://schemas.openxmlformats.org/officeDocument/2006/relationships/notesSlide",
            target,
        )
        return rId

    def add_notes_master(self, rId: str, target: str) -> str:
        self.add(
            rId,
            "http://schemas.openxmlformats.org/officeDocument/2006/relationships/notesMaster",
            target,
        )
        return rId

    def to_xml(self) -> str:
        """Generate the .rels XML string."""
        parts = ['<?xml version="1.0" encoding="UTF-8" standalone="yes"?>']
        parts.append(f'<Relationships xmlns="{REL_NS}">')
        for rId, type_uri, target, target_mode in self._rels:
            tm = f' TargetMode="{escape_xml(target_mode)}"' if target_mode else ""
            parts.append(
                f'  <Relationship Id="{escape_xml(rId)}"'
                f' Type="{escape_xml(type_uri)}"'
                f' Target="{escape_xml(target)}"{tm}/>'
            )
        parts.append("</Relationships>")
        return "\n".join(parts)

    def __len__(self) -> int:
        return len(self._rels)

    def __bool__(self) -> bool:
        return bool(self._rels)
