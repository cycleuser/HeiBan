"""HeiBan PPTX 导出器测试"""

from pathlib import Path

import pytest

from heiban.pptx_exporter import (
    PPTXExporter, _strip_html, _parse_html_elements,
    _render_latex_to_image, _fix_latex_backslashes,
)
from heiban.v2.md_parser import MarkdownSlideParser


class TestStripHtml:
    def test_simple_text(self):
        assert _strip_html("<p>Hello</p>") == "Hello"

    def test_bold(self):
        assert _strip_html("<strong>bold</strong>") == "bold"

    def test_italic(self):
        assert _strip_html("<em>italic</em>") == "italic"

    def test_code(self):
        assert _strip_html("<code>code</code>") == "code"

    def test_link(self):
        assert _strip_html('<a href="http://example.com">link</a>') == "link"

    def test_entities(self):
        assert _strip_html("&amp; &lt; &gt;") == "& < >"

    def test_br_to_newline(self):
        result = _strip_html("line1<br/>line2")
        assert "line1" in result and "line2" in result

    def test_nested(self):
        assert _strip_html("<p><strong>bold</strong> and <em>italic</em></p>") == "bold and italic"


class TestParseHtmlElements:
    def test_h1(self):
        elems = _parse_html_elements("<h1>Title</h1><p>Content</p>")
        headings = [e for e in elems if e["type"] == "heading"]
        assert len(headings) >= 1
        assert headings[0]["text"] == "Title"
        assert headings[0]["level"] == 1

    def test_no_heading(self):
        elems = _parse_html_elements("<p>Just a paragraph</p>")
        headings = [e for e in elems if e["type"] == "heading"]
        assert len(headings) == 0


class TestPPTXExporter:
    """测试 PPTX 导出器"""

    def test_export_basic(self, tmp_path):
        parser = MarkdownSlideParser()
        slides = parser.parse("# Hello\n\n---\n\n# World")

        exporter = PPTXExporter()
        output = exporter.export(slides, str(tmp_path / "test.pptx"))
        assert Path(output).exists()
        assert Path(output).stat().st_size > 0

    def test_export_with_code(self, tmp_path):
        parser = MarkdownSlideParser()
        slides = parser.parse('```python\nprint("hello")\n```')

        exporter = PPTXExporter()
        output = exporter.export(slides, str(tmp_path / "code.pptx"))
        assert Path(output).exists()

    def test_export_with_table(self, tmp_path):
        parser = MarkdownSlideParser()
        slides = parser.parse("| A | B |\n|---|---|\n| 1 | 2 |")

        exporter = PPTXExporter()
        output = exporter.export(slides, str(tmp_path / "table.pptx"))
        assert Path(output).exists()

    def test_export_with_list(self, tmp_path):
        parser = MarkdownSlideParser()
        slides = parser.parse("- Item 1\n- Item 2\n- Item 3")

        exporter = PPTXExporter()
        output = exporter.export(slides, str(tmp_path / "list.pptx"))
        assert Path(output).exists()

    def test_export_with_ordered_list(self, tmp_path):
        parser = MarkdownSlideParser()
        slides = parser.parse("1. First\n2. Second\n3. Third")

        exporter = PPTXExporter()
        output = exporter.export(slides, str(tmp_path / "olist.pptx"))
        assert Path(output).exists()

    def test_export_with_blockquote(self, tmp_path):
        parser = MarkdownSlideParser()
        slides = parser.parse("> This is a quote")

        exporter = PPTXExporter()
        output = exporter.export(slides, str(tmp_path / "quote.pptx"))
        assert Path(output).exists()

    def test_export_themes(self, tmp_path):
        parser = MarkdownSlideParser()
        slides = parser.parse("# Hello")

        for theme in ["black", "white", "league", "beige"]:
            exporter = PPTXExporter()
            exporter.theme = theme
            output = exporter.export(slides, str(tmp_path / f"theme_{theme}.pptx"))
            assert Path(output).exists()

    def test_export_aspect_ratios(self, tmp_path):
        parser = MarkdownSlideParser()
        slides = parser.parse("# Hello")

        for ratio in ["16:9", "4:3", "21:9", "3:2"]:
            exporter = PPTXExporter()
            exporter.aspect_ratio = ratio
            output = exporter.export(slides, str(tmp_path / f"ratio_{ratio}.pptx"))
            assert Path(output).exists()

    def test_export_empty_slides(self, tmp_path):
        exporter = PPTXExporter()
        output = exporter.export([], str(tmp_path / "empty.pptx"))
        assert Path(output).exists()

    def test_export_with_background_attr(self, tmp_path):
        parser = MarkdownSlideParser()
        slides = parser.parse('<!-- .slide: data-background="#ff0000" -->\n\n# Hello')

        exporter = PPTXExporter()
        output = exporter.export(slides, str(tmp_path / "bg.pptx"))
        assert Path(output).exists()

    def test_export_from_converter(self, tmp_path):
        from heiban.v2.converter import MarkdownToSlideConverterV2

        converter = MarkdownToSlideConverterV2()
        exporter = PPTXExporter()

        output = exporter.export_from_converter(
            converter, "# Hello\n\n---\n\n# World",
            str(tmp_path / "converter.pptx"),
        )
        assert Path(output).exists()

    def test_export_convenience_function(self, tmp_path):
        from heiban.pptx_exporter import export_pptx

        parser = MarkdownSlideParser()
        slides = parser.parse("# Hello")

        output = export_pptx(slides, str(tmp_path / "conv.pptx"), theme="white")
        assert Path(output).exists()


class TestMathRendering:
    def test_fix_backslashes_matrix(self):
        raw = r"\begin{bmatrix} a & b \ c & d \end{bmatrix}"
        fixed = _fix_latex_backslashes(raw)
        assert "\\\\" in fixed or "\\\\\\ " in fixed

    def test_fix_backslashes_preserves_commands(self):
        raw = r"\frac{1}{\sigma\sqrt{2\pi}}"
        fixed = _fix_latex_backslashes(raw)
        assert fixed == raw

    def test_render_simple_formula(self):
        result = _render_latex_to_image(
            r"$e^{i\pi} + 1 = 0$", dpi=150, font_size=28,
            text_color="#000000", bg_color="#FFFFFF",
        )
        assert result is not None
        assert len(result) > 200

    def test_render_matrix_formula(self):
        result = _render_latex_to_image(
            r"$$\begin{bmatrix} a & b \\ c & d \end{bmatrix}$$",
            dpi=150, font_size=36, text_color="#000000", bg_color="#FFFFFF",
        )
        assert result is not None
        assert len(result) > 200


class TestPDFExporter:
    """测试 PDF 导出器"""

    def test_backend_detection(self):
        from heiban.pdf_exporter import PDFExporter
        exporter = PDFExporter()
        assert exporter.backend_name in ("weasyprint", "playwright", "none")

    def test_explicit_backend(self):
        from heiban.pdf_exporter import PDFExporter
        exporter = PDFExporter(backend="weasyprint")
        assert exporter.backend_name == "weasyprint"

    def test_export_missing_file_raises(self, tmp_path):
        from heiban.pdf_exporter import PDFExporter
        exporter = PDFExporter()
        with pytest.raises(FileNotFoundError):
            exporter.export_html_file(str(tmp_path / "nonexistent.html"))


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
