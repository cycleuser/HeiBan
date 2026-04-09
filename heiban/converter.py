#!/usr/bin/env python3
"""
Markdown转幻灯片转换器
将包含Mermaid图表的markdown转换为reveal.js幻灯片
"""

import re
from pathlib import Path
from typing import List, Tuple, Optional


class MarkdownToSlideConverter:
    """Markdown转幻灯片转换器"""

    CSS_TEMPLATE = """
        :root {
            --r-background-color: #ffffff;
            --r-main-font: 'PingFang SC', 'Microsoft YaHei', sans-serif;
            --r-heading-font: 'PingFang SC', 'Microsoft YaHei', sans-serif;
        }
        .reveal { font-size: {font_size}px; }
        .reveal h1 {{ font-size: 2em; color: #1a1a2e; margin-bottom: 0.4em; }}
        .reveal h2 {{ font-size: 1.5em; color: #2d5a7b; margin-bottom: 0.4em; }}
        .reveal h3 {{ font-size: 1.2em; color: #4a4a6a; }}
        .reveal ul, .reveal ol {{ display: block; text-align: left; margin-left: 1.5em; }}
        .reveal li {{ margin: 0.3em 0; }}
        .reveal code {{ background: #f5f5f5; padding: 0.1em 0.3em; border-radius: 3px; font-size: 0.9em; }}
        .reveal pre {{ width: 100%; font-size: 0.6em; margin: 0.3em 0; background: #1e1e1e; border-radius: 6px; overflow: auto; text-align: left; }}
        .reveal pre code {{ padding: 0.6em; background: transparent; color: #d4d4d4; display: block; overflow-x: auto; white-space: pre; line-height: 1.4; text-align: left; }}
        .reveal table {{ width: 100%; border-collapse: collapse; font-size: 0.75em; }}
        .reveal table th, .reveal table td {{ padding: 0.3em 0.6em; border: 1px solid #ddd; text-align: left; }}
        .reveal table th {{ background: #2d5a7b; color: white; }}
        .reveal table tr:nth-child(even) {{ background: #f8f9fa; }}
        .columns {{ display: flex; gap: 1.5em; }}
        .columns > div {{ flex: 1; }}
        .reveal img {{ max-width: 100%; height: auto; }}
    """

    HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <link rel="stylesheet" href="lib/css/reveal.min.css">
    <link rel="stylesheet" href="lib/css/github-dark.min.css">
    <style>
{styles}
    </style>
</head>
<body>
    <div class="reveal">
        <div class="slides">
{content}
        </div>
    </div>
    <script src="lib/js/reveal.min.js"></script>
    <script src="lib/js/mermaid.min.js"></script>
    <script src="lib/js/highlight.min.js"></script>
    <script>
        Reveal.initialize({{
            hash: true,
            slideNumber: 'c/t',
            progress: true,
            controls: true,
            width: {width},
            height: {height},
            margin: 0.08
        }});
        mermaid.initialize({{ startOnLoad: true, theme: '{mermaid_theme}', securityLevel: 'loose' }});
        hljs.highlightAll();
    </script>
</body>
</html>"""

    SLIDE_TEMPLATE = """
            <section>
{content}
            </section>"""

    def __init__(self):
        self.width = 1280
        self.height = 720
        self.font_size = 26
        self.mermaid_theme = "default"

    def parse_markdown(self, md_content: str) -> List[str]:
        """解析markdown内容为幻灯片列表"""
        if not md_content.strip():
            return []
        slides = []
        current_slide = []
        lines = md_content.strip().split("\n")

        for line in lines:
            line = line.rstrip()
            if line.strip() == "---":
                if current_slide:
                    slides.append("\n".join(current_slide))
                    current_slide = []
            elif line.startswith("## ") or line.startswith("# "):
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
        """转换mermaid图表"""
        mermaid_lines = []
        i = start_idx + 1
        while i < len(lines):
            if lines[i].strip() == "```":
                break
            mermaid_lines.append(lines[i])
            i += 1

        return (
            f'                <div class="mermaid">\n{"\\n".join(mermaid_lines)}\n                </div>',
            i,
        )

    def convert_inline_code(self, text: str) -> str:
        """转换行内代码"""
        text = self._escape_html(text)
        text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
        text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
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

        # 表头
        headers = [h.strip() for h in rows[0].strip("|").split("|")]
        html_lines.append(
            "                    <tr>"
            + "".join(f"<th>{self._escape_html(h)}</th>" for h in headers)
            + "</tr>"
        )

        # 数据行（跳过分割线）
        for row in rows[2:]:
            cells = [c.strip() for c in row.strip("|").split("|")]
            html_lines.append(
                "                    <tr>"
                + "".join(f"<td>{self._escape_html(c)}</td>" for c in cells)
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

            html_slides.append(self.SLIDE_TEMPLATE.format(content="\n".join(slide_content)))

        return "\n".join(html_slides)

    def generate_html(self, md_content: str, title: str = "幻灯片") -> str:
        """生成完整的HTML文件"""
        content = self.convert_markdown_to_html(md_content)
        styles = self.CSS_TEMPLATE.replace("{font_size}", str(self.font_size))

        return self.HTML_TEMPLATE.format(
            title=title,
            styles=styles,
            content=content,
            width=self.width,
            height=self.height,
            mermaid_theme=self.mermaid_theme,
        )

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
