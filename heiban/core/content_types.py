"""Content Types ([Content_Types].xml) builder.

OOXML requires a [Content_Types].xml at the root of the ZIP that declares the
MIME type of every part.  This module builds that XML.
"""

from typing import Dict, Optional
from heiban.core.xml_utils import escape_xml

_CT_NS = "http://schemas.openxmlformats.org/package/2006/content-types"


class ContentTypesBuilder:
    """Builds the [Content_Types].xml document."""

    def __init__(self):
        self._defaults: Dict[str, str] = {}  # ext → content_type
        self._overrides: Dict[str, str] = {}  # part_path → content_type

    def add_default(self, extension: str, content_type: str):
        """Map a file extension to a content type (e.g. 'rels' → rels type)."""
        ext = extension.lstrip(".")
        self._defaults[ext] = content_type

    def add_override(self, part_path: str, content_type: str):
        """Set an explicit content type for a specific part path."""
        # Ensure paths start with /
        if not part_path.startswith("/"):
            part_path = "/" + part_path
        self._overrides[part_path] = content_type

    def add_defaults_from_dict(self, mapping: Dict[str, str]):
        for ext, ct in mapping.items():
            self.add_default(ext, ct)

    def add_overrides_from_dict(self, mapping: Dict[str, str]):
        for path, ct in mapping.items():
            self.add_override(path, ct)

    def to_xml(self) -> str:
        """Generate the [Content_Types].xml string."""
        parts = ['<?xml version="1.0" encoding="UTF-8" standalone="yes"?>']
        parts.append(f'<Types xmlns="{_CT_NS}">')

        # Default extensions
        for ext in sorted(self._defaults):
            ct = self._defaults[ext]
            parts.append(f'  <Default Extension="{escape_xml(ext)}" ContentType="{escape_xml(ct)}"/>')

        # Overrides
        for path in sorted(self._overrides):
            ct = self._overrides[path]
            parts.append(f'  <Override PartName="{escape_xml(path)}" ContentType="{escape_xml(ct)}"/>')

        parts.append("</Types>")
        return "\n".join(parts)
