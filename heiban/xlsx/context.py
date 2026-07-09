"""XLSX write context — extends WriteContext with Excel-specific state."""

from typing import List
from heiban.core.context import WriteContext
from heiban.core.relationships import RelationshipsBuilder


# OOXML Spreadsheet namespaces
X_NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
R_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"

# Content types
WORKBOOK_CT = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"
WORKSHEET_CT = "application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"
STYLES_CT = "application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"
SHARED_STRINGS_CT = "application/vnd.openxmlformats-officedocument.spreadsheetml.sharedStrings+xml"
THEME_CT = "application/vnd.openxmlformats-officedocument.theme+xml"


class XlsxWriteContext(WriteContext):
    """Excel-specific compilation context.

    Tracks worksheets, shared strings, and styles.
    """

    def __init__(self):
        super().__init__(media_dir="xl/media", media_prefix="image")

        # Register content types
        self.register_default("rels", "application/vnd.openxmlformats-package.relationships+xml")
        self.register_part("/xl/workbook.xml", WORKBOOK_CT)
        self.register_part("/xl/styles.xml", STYLES_CT)
        self.register_part("/xl/sharedStrings.xml", SHARED_STRINGS_CT)
        self.register_part("/xl/theme/theme1.xml", THEME_CT)

        # Shared strings
        self._shared_strings: List[str] = []
        self._string_index: dict = {}

        # Setup workbook relationships
        self.set_current_rels("xl/_rels/workbook.xml.rels")
        self._wb_rels = self.current_rels
        self._wb_rels.add_styles("rIdStyles", "styles.xml")
        self._wb_rels.add_shared_strings("rIdSharedStrings", "sharedStrings.xml")
        self._wb_rels.add_theme("rIdTheme", "theme/theme1.xml")

        # Setup worksheet-level relationship tracking
        self._sheet_rels: dict = {}  # sheet_path → RelationshipsBuilder

    def add_worksheet(self, sheet_num: int, name: str = "") -> str:
        """Register a new worksheet. Returns the relationship ID."""
        safe_name = name or f"Sheet{sheet_num}"
        sheet_path = f"worksheets/sheet{sheet_num}.xml"
        rels_path = f"xl/worksheets/_rels/sheet{sheet_num}.xml.rels"

        self.register_part(f"/xl/{sheet_path}", WORKSHEET_CT)

        rId = f"rIdSheet{sheet_num}"
        self._wb_rels.add_worksheet(rId, sheet_path)

        # Create worksheet relationships
        ws_rels = RelationshipsBuilder()
        self._sheet_rels[sheet_path] = ws_rels
        self._rels[rels_path] = ws_rels

        return rId

    def get_or_add_shared_string(self, text: str) -> int:
        """Add a string to the shared strings table and return its index."""
        if text in self._string_index:
            return self._string_index[text]
        idx = len(self._shared_strings)
        self._shared_strings.append(text)
        self._string_index[text] = idx
        return idx

    def build_shared_strings_xml(self) -> str:
        """Generate the xl/sharedStrings.xml content."""
        count = len(self._shared_strings)
        unique_count = count  # All strings are unique by our dedup

        items = []
        for s in self._shared_strings:
            from heiban.core.xml_utils import escape_xml
            text = escape_xml(s)
            items.append(f"  <si><t>{text}</t></si>")

        return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<sst xmlns="{X_NS}" count="{count}" uniqueCount="{unique_count}">
{chr(10).join(items)}
</sst>"""

    def build_package_rels(self) -> str:
        """Build root _rels/.rels."""
        rels = RelationshipsBuilder()
        rels.add(
            "rId1",
            "http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument",
            "xl/workbook.xml",
        )
        return rels.to_xml()

    def build_styles_xml(self) -> str:
        """Generate a minimal styles.xml for XLSX."""
        return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
  <fonts count="3">
    <font><sz val="11"/><name val="Calibri"/></font>
    <font><b/><sz val="11"/><name val="Calibri"/></font>
    <font><sz val="10"/><name val="Consolas"/></font>
  </fonts>
  <fills count="3">
    <fill><patternFill patternType="none"/></fill>
    <fill><patternFill patternType="gray125"/></fill>
    <fill><patternFill patternType="solid"><fgColor rgb="FF2E75B6"/><bgColor indexed="64"/></patternFill></fill>
  </fills>
  <borders count="1">
    <border><left/><right/><top/><bottom/><diagonal/></border>
  </borders>
  <cellStyleXfs count="1">
    <xf numFmtId="0" fontId="0" fillId="0" borderId="0"/>
  </cellStyleXfs>
  <cellXfs count="3">
    <xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/>
    <xf numFmtId="0" fontId="1" fillId="2" borderId="0" xfId="0" applyFont="1" applyFill="1"/>
    <xf numFmtId="0" fontId="2" fillId="0" borderId="0" xfId="0" applyFont="1"/>
  </cellXfs>
</styleSheet>"""

    def build_theme_xml(self) -> str:
        """Generate minimal theme XML (same as PPTX theme)."""
        from heiban.pptx.parts.theme import build_theme_xml
        return build_theme_xml()
