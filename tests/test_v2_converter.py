"""HeiBan v2 转换器测试"""

import pytest
from pathlib import Path

from heiban.v2.md_parser import MarkdownSlideParser, Slide, SlideAttributes
from heiban.v2.converter import MarkdownToSlideConverterV2


class TestMarkdownSlideParser:
    """测试 Markdown 幻灯片解析器"""

    def test_parse_single_slide(self):
        parser = MarkdownSlideParser()
        slides = parser.parse("# Hello\n\nWorld")
        assert len(slides) == 1
        assert "<h1>Hello</h1>" in slides[0].content
        assert "<p>World</p>" in slides[0].content

    def test_parse_multiple_slides(self):
        parser = MarkdownSlideParser()
        slides = parser.parse("# Slide 1\n\n---\n\n# Slide 2")
        assert len(slides) == 2
        assert "<h1>Slide 1</h1>" in slides[0].content
        assert "<h1>Slide 2</h1>" in slides[1].content

    def test_parse_horizontal_slides(self):
        parser = MarkdownSlideParser()
        content = "# Slide 1\n\n---\n\n# Slide 2\n\n---\n\n# Slide 3"
        slides = parser.parse(content)
        assert len(slides) == 3
        assert not slides[0].is_vertical
        assert not slides[1].is_vertical
        assert not slides[2].is_vertical

    def test_parse_vertical_slides(self):
        parser = MarkdownSlideParser()
        content = "# Slide 1\n\n----\n\n# Slide 2\n\n----\n\n# Slide 3"
        slides = parser.parse(content)
        assert len(slides) == 3
        assert not slides[0].is_vertical
        assert slides[1].is_vertical
        assert slides[2].is_vertical

    def test_parse_mixed_slides(self):
        parser = MarkdownSlideParser()
        content = "# Slide 1\n\n---\n\n# Slide 2\n\n----\n\n# Slide 3\n\n---\n\n# Slide 4"
        slides = parser.parse(content)
        assert len(slides) == 4
        assert not slides[0].is_vertical
        assert not slides[1].is_vertical
        assert slides[2].is_vertical
        assert not slides[3].is_vertical

    def test_parse_slide_attributes(self):
        parser = MarkdownSlideParser()
        content = '<!-- .slide: data-background="#ff0000" data-transition="zoom" -->\n\n# Hello'
        slides = parser.parse(content)
        assert len(slides) == 1
        assert slides[0].attributes is not None
        assert slides[0].attributes.background_color == "#ff0000"
        assert slides[0].attributes.transition == "zoom"

    def test_parse_speaker_notes(self):
        parser = MarkdownSlideParser()
        content = '# Hello\n\n<aside class="notes">This is a note</aside>'
        slides = parser.parse(content)
        assert len(slides) == 1
        assert slides[0].notes == "This is a note"

    def test_parse_gfm_table(self):
        parser = MarkdownSlideParser()
        content = "| A | B |\n|---|---|\n| 1 | 2 |"
        slides = parser.parse(content)
        assert len(slides) == 1
        assert "<table>" in slides[0].content
        assert "<th>A</th>" in slides[0].content
        assert "<td>1</td>" in slides[0].content

    def test_parse_task_list(self):
        parser = MarkdownSlideParser()
        content = "- [x] Done\n- [ ] Todo"
        slides = parser.parse(content)
        assert len(slides) == 1
        assert "task-list-item" in slides[0].content

    def test_parse_strikethrough(self):
        parser = MarkdownSlideParser()
        content = "~~deleted~~"
        slides = parser.parse(content)
        assert len(slides) == 1
        assert "<s>deleted</s>" in slides[0].content or "<del>deleted</del>" in slides[0].content

    def test_parse_footnotes(self):
        parser = MarkdownSlideParser()
        content = "Text[^1]\n\n[^1]: Note"
        slides = parser.parse(content)
        assert len(slides) == 1
        assert "footnote" in slides[0].content.lower() or "<sup>" in slides[0].content

    def test_parse_nested_lists(self):
        parser = MarkdownSlideParser()
        content = "- Item 1\n  - Sub 1\n  - Sub 2\n- Item 2"
        slides = parser.parse(content)
        assert len(slides) == 1
        assert slides[0].content.count("<ul>") >= 2

    def test_parse_ordered_lists(self):
        parser = MarkdownSlideParser()
        content = "1. First\n2. Second\n3. Third"
        slides = parser.parse(content)
        assert len(slides) == 1
        assert "<ol>" in slides[0].content

    def test_parse_blockquote(self):
        parser = MarkdownSlideParser()
        content = "> This is a quote"
        slides = parser.parse(content)
        assert len(slides) == 1
        assert "<blockquote>" in slides[0].content

    def test_parse_empty_content(self):
        parser = MarkdownSlideParser()
        slides = parser.parse("")
        assert len(slides) == 0

    def test_parse_code_block(self):
        parser = MarkdownSlideParser()
        content = '```python\nprint("hello")\n```'
        slides = parser.parse(content)
        assert len(slides) == 1
        assert '<pre><code class="language-python">' in slides[0].content
        assert "print" in slides[0].content


class TestMarkdownToSlideConverterV2:
    """测试 v2 转换器"""

    def test_convert_basic(self):
        converter = MarkdownToSlideConverterV2()
        html = converter.convert("# Hello\n\n---\n\n# World", title="Test")
        assert "<!DOCTYPE html>" in html
        assert "Reveal.initialize" in html
        assert "<h1>Hello</h1>" in html
        assert "<h1>World</h1>" in html

    def test_convert_embedded(self):
        converter = MarkdownToSlideConverterV2()
        html = converter.convert("# Hello", title="Test", use_cdn=False)
        assert "reveal.min.js" in html or "Reveal" in html
        assert "katex" in html.lower()
        assert "mermaid" in html.lower()

    def test_convert_cdn(self):
        converter = MarkdownToSlideConverterV2()
        html = converter.convert("# Hello", title="Test", use_cdn=True)
        assert "cdn.jsdelivr.net" in html
        assert "reveal.min.css" in html

    def test_convert_themes(self):
        converter = MarkdownToSlideConverterV2()
        for theme in ["black", "white", "beige", "sky", "night"]:
            converter.theme = theme
            html = converter.convert("# Hello", title="Test")
            assert "<!DOCTYPE html>" in html

    def test_convert_transitions(self):
        converter = MarkdownToSlideConverterV2()
        for transition in ["slide", "fade", "zoom", "convex", "concave", "none"]:
            converter.transition = transition
            html = converter.convert("# Hello", title="Test")
            assert f"'{transition}'" in html or f'"{transition}"' in html

    def test_convert_aspect_ratios(self):
        converter = MarkdownToSlideConverterV2()
        for ratio, (w, h) in MarkdownToSlideConverterV2.ASPECT_RATIOS.items():
            converter.set_aspect_ratio(ratio)
            html = converter.convert("# Hello", title="Test")
            assert str(w) in html
            assert str(h) in html

    def test_convert_with_table(self):
        converter = MarkdownToSlideConverterV2()
        md = "| A | B |\n|---|---|\n| 1 | 2 |"
        html = converter.convert(md, title="Test")
        assert "<table>" in html
        assert "<th>A</th>" in html
        assert "<td>1</td>" in html

    def test_convert_with_code(self):
        converter = MarkdownToSlideConverterV2()
        md = '```python\nprint("hello")\n```'
        html = converter.convert(md, title="Test")
        assert '<code class="language-python">' in html

    def test_convert_with_blockquote(self):
        converter = MarkdownToSlideConverterV2()
        md = "> This is a quote"
        html = converter.convert(md, title="Test")
        assert "<blockquote>" in html

    def test_convert_with_task_list(self):
        converter = MarkdownToSlideConverterV2()
        md = "- [x] Done\n- [ ] Todo"
        html = converter.convert(md, title="Test")
        assert "task-list-item" in html

    def test_convert_with_notes(self):
        converter = MarkdownToSlideConverterV2()
        md = '# Hello\n\n<aside class="notes">Speaker notes</aside>'
        html = converter.convert(md, title="Test")
        assert '<aside class="notes">Speaker notes</aside>' in html

    def test_convert_with_background(self):
        converter = MarkdownToSlideConverterV2()
        md = '<!-- .slide: data-background="#ff0000" -->\n\n# Hello'
        html = converter.convert(md, title="Test")
        assert 'data-background="#ff0000"' in html or 'data-background-color="#ff0000"' in html

    def test_convert_with_auto_animate(self):
        converter = MarkdownToSlideConverterV2()
        md = "<!-- .slide: data-auto-animate -->\n\n# Hello"
        html = converter.convert(md, title="Test")
        assert "data-auto-animate" in html

    def test_convert_file(self, tmp_path):
        converter = MarkdownToSlideConverterV2()
        md_file = tmp_path / "test.md"
        md_file.write_text("# Hello\n\n---\n\n# World", encoding="utf-8")

        output = converter.convert_file(str(md_file))
        assert Path(output).exists()
        content = Path(output).read_text(encoding="utf-8")
        assert "<!DOCTYPE html>" in content

    def test_convert_file_with_output(self, tmp_path):
        converter = MarkdownToSlideConverterV2()
        md_file = tmp_path / "test.md"
        md_file.write_text("# Hello", encoding="utf-8")
        output_file = tmp_path / "custom.html"

        output = converter.convert_file(str(md_file), str(output_file))
        assert output == str(output_file)
        assert Path(output).exists()
