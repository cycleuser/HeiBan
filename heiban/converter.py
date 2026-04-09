#!/usr/bin/env python3
"""
Markdown转幻灯片转换器
将包含Mermaid图表的markdown转换为reveal.js幻灯片（自包含HTML，无外部依赖）
"""

import re
import subprocess
import tempfile
from pathlib import Path
from typing import List, Tuple, Optional


def _get_lib_path() -> Path:
    """获取包内lib文件夹路径"""
    try:
        from importlib.resources import files

        return files("heiban.data").joinpath("lib")
    except Exception:
        return Path(__file__).parent.parent / "data" / "lib"


def _load_lib_files() -> dict:
    """加载所有lib文件内容"""
    lib_path = _get_lib_path()
    libs = {}
    for js_file in [
        "reveal.min.js",
        "mermaid.min.js",
        "highlight.min.js",
        "katex.min.js",
        "auto-render.min.js",
    ]:
        fpath = lib_path / "js" / js_file
        if fpath.exists():
            with open(fpath, "r", encoding="utf-8") as f:
                libs[js_file] = f.read()
    for css_file in [
        "reveal.min.css",
        "github-dark-theme.css",
        "github-light-theme.css",
        "katex.min.css",
    ]:
        fpath = lib_path / "css" / css_file
        if fpath.exists():
            with open(fpath, "r", encoding="utf-8") as f:
                libs[css_file] = f.read()
    return libs


_LIBS = _load_lib_files()


class MarkdownToSlideConverter:
    """Markdown转幻灯片转换器"""

    ASPECT_RATIOS = {
        "16:9": (1600, 900),
        "4:3": (1024, 768),
        "21:9": (2100, 900),
        "3:2": (1080, 720),
    }

    def __init__(self):
        self.aspect_ratio = "16:9"
        self.width, self.height = self.ASPECT_RATIOS[self.aspect_ratio]
        self.font_size = 26
        self.mermaid_theme = "default"
        self.code_theme = "dark"

    def set_aspect_ratio(self, ratio: str):
        """设置宽高比"""
        if ratio in self.ASPECT_RATIOS:
            self.aspect_ratio = ratio
            self.width, self.height = self.ASPECT_RATIOS[ratio]

    def parse_markdown(self, md_content: str) -> List[str]:
        """解析markdown内容为幻灯片列表"""
        if not md_content.strip():
            return []
        slides = []
        current_slide = []
        lines = md_content.strip().split("\n")

        for line in lines:
            line = line.rstrip()
            stripped = line.strip()
            if stripped in ("---", "***", "___", "—", "–"):
                if current_slide:
                    slides.append("\n".join(current_slide))
                    current_slide = []
            elif line.startswith("# "):
                if current_slide:
                    slides.append("\n".join(current_slide))
                    current_slide = []
                current_slide.append(line)
            elif line.strip():
                current_slide.append(line)

        if current_slide:
            slides.append("\n".join(current_slide))

        return slides

    def convert_heading(self, line: str) -> str:
        """转换标题"""
        if line.startswith("### "):
            return f"                <h3>{self._escape_html(line[4:])}</h3>"
        elif line.startswith("## "):
            return f"                <h2>{self._escape_html(line[3:])}</h2>"
        elif line.startswith("# "):
            return f"                <h1>{self._escape_html(line[2:])}</h1>"
        return line

    def _escape_html(self, text: str) -> str:
        """转义HTML特殊字符"""
        text = text.replace("&", "&amp;")
        text = text.replace("<", "&lt;")
        text = text.replace(">", "&gt;")
        return text

    def convert_code_block(self, lines: List[str], start_idx: int) -> Tuple[str, int]:
        """转换代码块"""
        code_lines = []
        lang = ""
        i = start_idx + 1
        while i < len(lines):
            if lines[i].startswith("```"):
                break
            code_lines.append(lines[i])
            i += 1

        if code_lines:
            lang = lines[start_idx][3:].strip() if len(lines[start_idx]) > 3 else ""
            code = "\n".join(code_lines)
            if lang:
                return (
                    f'                <pre><code class="language-{lang}">{code}</code></pre>',
                    i,
                )
            return f"                <pre><code>{code}</code></pre>", i
        return "", i

    def convert_mermaid(self, lines: List[str], start_idx: int) -> Tuple[str, int]:
        """转换mermaid图表为SVG"""
        mermaid_lines = []
        i = start_idx + 1
        while i < len(lines):
            if lines[i].strip() == "```":
                break
            mermaid_lines.append(lines[i])
            i += 1

        mermaid_code = "\n".join(mermaid_lines)
        svg_content = self._render_mermaid_to_svg(mermaid_code)

        if svg_content:
            return (f'                <div class="mermaid-svg">{svg_content}</div>', i)
        else:
            return (
                f'                <pre><code class="language-mermaid">{mermaid_code}</code></pre>',
                i,
            )

    def _render_mermaid_to_svg(self, mermaid_code: str) -> Optional[str]:
        """使用mmdc渲染mermaid为SVG"""
        try:
            with tempfile.NamedTemporaryFile(mode="w", suffix=".mmd", delete=False) as f:
                f.write(mermaid_code)
                mmd_file = f.name

            svg_file = mmd_file.replace(".mmd", ".svg")

            theme = "dark" if self.code_theme == "dark" else "default"
            result = subprocess.run(
                ["mmdc", "-i", mmd_file, "-o", svg_file, "-t", theme, "-b", "transparent"],
                capture_output=True,
                timeout=10,
            )

            if result.returncode == 0 and Path(svg_file).exists():
                with open(svg_file, "r") as f:
                    svg = f.read()
                Path(mmd_file).unlink()
                Path(svg_file).unlink()
                return svg
            else:
                Path(mmd_file).unlink(missing_ok=True)
                Path(svg_file).unlink(missing_ok=True)
                return None
        except Exception:
            return None

    def convert_inline_code(self, text: str) -> str:
        """转换行内代码"""
        text = self._escape_html(text)
        text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
        text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
        return text

    def convert_table(self, lines: List[str], start_idx: int) -> Tuple[str, int]:
        """转换表格"""
        rows = []
        i = start_idx
        while i < len(lines) and lines[i].startswith("|"):
            rows.append(lines[i])
            i += 1

        if len(rows) < 2:
            return "", i

        html_lines = ["                <table>"]

        headers = [h.strip() for h in rows[0].strip("|").split("|")]
        html_lines.append(
            "                    <tr>"
            + "".join(f"<th>{self.convert_inline_code(h)}</th>" for h in headers)
            + "</tr>"
        )

        for row in rows[2:]:
            cells = [c.strip() for c in row.strip("|").split("|")]
            html_lines.append(
                "                    <tr>"
                + "".join(f"<td>{self.convert_inline_code(c)}</td>" for c in cells)
                + "</tr>"
            )

        html_lines.append("                </table>")
        return "\n".join(html_lines), i

    def convert_list(self, lines: List[str], start_idx: int) -> Tuple[str, int]:
        """转换无序列表"""
        list_items = []
        i = start_idx
        in_code = False

        while i < len(lines):
            line = lines[i]
            if line.startswith("```"):
                in_code = not in_code
                i += 1
                continue
            if in_code:
                i += 1
                continue
            if line.startswith("- "):
                item = line[2:]
                item = self.convert_inline_code(item)
                list_items.append(f"                    <li>{item}</li>")
                i += 1
            elif line.strip() == "":
                break
            else:
                break

        if list_items:
            return "                <ul>\n" + "\n".join(list_items) + "\n                </ul>", i
        return "", i

    def convert_markdown_to_html(self, md_content: str) -> str:
        """将markdown转换为HTML内容"""
        slides = self.parse_markdown(md_content)
        html_slides = []

        for slide in slides:
            slide_content = []
            lines = slide.strip().split("\n")
            i = 0

            while i < len(lines):
                line = lines[i].rstrip()

                if not line:
                    i += 1
                    continue

                if line.startswith("```mermaid"):
                    mermaid_html, i = self.convert_mermaid(lines, i)
                    slide_content.append(mermaid_html)
                elif line.startswith("```"):
                    code_html, i = self.convert_code_block(lines, i)
                    slide_content.append(code_html)
                elif line.startswith("|"):
                    table_html, i = self.convert_table(lines, i)
                    slide_content.append(table_html)
                elif line.startswith("- "):
                    list_html, i = self.convert_list(lines, i)
                    slide_content.append(list_html)
                elif line.startswith(("### ", "## ", "# ")):
                    slide_content.append(self.convert_heading(line))
                    i += 1
                elif line.startswith(">"):
                    slide_content.append(f"                <p>{self._escape_html(line[2:])}</p>")
                    i += 1
                else:
                    if line.strip():
                        slide_content.append(
                            f"                <p>{self.convert_inline_code(line)}</p>"
                        )
                    i += 1

            html_slides.append(
                "            <section>\n" + "\n".join(slide_content) + "\n            </section>"
            )

        return "\n".join(html_slides)

    def generate_html(self, md_content: str, title: str = "幻灯片") -> str:
        """生成完整的自包含HTML文件"""
        content = self.convert_markdown_to_html(md_content)

        reveal_css = _LIBS.get("reveal.min.css", "")
        reveal_js = _LIBS.get("reveal.min.js", "")
        mermaid_js = _LIBS.get("mermaid.min.js", "")
        highlight_js = _LIBS.get("highlight.min.js", "")
        katex_css = _LIBS.get("katex.min.css", "")
        katex_js = _LIBS.get("katex.min.js", "")
        auto_render_js = _LIBS.get("auto-render.min.js", "")

        is_dark = self.code_theme == "dark"

        if is_dark:
            hljs_css = """
/* GitHub Dark Theme - Dark Mode */
.hljs {
    color: #e1e4e8;
    background: #1a1a1a;
}
.hljs-doctag,
.hljs-keyword,
.hljs-meta .hljs-keyword,
.hljs-template-tag,
.hljs-template-variable,
.hljs-type,
.hljs-variable.language_ {
    color: #f97583;
}
.hljs-title,
.hljs-title.class_,
.hljs-title.class_.inherited__,
.hljs-title.function_ {
    color: #b392f0;
}
.hljs-attr,
.hljs-attribute,
.hljs-literal,
.hljs-meta,
.hljs-number,
.hljs-operator,
.hljs-variable,
.hljs-selector-attr,
.hljs-selector-class,
.hljs-selector-id {
    color: #79b8ff;
}
.hljs-regexp,
.hljs-meta .hljs-string,
.hljs-string {
    color: #9ecbff;
}
.hljs-built_in,
.hljs-symbol {
    color: #ffab70;
}
.hljs-comment,
.hljs-code,
.hljs-formula {
    color: #6a737d;
}
.hljs-name,
.hljs-quote,
.hljs-selector-tag,
.hljs-selector-pseudo {
    color: #85e89d;
}
.hljs-subst {
    color: #e1e4e8;
}
.hljs-section {
    color: #79b8ff;
    font-weight: bold;
}
.hljs-bullet {
    color: #ffea7f;
}
.hljs-emphasis {
    color: #e1e4e8;
    font-style: italic;
}
.hljs-strong {
    color: #e1e4e8;
    font-weight: bold;
}
.hljs-addition {
    color: #bef5cb;
    background-color: #144620;
}
.hljs-deletion {
    color: #fdb8c0;
    background-color: #5a1e1e;
}
.hljs-char.escape_,
.hljs-link,
.hljs-params,
.hljs-property,
.hljs-punctuation,
.hljs-tag {
    color: #e1e4e8;
}
"""
        else:
            hljs_css = """
/* GitHub Light Theme - Light Mode */
.hljs {
    color: #24292e;
    background: #ffffff;
}
.hljs-doctag,
.hljs-keyword,
.hljs-meta .hljs-keyword,
.hljs-template-tag,
.hljs-template-variable,
.hljs-type,
.hljs-variable.language_ {
    color: #d73a49;
}
.hljs-title,
.hljs-title.class_,
.hljs-title.class_.inherited__,
.hljs-title.function_ {
    color: #6f42c1;
}
.hljs-attr,
.hljs-attribute,
.hljs-literal,
.hljs-meta,
.hljs-number,
.hljs-operator,
.hljs-variable,
.hljs-selector-attr,
.hljs-selector-class,
.hljs-selector-id {
    color: #005cc5;
}
.hljs-regexp,
.hljs-meta .hljs-string,
.hljs-string {
    color: #032f62;
}
.hljs-built_in,
.hljs-symbol {
    color: #e36209;
}
.hljs-comment,
.hljs-code,
.hljs-formula {
    color: #6a737d;
}
.hljs-name,
.hljs-quote,
.hljs-selector-tag,
.hljs-selector-pseudo {
    color: #22863a;
}
.hljs-subst {
    color: #24292e;
}
.hljs-section {
    color: #005cc5;
    font-weight: bold;
}
.hljs-bullet {
    color: #735c0f;
}
.hljs-emphasis {
    color: #24292e;
    font-style: italic;
}
.hljs-strong {
    color: #24292e;
    font-weight: bold;
}
.hljs-addition {
    color: #22863a;
    background-color: #f0fff4;
}
.hljs-deletion {
    color: #b31d28;
    background-color: #ffeef0;
}
.hljs-char.escape_,
.hljs-link,
.hljs-params,
.hljs-property,
.hljs-punctuation,
.hljs-tag {
    color: #24292e;
}
"""

        page_bg = "#000000" if is_dark else "#ffffff"
        page_text = "#f0f0f0" if is_dark else "#24292e"
        page_heading = "#4da6ff" if is_dark else "#005cc5"
        pre_bg = "#1a1a1a" if is_dark else "#f6f8fa"
        inline_code_bg = "#2d2d2d" if is_dark else "#e6f3ff"
        inline_code_text = "#ffcc66" if is_dark else "#d73a49"
        table_border = "#333333" if is_dark else "#d1d9e0"
        table_bg = "#1a1a1a" if is_dark else "#ffffff"
        table_even = "#0d0d0d" if is_dark else "#f6f8fa"
        table_th_bg = "#1a1a1a" if is_dark else "#005cc5"
        table_th_text = "#ffffff" if is_dark else "#ffffff"
        table_td_text = "#f0f0f0" if is_dark else "#24292e"
        mermaid_theme = "dark" if is_dark else "default"

        html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
{reveal_css}

/* Page Theme - Override reveal defaults */
body {{
    background: {page_bg} !important;
    color: {page_text} !important;
}}
.reveal-viewport {{
    background: {page_bg} !important;
    color: {page_text} !important;
}}
.reveal {{
    background: {page_bg} !important;
    color: {page_text} !important;
}}
html {{
    background: {page_bg} !important;
}}

{hljs_css}

/* Custom Styles */
.reveal {{
    font-size: {self.font_size}px;
}}
.reveal h1 {{
    font-size: 2.2em;
    color: {page_heading};
    margin-bottom: 0.4em;
}}
.reveal h2 {{
    font-size: 1.6em;
    color: {page_heading};
    margin-bottom: 0.4em;
}}
.reveal h3 {{
    font-size: 1.2em;
    color: {page_heading};
    opacity: 0.85;
}}
.reveal ul, .reveal ol {{
    display: block;
    text-align: left;
    margin-left: 1.5em;
}}
.reveal li {{
    margin: 0.3em 0;
}}
.reveal code {{
    background: {inline_code_bg};
    color: {inline_code_text};
    padding: 0.1em 0.3em;
    border-radius: 3px;
    font-size: 0.9em;
    font-weight: 500;
}}
.reveal pre {{
    width: 100%;
    font-size: 0.65em;
    margin: 0.5em 0;
    background: {pre_bg};
    border-radius: 8px;
    overflow: auto;
    box-shadow: 0 4px 6px rgba(0,0,0,0.2);
    text-align: left;
}}
.reveal pre code {{
    padding: 1em;
    max-height: 600px;
    line-height: 1.5;
    text-align: left;
    display: block;
    color: {page_text};
    background: transparent;
}}
.reveal table {{
    width: 100%;
    border-collapse: collapse;
    font-size: 0.8em;
    box-shadow: 0 2px 4px rgba(0,0,0,0.3);
    background: {table_bg};
}}
.reveal table th {{
    background: {table_th_bg};
    color: {table_th_text};
    padding: 0.5em;
    font-weight: bold;
    border: 1px solid {table_border};
}}
.reveal table td {{
    padding: 0.4em 0.6em;
    border: 1px solid {table_border};
    color: {table_td_text};
}}
.reveal table tr:nth-child(even) {{
    background: {table_even};
}}
.columns {{
    display: flex;
    gap: 2em;
}}
.columns > div {{
    flex: 1;
}}
.reveal img {{
    max-width: 100%;
    height: auto;
}}
.reveal section {{
    padding: 1em;
}}
.reveal p {{
    margin: 0.5em 0;
}}
{katex_css}
    </style>
</head>
<body>
    <div class="reveal">
        <div class="slides">
{content}
        </div>
    </div>
    <script>
{reveal_js}
    </script>
    <script>
{mermaid_js}
    </script>
    <script>
{highlight_js}
    </script>
    <script>
{katex_js}
    </script>
    <script>
{auto_render_js}
    </script>
    <script>
        Reveal.initialize({{
            hash: true,
            slideNumber: 'c/t',
            progress: true,
            controls: true,
            width: {self.width},
            height: {self.height},
            margin: 0.08
        }});
        mermaid.initialize({{ startOnLoad: true, theme: '{mermaid_theme}', securityLevel: 'loose' }});
        hljs.highlightAll();
        renderMathInElement(document.body, {{
            delimiters: [
                {{left: '$$', right: '$$', display: true}},
                {{left: '$', right: '$', display: false}},
                {{left: '\\[', right: '\\]', display: true}},
                {{left: '\\(', right: '\\)', display: false}}
            ]
        }});
    </script>
</body>
</html>"""
        return html

    def convert_file(self, input_path: str, output_path: Optional[str] = None) -> str:
        """转换文件"""
        with open(input_path, "r", encoding="utf-8") as f:
            md_content = f.read()

        if output_path is None:
            output_path = str(Path(input_path).with_suffix(".html"))

        html = self.generate_html(md_content, Path(input_path).stem)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html)

        return output_path


def main():
    """命令行入口"""
    import argparse

    parser = argparse.ArgumentParser(description="Mermaid转HTML幻灯片生成器")
    parser.add_argument("input", help="输入的Markdown文件")
    parser.add_argument("-o", "--output", help="输出的HTML文件")
    parser.add_argument("--width", type=int, default=1280, help="幻灯片宽度")
    parser.add_argument("--height", type=int, default=720, help="幻灯片高度")
    parser.add_argument("--font-size", type=int, default=26, help="字体大小")

    args = parser.parse_args()

    converter = MarkdownToSlideConverter()
    converter.width = args.width
    converter.height = args.height
    converter.font_size = args.font_size

    output = converter.convert_file(args.input, args.output)
    print(f"转换完成: {output}")


if __name__ == "__main__":
    main()
