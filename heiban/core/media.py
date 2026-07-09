"""Media manager — handles image/audio/video files for OPC packaging."""

import base64
import io
import os
import struct
import imghdr
from typing import Dict, Optional, Tuple
from pathlib import Path


class MediaManager:
    """Collects and tracks media files for inclusion in an OPC package.

    Each medium gets a unique id (e.g. 'rId1') and a part path (e.g.
    'word/media/image1.png').  Content-types are registered automatically.
    """

    # Map image type to extension and content type
    _MIME_MAP = {
        "png": ("image/png", ".png"),
        "jpeg": ("image/jpeg", ".jpg"),
        "jpg": ("image/jpeg", ".jpg"),
        "gif": ("image/gif", ".gif"),
        "bmp": ("image/bmp", ".bmp"),
        "tiff": ("image/tiff", ".tiff"),
        "svg": ("image/svg+xml", ".svg"),
        "webp": ("image/webp", ".webp"),
    }

    def __init__(self, media_dir: str = "word/media", prefix: str = "image"):
        self._media_dir = media_dir
        self._prefix = prefix
        self._items: Dict[str, Tuple[str, bytes, str]] = {}  # rId → (path, data, content_type)
        self._counter = 1
        self._content_types: Dict[str, str] = {}  # path → content_type

    def add_image(
        self, data: bytes, ext: Optional[str] = None, name: Optional[str] = None
    ) -> Tuple[str, str]:
        """Register an image.  Returns (rId, part_path).

        Args:
            data: Raw image bytes.
            ext: File extension (without dot).  Auto-detected if None.
            name: Custom filename stem (auto-generated if None).
        """
        if ext is None:
            ext = _detect_image_ext(data)
        if ext is None:
            ext = "png"

        mime, default_ext = self._MIME_MAP.get(ext.lower(), ("application/octet-stream", f".{ext}"))
        use_ext = f".{ext.lower()}"

        if name is None:
            name = f"{self._prefix}{self._counter}"
        part_path = f"{self._media_dir}/{name}{use_ext}"

        rId = f"rId{self._items.__len__() + 100}"
        self._items[rId] = (part_path, data, mime)
        self._content_types[part_path] = mime
        self._counter += 1
        return rId, part_path

    def add_image_from_file(self, filepath: str) -> Tuple[str, str]:
        """Register an image from a file path."""
        with open(filepath, "rb") as f:
            data = f.read()
        ext = Path(filepath).suffix.lstrip(".")
        return self.add_image(data, ext=ext, name=Path(filepath).stem)

    def add_image_from_pil(self, img) -> Tuple[str, str]:
        """Register a PIL/Pillow Image object."""
        buf = io.BytesIO()
        fmt = img.format or "PNG"
        img.save(buf, format=fmt)
        return self.add_image(buf.getvalue(), ext=fmt.lower())

    def add_image_from_base64(self, b64_str: str, ext: str = "png") -> Tuple[str, str]:
        """Register an image from a base64 string (with or without data URI prefix)."""
        if b64_str.startswith("data:"):
            # Strip data URI header
            header, b64_str = b64_str.split(",", 1)
            if "image/" in header:
                mime_part = header.split(":")[1].split(";")[0]
                ext = mime_part.split("/")[1]
        data = base64.b64decode(b64_str)
        return self.add_image(data, ext=ext)

    def get_data(self, rId: str) -> bytes:
        return self._items[rId][1]

    def get_path(self, rId: str) -> str:
        return self._items[rId][0]

    def get_content_type(self, rId: str) -> str:
        return self._items[rId][2]

    @property
    def items(self):
        """Iterator over (rId, part_path, data, content_type) tuples."""
        for rId, (path, data, ct) in self._items.items():
            yield rId, path, data, ct

    @property
    def content_types(self) -> Dict[str, str]:
        return dict(self._content_types)

    def __len__(self) -> int:
        return len(self._items)

    def __bool__(self) -> bool:
        return bool(self._items)


def _detect_image_ext(data: bytes) -> Optional[str]:
    """Try to detect image type from magic bytes."""
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    if data.startswith(b"\xff\xd8\xff"):
        return "jpeg"
    if data.startswith(b"GIF87a") or data.startswith(b"GIF89a"):
        return "gif"
    if data.startswith(b"BM"):
        return "bmp"
    if data.startswith(b"<svg") or data.startswith(b"<?xml"):
        # Basic check for SVG
        text = data[:200].decode("utf-8", errors="ignore").strip().lower()
        if "<svg" in text:
            return "svg"
    if data.startswith(b"RIFF") and data[8:12] == b"WEBP":
        return "webp"
    return None
