"""XML generation utilities — string-based XML building for OOXML.

Inspired by @office-open/xml.  Uses plain string concatenation (f-strings +
join) rather than DOM/ElementTree for maximum performance and minimal overhead.
"""

import re
from typing import Dict, List, Optional, Union

_XML_ESCAPE_TABLE = {
    "&": "&amp;",
    '"': "&quot;",
    "'": "&apos;",
    "<": "&lt;",
    ">": "&gt;",
}
_XML_ESCAPE_RE = re.compile(r'[&"\'<>]')


def escape_xml(text: Union[str, int, float, None]) -> str:
    """Escape special XML characters in text content."""
    if text is None:
        return ""
    s = str(text)
    return _XML_ESCAPE_RE.sub(lambda m: _XML_ESCAPE_TABLE[m.group(0)], s)


def attr(name: str, value: Union[str, int, float, bool, None]) -> str:
    """Build an XML attribute string.  Returns '' when value is None/False."""
    if value is None or value is False:
        return ""
    if value is True:
        return f' {name}="true"'
    return f' {name}="{escape_xml(value)}"'


def _marshal_attrs(attrib: Optional[Dict[str, Union[str, int, float, bool, None]]]) -> str:
    """Marshal a dict of attributes into a single string."""
    if not attrib:
        return ""
    parts = []
    for k, v in attrib.items():
        a = attr(k, v)
        if a:
            parts.append(a)
    return "".join(parts)


def elem(
    tag: str,
    content: Union[str, List[str], None] = None,
    attrib: Optional[Dict[str, Union[str, int, float, bool, None]]] = None,
) -> str:
    """Build an XML element with content and attributes.

    Args:
        tag: Element tag name (may include namespace prefix, e.g. 'w:p')
        content: String content or list of child element strings.
        attrib: Optional dict of attributes.

    Returns:
        Complete XML element string.
    """
    attrs = _marshal_attrs(attrib)
    if content is None:
        return f"<{tag}{attrs}/>"
    if isinstance(content, list):
        inner = "".join(content)
    else:
        inner = escape_xml(content)
    return f"<{tag}{attrs}>{inner}</{tag}>"


def elem_empty(
    tag: str,
    attrib: Optional[Dict[str, Union[str, int, float, bool, None]]] = None,
) -> str:
    """Build a self-closing XML element."""
    attrs = _marshal_attrs(attrib)
    return f"<{tag}{attrs}/>"


def cdata(content: str) -> str:
    """Wrap content in a CDATA section."""
    # Ensure no ']]>' inside
    safe = content.replace("]]>", "]]]]><![CDATA[>")
    return f"<![CDATA[{safe}]]>"


class XMLBuilder:
    """Fluent builder for constructing XML trees via context manager / method chaining.

    Usage::

        doc = XMLBuilder("w:document", {"xmlns:w": NS})
        with doc.element("w:body"):
            doc.element("w:p", children=[
                doc.element("w:r", children=[doc.element("w:t", "Hello")])
            ])
        xml_str = doc.to_string()
    """

    def __init__(
        self,
        tag: str,
        attrib: Optional[Dict[str, Union[str, int, float, bool, None]]] = None,
    ):
        self.tag = tag
        self.attrib = attrib or {}
        self.children: List[str] = []
        self._stack: List[List[str]] = []

    def element(
        self,
        tag: str,
        content: Union[str, List[str], None] = None,
        attrib: Optional[Dict[str, Union[str, int, float, bool, None]]] = None,
        children: Optional[List[str]] = None,
    ) -> str:
        """Build and return an XML element string; if children given they become content."""
        if children is not None:
            content = children
        return elem(tag, content, attrib)

    def add(self, xml_str: str) -> "XMLBuilder":
        """Append raw XML to the outermost element."""
        target = self._stack[-1] if self._stack else self.children
        target.append(xml_str)
        return self

    def to_string(self, xml_declaration: bool = False) -> str:
        """Serialize the XML tree to a string."""
        inner = "".join(self.children)
        attrs = _marshal_attrs(self.attrib)
        result = f"<{self.tag}{attrs}>{inner}</{self.tag}>"
        if xml_declaration:
            result = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>' + result
        return result
