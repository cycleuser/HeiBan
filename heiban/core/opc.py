"""OPC (Open Packaging Conventions) Packer — assembles a ZIP with proper
OOXML structure: [Content_Types].xml, _rels/.rels, typed parts, and media.

Inspired by @office-open/core's packer.ts — uses Python's zipfile for ZIP
assembly with fflate-equivalent DEFLATE compression (zlib).
"""

import zipfile
import io
from typing import Dict, Optional

Zippable = Dict[str, bytes]  # path → binary data


class OPCPacker:
    """Assembles an OOXML-compliant ZIP archive.

    Usage::

        packer = OPCPacker()
        packer.add("[Content_Types].xml", xml_bytes)
        packer.add("_rels/.rels", rels_bytes)
        packer.add("word/document.xml", doc_bytes)
        result = packer.pack()  # bytes
    """

    def __init__(self):
        self._files: Dict[str, bytes] = {}

    def add(self, path: str, data: bytes):
        """Add a file to the package."""
        self._files[path] = data

    def add_xml(self, path: str, xml_str: str):
        """Add an XML file (auto-encodes to UTF-8)."""
        self._files[path] = xml_str.encode("utf-8")

    def add_all(self, files: Dict[str, bytes]):
        """Add multiple files at once."""
        self._files.update(files)

    def add_all_xml(self, files: Dict[str, str]):
        """Add multiple XML strings at once."""
        for path, xml_str in files.items():
            self.add_xml(path, xml_str)

    def pack(self) -> bytes:
        """Assemble the ZIP archive and return as bytes."""
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            # [Content_Types].xml MUST be first (per OPC spec, though not strictly required)
            ct = self._files.pop("[Content_Types].xml", None)
            if ct is not None:
                zf.writestr("[Content_Types].xml", ct)

            for path, data in sorted(self._files.items()):
                zf.writestr(path, data)
        return buf.getvalue()

    def save(self, filepath: str):
        """Pack and save to a file."""
        data = self.pack()
        with open(filepath, "wb") as f:
            f.write(data)

    def __len__(self) -> int:
        return len(self._files)
