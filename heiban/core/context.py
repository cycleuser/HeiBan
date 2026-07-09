"""WriteContext — shared state during OOXML compilation.

Inspired by @office-open/core's WriteContext.  Holds relationships, media,
content types, and format-specific state while the compiler walks the AST
and produces XML parts.
"""

from typing import Dict, List, Optional, Set, Tuple
from heiban.core.relationships import RelationshipsBuilder
from heiban.core.content_types import ContentTypesBuilder
from heiban.core.media import MediaManager


class WriteContext:
    """Base context for compiling an OOXML package.

    Format-specific compilers (DOCX, PPTX, XLSX) subclass this and add their
    own state (e.g. numbering definitions, shared strings, slide count).
    """

    def __init__(self, media_dir: str = "word/media", media_prefix: str = "image"):
        self.media: MediaManager = MediaManager(media_dir=media_dir, prefix=media_prefix)
        self.content_types: ContentTypesBuilder = ContentTypesBuilder()

        # Rels: map from rels-part-path to RelationshipsBuilder
        self._rels: Dict[str, RelationshipsBuilder] = {}
        self._current_rels_path: Optional[str] = None

        # Track all part paths for content-type registration
        self._parts: Set[str] = set()

    # --- Relationships ---

    def set_current_rels(self, path: str):
        """Set the active .rels file path that subsequent add_relationship()
        calls target."""
        self._current_rels_path = path
        if path not in self._rels:
            self._rels[path] = RelationshipsBuilder()

    @property
    def current_rels(self) -> Optional[RelationshipsBuilder]:
        if self._current_rels_path is None:
            return None
        return self._rels.get(self._current_rels_path)

    def add_relationship(
        self, rId: str, type_uri: str, target: str, target_mode: Optional[str] = None
    ):
        """Add a relationship to the currently-active .rels file."""
        rels = self.current_rels
        if rels is None:
            raise RuntimeError("No active .rels file.  Call set_current_rels() first.")
        rels.add(rId, type_uri, target, target_mode)

    def add_media_relationship(self, rId: str, target: str):
        """Shorthand for adding an image relationship."""
        self.add_relationship(
            rId,
            "http://schemas.openxmlformats.org/officeDocument/2006/relationships/image",
            target,
        )

    def get_rels(self) -> Dict[str, str]:
        """Return all .rels files as {path: xml_string}."""
        result = {}
        for path, builder in self._rels.items():
            result[path] = builder.to_xml()
        return result

    # --- Content Types ---

    def register_part(self, part_path: str, content_type: str):
        """Register a part with its content type."""
        self.content_types.add_override(part_path, content_type)
        self._parts.add(part_path)

    def register_default(self, extension: str, content_type: str):
        """Register a default content type for an extension."""
        self.content_types.add_default(extension, content_type)

    # --- Media ---

    def add_image(self, data: bytes, ext: Optional[str] = None) -> Tuple[str, str]:
        """Add an image and return (rId, part_path)."""
        rId, path = self.media.add_image(data, ext=ext)
        self.register_part(path, self.media.get_content_type(rId))
        return rId, path

    def add_image_from_file(self, filepath: str) -> Tuple[str, str]:
        rId, path = self.media.add_image_from_file(filepath)
        self.register_part(path, self.media.get_content_type(rId))
        return rId, path

    # --- Final assembly ---

    def collect_content_types(self) -> str:
        """Return the [Content_Types].xml string."""
        return self.content_types.to_xml()

    def collect_media(self) -> Dict[str, bytes]:
        """Return {part_path: data} for all media files."""
        result = {}
        for rId, path, data, ct in self.media.items:
            result[path] = data
        return result
