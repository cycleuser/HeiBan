#!/usr/bin/env python3
"""
Reveal.js 幻灯片双向转换工具
支持 HTML <-> Markdown 完美互转，严格保持当前 Reveal.js 结构。
"""

import os
import sys
import re
import html
import subprocess
import argparse
from pathlib import Path

# 自动安装依赖
try:
    from bs4 import BeautifulSoup, NavigableString, Tag
    import markdown
except ImportError:
    print("📦 正在安装必要依赖: beautifulsoup4, markdown...")
    subprocess.check_call(
        [sys.executable, "-m", "pip", "install", "beautifulsoup4", "markdown", "-q"]
    )
    from bs4 import BeautifulSoup, NavigableString, Tag
    import markdown


class HTMLToMarkdown:
    """将 Reveal.js HTML 转换为 Markdown"""

    def __init__(self):
        self.md_lines = []

    def convert(self, html_content):
        soup = BeautifulSoup(html_content, "html.parser")
        slides_container = soup.find("div", class_="slides")
        if not slides_container:
            raise ValueError("未找到 <div class='slides'> 容器")

        self.md_lines = []
        self._process_sections(slides_container, is_root=True)
        return "\n".join(self.md_lines).strip()

    def _process_sections(self, container, is_root=False):
        sections = [
            c for c in container.children if isinstance(c, Tag) and c.name == "section"
        ]
        if not sections:
            return

        # 检查是否为纵向幻灯片（嵌套 section）
        has_nested = any(s.find("section") for s in sections)

        for i, section in enumerate(sections):
            if i > 0:
                if is_root and not has_nested:
                    self.md_lines.append("\n---\n")
                elif is_root and has_nested:
                    self.md_lines.append("\n----\n")
                else:
                    self.md_lines.append("\n----\n")

            if section.find("section"):
                self._process_sections(section)
            else:
                self._convert_element(section)

    def _convert_element(self, tag):
        if not tag or not isinstance(tag, Tag):
            return

        name = tag.name
        if name == "h1":
            self.md_lines.append(f"# {self._get_text(tag)}\n")
        elif name == "h2":
            self.md_lines.append(f"## {self._get_text(tag)}\n")
        elif name == "h3":
            self.md_lines.append(f"### {self._get_text(tag)}\n")
        elif name == "p":
            text = self._process_children(tag).strip()
            if text:
                self.md_lines.append(f"{text}\n")
        elif name in ["ul", "ol"]:
            self._convert_list(tag)
        elif name == "pre":
            self._convert_code(tag)
        elif name == "table":
            self._convert_table(tag)
        elif name == "img":
            src = tag.get("src", "")
            alt = tag.get("alt", "")
            self.md_lines.append(f"![{alt}]({src})\n")
        elif name == "svg":
            # 保留内联 SVG 为原始 HTML
            self.md_lines.append(f"\n{str(tag)}\n")
        elif name in ["strong", "b"]:
            self.md_lines.append(f"**{self._get_text(tag)}**")
        elif name in ["em", "i"]:
            self.md_lines.append(f"*{self._get_text(tag)}*")
        elif name == "br":
            self.md_lines.append("  \n")
        elif name == "div":
            # 处理 columns 等布局
            classes = tag.get("class", [])
            if "columns" in classes:
                self.md_lines.append("\n<div class='columns'>\n")
                for child in tag.children:
                    if isinstance(child, Tag) and child.name == "div":
                        self.md_lines.append("<div>\n")
                        self._convert_element(child)
                        self.md_lines.append("</div>\n")
                self.md_lines.append("</div>\n")
            else:
                self._process_children(tag)
        else:
            self._process_children(tag)

    def _process_children(self, tag):
        result = []
        for child in tag.children:
            if isinstance(child, NavigableString):
                result.append(str(child))
            elif isinstance(child, Tag):
                if child.name in ["strong", "b"]:
                    result.append(f"**{self._get_text(child)}**")
                elif child.name in ["em", "i"]:
                    result.append(f"*{self._get_text(child)}*")
                elif child.name == "br":
                    result.append("  \n")
                elif child.name == "a":
                    href = child.get("href", "")
                    result.append(f"[{self._get_text(child)}]({href})")
                else:
                    result.append(self._get_text(child))
        return "".join(result)

    def _get_text(self, tag):
        # 获取纯文本，保留内部格式标记
        text = []
        for child in tag.children:
            if isinstance(child, NavigableString):
                text.append(str(child))
            elif isinstance(child, Tag):
                if child.name in ["strong", "b"]:
                    text.append(f"**{child.get_text()}**")
                elif child.name in ["em", "i"]:
                    text.append(f"*{child.get_text()}*")
                else:
                    text.append(child.get_text())
        return "".join(text).strip()

    def _convert_list(self, tag):
        is_ordered = tag.name == "ol"
        for i, li in enumerate(tag.find_all("li", recursive=False)):
            prefix = f"{i + 1}. " if is_ordered else "- "
            text = self._get_text(li).strip()
            self.md_lines.append(f"{prefix}{text}\n")
            # 处理嵌套列表
            nested = li.find(["ul", "ol"], recursive=False)
            if nested:
                self._convert_list(nested)

    def _convert_code(self, tag):
        code_tag = tag.find("code")
        if code_tag:
            classes = code_tag.get("class", [])
            lang = "text"
            for c in classes:
                if c.startswith("language-"):
                    lang = c.replace("language-", "")
                    break
            code_text = code_tag.get_text()
            self.md_lines.append(f"```{lang}\n{code_text}\n```\n")
        else:
            self.md_lines.append(f"```\n{tag.get_text()}\n```\n")

    def _convert_table(self, tag):
        rows = tag.find_all("tr")
        if not rows:
            return
        md_table = []
        headers = []
        for th in rows[0].find_all(["th", "td"]):
            headers.append(self._get_text(th).strip())
        md_table.append("| " + " | ".join(headers) + " |")
        md_table.append("| " + " | ".join(["---"] * len(headers)) + " |")

        for row in rows[1:]:
            cells = [self._get_text(td).strip() for td in row.find_all("td")]
            if len(cells) < len(headers):
                cells.extend([""] * (len(headers) - len(cells)))
            md_table.append("| " + " | ".join(cells) + " |")
        self.md_lines.append("\n" + "\n".join(md_table) + "\n")


class MarkdownToHTML:
    """将 Markdown 转换为 Reveal.js HTML"""

    def __init__(self, template_html_path=None):
        self.template = None
        if template_html_path and os.path.exists(template_html_path):
            self._load_template(template_html_path)
        else:
            self._load_default_template()

    def _load_template(self, path):
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        soup = BeautifulSoup(content, "html.parser")
        slides = soup.find("div", class_="slides")
        if slides:
            slides.clear()
        self.template = str(soup)
        self.full_html = content
        self.slides_placeholder = '<div class="slides">\n        </div>'

    def _load_default_template(self):
        # 极简 Reveal.js 模板，实际使用时建议从现有 HTML 提取
        self.full_html = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>演示文稿</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/reveal.js@4.5.0/dist/reveal.css">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/reveal.js@4.5.0/dist/theme/white.css">
</head>
<body>
    <div class="reveal">
        <div class="slides">
        </div>
    </div>
    <script src="https://cdn.jsdelivr.net/npm/reveal.js@4.5.0/dist/reveal.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/reveal.js@4.5.0/plugin/markdown/markdown.js"></script>
    <script>Reveal.initialize({ hash: true, plugins: [ RevealMarkdown ] });</script>
</body>
</html>"""
        self.template = self.full_html

    def convert(self, md_content, output_path):
        # 分割幻灯片
        # Reveal.js 使用 --- 分隔横向，---- 分隔纵向
        slides = self._split_slides(md_content)

        html_slides = []
        for slide in slides:
            if slide["type"] == "h":
                html_slides.append(
                    f"<section>\n{self._md_to_html(slide['content'])}\n</section>"
                )
            elif slide["type"] == "v":
                html_slides.append(
                    f"<section>\n{self._md_to_html(slide['content'])}\n</section>"
                )

        # 处理纵向嵌套逻辑
        final_html = self._build_vertical_stack(html_slides)

        # 替换模板中的 slides 内容
        soup = BeautifulSoup(self.full_html, "html.parser")
        slides_div = soup.find("div", class_="slides")
        if slides_div:
            slides_div.clear()
            slides_div.append(BeautifulSoup(final_html, "html.parser"))

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(str(soup))
        print(f"✅ 已生成: {output_path}")

    def _split_slides(self, md_content):
        slides = []
        # 先按纵向分割，再按横向分割
        # 简化逻辑：按行扫描 --- 和 ----
        lines = md_content.split("\n")
        current_slide = []
        current_type = "h"

        def flush_slide():
            if current_slide:
                slides.append(
                    {"type": current_type, "content": "\n".join(current_slide).strip()}
                )

        for line in lines:
            if re.match(r"^----+\s*$", line):
                flush_slide()
                current_slide = []
                current_type = "v"
            elif re.match(r"^---+\s*$", line):
                flush_slide()
                current_slide = []
                current_type = "h"
            else:
                current_slide.append(line)
        flush_slide()
        return slides

    def _md_to_html(self, md_text):
        # 使用 markdown 库转换
        exts = ["tables", "fenced_code", "attr_list", "md_in_html"]
        return markdown.markdown(md_text, extensions=exts)

    def _build_vertical_stack(self, slides):
        if not slides:
            return ""

        result = []
        i = 0
        while i < len(slides):
            if slides[i]["type"] == "h":
                result.append(
                    slides[i]["html"]
                    if "html" in slides[i]
                    else f"<section>\n{self._md_to_html(slides[i]['content'])}\n</section>"
                )
                i += 1
            else:
                # 纵向组
                result.append("<section>")
                while i < len(slides) and slides[i]["type"] == "v":
                    result.append(self._md_to_html(slides[i]["content"]))
                    i += 1
                result.append("</section>")
        return "\n".join(result)


def main():
    parser = argparse.ArgumentParser(description="Reveal.js 幻灯片双向转换工具")
    parser.add_argument(
        "mode",
        nargs="?",
        choices=["html2md", "md2html", "auto"],
        default="auto",
        help="转换模式",
    )
    parser.add_argument("file", help="输入文件路径")
    parser.add_argument("-o", "--output", help="输出文件路径（默认同名不同后缀）")
    parser.add_argument("-t", "--template", help="转换 MD->HTML 时使用的 HTML 模板路径")

    args = parser.parse_args()

    input_path = Path(args.file)
    if not input_path.exists():
        print(f"❌ 文件不存在: {input_path}")
        sys.exit(1)

    ext = input_path.suffix.lower()
    mode = args.mode
    if mode == "auto":
        mode = "html2md" if ext == ".html" else "md2html"

    if mode == "html2md":
        if ext != ".html":
            print("❌ 请输入 HTML 文件进行 html2md 转换")
            sys.exit(1)
        output_path = (
            Path(args.output) if args.output else input_path.with_suffix(".md")
        )

        print(f"🔄 正在转换: {input_path} -> {output_path}")
        with open(input_path, "r", encoding="utf-8") as f:
            html_content = f.read()

        converter = HTMLToMarkdown()
        md_content = converter.convert(html_content)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(md_content)
        print(f"✅ 转换成功: {output_path}")

    elif mode == "md2html":
        if ext not in [".md", ".markdown"]:
            print("❌ 请输入 Markdown 文件进行 md2html 转换")
            sys.exit(1)
        output_path = (
            Path(args.output) if args.output else input_path.with_suffix(".html")
        )

        print(f"🔄 正在转换: {input_path} -> {output_path}")
        with open(input_path, "r", encoding="utf-8") as f:
            md_content = f.read()

        template_path = (
            args.template if args.template else input_path.with_suffix(".html")
        )
        converter = MarkdownToHTML(
            template_path if Path(template_path).exists() else None
        )
        converter.convert(md_content, output_path)


if __name__ == "__main__":
    main()
