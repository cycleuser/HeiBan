"""HeiBan v2 主转换器 - 将 Markdown 转换为 reveal.js HTML 幻灯片"""

import base64
import re
from pathlib import Path
from typing import Optional

from heiban.v2.md_parser import MarkdownSlideParser, Slide


def _get_lib_path() -> Path:
    """获取包内 lib 文件夹路径"""
    try:
        from importlib.resources import files

        return files("heiban.data").joinpath("lib")
    except Exception:
        return Path(__file__).parent.parent / "data" / "lib"


def _load_lib_files() -> dict:
    """加载所有 lib 文件内容"""
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
            with open(fpath, encoding="utf-8") as f:
                libs[js_file] = f.read()
    for css_file in [
        "reveal.min.css",
        "katex.min.css",
    ]:
        fpath = lib_path / "css" / css_file
        if fpath.exists():
            with open(fpath, encoding="utf-8") as f:
                libs[css_file] = f.read()
    return libs


_LIBS = _load_lib_files()

REVEAL_THEMES = {
    "black": "black",
    "white": "white",
    "league": "league",
    "beige": "beige",
    "sky": "sky",
    "night": "night",
    "serif": "serif",
    "simple": "simple",
    "solarized": "solarized",
    "blood": "blood",
    "moon": "moon",
}

REVEAL_TRANSITIONS = {
    "none": "none",
    "fade": "fade",
    "slide": "slide",
    "convex": "convex",
    "concave": "concave",
    "zoom": "zoom",
}


class MarkdownToSlideConverterV2:
    """v2 版本 Markdown 转 reveal.js 幻灯片转换器

    特性:
    - 基于 markdown-it-py 的完整 GFM 支持
    - 垂直幻灯片 (----)
    - 幻灯片属性 (背景、转场等)
    - Fragment 动画
    - 演讲者备注
    - 脚注、标记、上下标
    - 任务列表
    - Mermaid 图表 (客户端渲染 + mmdc 预渲染)
    - KaTeX 数学公式
    - 代码高亮
    - 图片嵌入 (base64)
    - 矢量完美 PDF 导出支持
    """

    ASPECT_RATIOS = {
        "16:9": (1920, 1080),
        "4:3": (1024, 768),
        "21:9": (2560, 1080),
        "3:2": (1440, 960),
    }

    def __init__(self):
        self.parser = MarkdownSlideParser()
        self.aspect_ratio = "16:9"
        self.width, self.height = self.ASPECT_RATIOS[self.aspect_ratio]
        self.font_size = 28
        self.theme = "black"
        self.transition = "slide"
        self.transition_speed = "default"
        self.mermaid_theme = "default"
        self.code_theme = "dark"
        self.slide_number = "c/t"
        self.show_progress = True
        self.show_controls = True
        self.hash = True
        self.center = True
        self.embed_images = True
        self.image_base_path: Optional[Path] = None

    def set_aspect_ratio(self, ratio: str):
        """设置宽高比"""
        if ratio in self.ASPECT_RATIOS:
            self.aspect_ratio = ratio
            self.width, self.height = self.ASPECT_RATIOS[ratio]

    def _embed_image(self, img_match: re.Match) -> str:
        """将图片转换为 base64 嵌入"""
        src = img_match.group(1)
        alt = img_match.group(2) if img_match.lastindex >= 2 else ""
        title = img_match.group(3) if img_match.lastindex >= 3 else ""

        if src.startswith(("data:", "http://", "https://")):
            return img_match.group(0)

        img_path = Path(src)
        if not img_path.is_absolute() and self.image_base_path:
            img_path = self.image_base_path / img_path

        if img_path.exists():
            try:
                with open(img_path, "rb") as f:
                    data = base64.b64encode(f.read()).decode()
                ext = img_path.suffix.lower().lstrip(".")
                mime_map = {
                    "png": "image/png",
                    "jpg": "image/jpeg",
                    "jpeg": "image/jpeg",
                    "gif": "image/gif",
                    "svg": "image/svg+xml",
                    "webp": "image/webp",
                }
                mime = mime_map.get(ext, "image/png")
                title_attr = f' title="{title}"' if title else ""
                alt_attr = f' alt="{alt}"' if alt else ""
                return f'<img src="data:{mime};base64,{data}"{alt_attr}{title_attr}>'
            except Exception:
                pass

        return img_match.group(0)

    def _process_slide_content(self, slide: Slide) -> str:
        """处理单个幻灯片内容，嵌入图片并添加结构"""
        content = slide.content

        if self.embed_images:
            content = re.sub(
                r'<img\s+src="([^"]+)"(?:\s+alt="([^"]*)")?(?:\s+title="([^"]*)")?\s*/?>',
                self._embed_image,
                content,
            )

        return content

    def _build_section_tag(self, slide: Slide, is_nested: bool = False) -> str:
        """构建 reveal.js <section> 标签"""
        content = self._process_slide_content(slide)
        attrs = slide.attributes.to_data_attrs() if slide.attributes else {}

        attr_str = ""
        for key, value in attrs.items():
            if value:
                attr_str += f' {key}="{value}"'
            else:
                attr_str += f" {key}"

        section_parts = [f"            <section{attr_str}>"]

        if content:
            if self.center:
                section_parts.append('                <div class="center-content">')
                section_parts.append(f"                    {content}")
                section_parts.append("                </div>")
            else:
                section_parts.append(f"                {content}")

        if slide.notes:
            section_parts.append(f'                <aside class="notes">{slide.notes}</aside>')

        section_parts.append("            </section>")
        return "\n".join(section_parts)

    def _build_slides_html(self, slides: list[Slide]) -> str:
        """构建所有幻灯片的 HTML 结构，支持垂直嵌套"""
        result = []
        i = 0

        while i < len(slides):
            slide = slides[i]

            if slide.is_vertical:
                nested_sections = [self._build_section_tag(slide)]
                i += 1
                while i < len(slides) and slides[i].is_vertical:
                    nested_sections.append(self._build_section_tag(slides[i]))
                    i += 1

                outer_section = "            <section>\n"
                outer_section += "\n".join(nested_sections)
                outer_section += "\n            </section>"
                result.append(outer_section)
            else:
                result.append(self._build_section_tag(slide))
                i += 1

        return "\n".join(result)

    def convert(self, md_content: str, title: str = "演示文稿", use_cdn: bool = False) -> str:
        """将 Markdown 内容转换为完整的 reveal.js HTML"""
        slides = self.parser.parse(md_content)
        slides_html = self._build_slides_html(slides)

        if use_cdn:
            return self._generate_cdn_html(slides_html, title)
        else:
            return self._generate_embedded_html(slides_html, title)

    def _get_base_styles(self) -> str:
        """生成基础样式"""
        return f"""
/* v2 Custom Styles */
.reveal {{
    font-size: {self.font_size}px;
}}

.reveal .center-content {{
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    min-height: 100%;
}}

.reveal h1 {{
    font-size: 2.2em;
    margin-bottom: 0.4em;
}}

.reveal h2 {{
    font-size: 1.7em;
    margin-bottom: 0.4em;
}}

.reveal h3 {{
    font-size: 1.3em;
    margin-bottom: 0.3em;
}}

.reveal h4 {{
    font-size: 1.1em;
}}

.reveal ul, .reveal ol {{
    display: block;
    text-align: left;
    margin-left: 1.5em;
}}

.reveal li {{
    margin: 0.3em 0;
}}

.reveal li > ul, .reveal li > ol {{
    margin-left: 1em;
    font-size: 0.85em;
}}

.reveal code {{
    padding: 0.15em 0.4em;
    border-radius: 4px;
    font-size: 0.85em;
    font-weight: 500;
}}

.reveal pre {{
    width: 100%;
    font-size: 0.6em;
    margin: 0.5em 0;
    border-radius: 8px;
    overflow: auto;
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    text-align: left;
}}

.reveal pre code {{
    padding: 1em;
    max-height: 600px;
    line-height: 1.5;
    display: block;
    background: transparent;
}}

.reveal table {{
    width: 100%;
    border-collapse: collapse;
    font-size: 0.75em;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}}

.reveal table th {{
    padding: 0.6em 0.8em;
    font-weight: 600;
    border: 1px solid currentColor;
}}

.reveal table td {{
    padding: 0.5em 0.7em;
    border: 1px solid currentColor;
}}

.reveal blockquote {{
    padding: 0.5em 1em;
    margin: 0.5em 0;
    border-left: 4px solid currentColor;
    opacity: 0.85;
    font-style: italic;
}}

.reveal img {{
    max-width: 100%;
    height: auto;
    margin: 0.5em auto;
}}

.reveal .footnotes {{
    font-size: 0.6em;
    margin-top: 1em;
    opacity: 0.7;
}}

.reveal .task-list-item {{
    list-style-type: none;
    margin-left: -1.5em;
}}

.reveal .task-list-item input {{
    margin-right: 0.5em;
}}

.reveal mark {{
    padding: 0.1em 0.3em;
    border-radius: 2px;
}}

.reveal .mermaid-svg {{
    display: flex;
    justify-content: center;
    margin: 0.5em 0;
}}

.reveal .mermaid-svg svg {{
    max-width: 100%;
    height: auto;
}}

.reveal .columns {{
    display: flex;
    gap: 2em;
    align-items: flex-start;
}}

.reveal .columns > div {{
    flex: 1;
}}

.reveal section {{
    padding: 1em;
}}

.reveal p {{
    margin: 0.5em 0;
}}

.reveal a {{
    text-decoration: underline;
    text-underline-offset: 3px;
}}

.reveal del {{
    opacity: 0.6;
}}

.reveal sup, .reveal sub {{
    font-size: 0.7em;
}}
"""

    def _get_theme_colors(self) -> dict:
        """获取主题颜色配置"""
        if self.theme == "black" or self.theme == "night":
            return {
                "bg": "#000000",
                "text": "#f0f0f0",
                "heading": "#4da6ff",
                "link": "#4da6ff",
                "link_hover": "#6db8ff",
                "code_bg": "#2d2d2d",
                "code_text": "#ffcc66",
                "pre_bg": "#1a1a1a",
                "table_border": "#333333",
                "table_bg": "#1a1a1a",
                "table_even": "#0d0d0d",
                "table_th_bg": "#1a1a1a",
                "table_th_text": "#ffffff",
                "blockquote_border": "#4da6ff",
                "mark_bg": "#555500",
                "mark_text": "#ffffff",
                "is_dark": True,
            }
        elif self.theme == "white" or self.theme == "simple":
            return {
                "bg": "#ffffff",
                "text": "#24292e",
                "heading": "#005cc5",
                "link": "#005cc5",
                "link_hover": "#003d80",
                "code_bg": "#e6f3ff",
                "code_text": "#d73a49",
                "pre_bg": "#f6f8fa",
                "table_border": "#d1d9e0",
                "table_bg": "#ffffff",
                "table_even": "#f6f8fa",
                "table_th_bg": "#005cc5",
                "table_th_text": "#ffffff",
                "blockquote_border": "#005cc5",
                "mark_bg": "#fff3cd",
                "mark_text": "#24292e",
                "is_dark": False,
            }
        elif self.theme == "beige":
            return {
                "bg": "#f7f3de",
                "text": "#333333",
                "heading": "#333333",
                "link": "#8b743d",
                "link_hover": "#a0884d",
                "code_bg": "#e8e0c8",
                "code_text": "#8b4513",
                "pre_bg": "#ede6ce",
                "table_border": "#c8b896",
                "table_bg": "#f7f3de",
                "table_even": "#ede6ce",
                "table_th_bg": "#8b743d",
                "table_th_text": "#ffffff",
                "blockquote_border": "#8b743d",
                "mark_bg": "#fff3cd",
                "mark_text": "#333333",
                "is_dark": False,
            }
        elif self.theme == "sky":
            return {
                "bg": "#f7fbfc",
                "text": "#333333",
                "heading": "#333333",
                "link": "#3b759e",
                "link_hover": "#4a8bb8",
                "code_bg": "#e0f0f8",
                "code_text": "#c7254e",
                "pre_bg": "#e8f4fa",
                "table_border": "#c8dce8",
                "table_bg": "#f7fbfc",
                "table_even": "#e8f4fa",
                "table_th_bg": "#3b759e",
                "table_th_text": "#ffffff",
                "blockquote_border": "#3b759e",
                "mark_bg": "#fff3cd",
                "mark_text": "#333333",
                "is_dark": False,
            }
        elif self.theme == "league":
            return {
                "bg": "#2b2b2b",
                "text": "#eeeeee",
                "heading": "#eeeeee",
                "link": "#13daec",
                "link_hover": "#28e4f2",
                "code_bg": "#3d3d3d",
                "code_text": "#ffcc66",
                "pre_bg": "#333333",
                "table_border": "#555555",
                "table_bg": "#2b2b2b",
                "table_even": "#222222",
                "table_th_bg": "#13daec",
                "table_th_text": "#2b2b2b",
                "blockquote_border": "#13daec",
                "mark_bg": "#555500",
                "mark_text": "#eeeeee",
                "is_dark": True,
            }
        elif self.theme == "serif":
            return {
                "bg": "#f1efea",
                "text": "#000000",
                "heading": "#333333",
                "link": "#51483d",
                "link_hover": "#6b5f50",
                "code_bg": "#e8e4d8",
                "code_text": "#8b4513",
                "pre_bg": "#eae6da",
                "table_border": "#c8c0b0",
                "table_bg": "#f1efea",
                "table_even": "#eae6da",
                "table_th_bg": "#51483d",
                "table_th_text": "#ffffff",
                "blockquote_border": "#51483d",
                "mark_bg": "#fff3cd",
                "mark_text": "#000000",
                "is_dark": False,
            }
        elif self.theme == "solarized":
            return {
                "bg": "#fdf6e3",
                "text": "#657b83",
                "heading": "#586e75",
                "link": "#268bd2",
                "link_hover": "#3a9bd9",
                "code_bg": "#eee8d5",
                "code_text": "#dc322f",
                "pre_bg": "#fdf6e3",
                "table_border": "#d3cbb8",
                "table_bg": "#fdf6e3",
                "table_even": "#eee8d5",
                "table_th_bg": "#268bd2",
                "table_th_text": "#fdf6e3",
                "blockquote_border": "#268bd2",
                "mark_bg": "#fff3cd",
                "mark_text": "#657b83",
                "is_dark": False,
            }
        elif self.theme == "blood":
            return {
                "bg": "#222222",
                "text": "#eeeeee",
                "heading": "#ffffff",
                "link": "#f44336",
                "link_hover": "#ff5252",
                "code_bg": "#333333",
                "code_text": "#ffcc66",
                "pre_bg": "#2a2a2a",
                "table_border": "#555555",
                "table_bg": "#222222",
                "table_even": "#1a1a1a",
                "table_th_bg": "#f44336",
                "table_th_text": "#ffffff",
                "blockquote_border": "#f44336",
                "mark_bg": "#555500",
                "mark_text": "#eeeeee",
                "is_dark": True,
            }
        elif self.theme == "moon":
            return {
                "bg": "#002b36",
                "text": "#93a1a1",
                "heading": "#eee8d5",
                "link": "#268bd2",
                "link_hover": "#3a9bd9",
                "code_bg": "#073642",
                "code_text": "#cb4b16",
                "pre_bg": "#073642",
                "table_border": "#586e75",
                "table_bg": "#002b36",
                "table_even": "#073642",
                "table_th_bg": "#268bd2",
                "table_th_text": "#eee8d5",
                "blockquote_border": "#268bd2",
                "mark_bg": "#555500",
                "mark_text": "#93a1a1",
                "is_dark": True,
            }
        else:
            return {
                "bg": "#000000",
                "text": "#f0f0f0",
                "heading": "#4da6ff",
                "link": "#4da6ff",
                "link_hover": "#6db8ff",
                "code_bg": "#2d2d2d",
                "code_text": "#ffcc66",
                "pre_bg": "#1a1a1a",
                "table_border": "#333333",
                "table_bg": "#1a1a1a",
                "table_even": "#0d0d0d",
                "table_th_bg": "#1a1a1a",
                "table_th_text": "#ffffff",
                "blockquote_border": "#4da6ff",
                "mark_bg": "#555500",
                "mark_text": "#ffffff",
                "is_dark": True,
            }

    def _generate_embedded_html(self, slides_html: str, title: str) -> str:
        """生成嵌入所有资源的 HTML"""
        colors = self._get_theme_colors()
        mermaid_theme = "dark" if colors["is_dark"] else "default"

        reveal_css = _LIBS.get("reveal.min.css", "")
        reveal_js = _LIBS.get("reveal.min.js", "")
        mermaid_js = _LIBS.get("mermaid.min.js", "")
        highlight_js = _LIBS.get("highlight.min.js", "")
        katex_css = _LIBS.get("katex.min.css", "")
        katex_js = _LIBS.get("katex.min.js", "")
        auto_render_js = _LIBS.get("auto-render.min.js", "")

        custom_css = self._get_base_styles()

        theme_css = f"""
/* Theme Colors */
.reveal-viewport {{
    background: {colors["bg"]} !important;
    color: {colors["text"]} !important;
}}
.reveal {{
    background: {colors["bg"]} !important;
    color: {colors["text"]} !important;
}}
.reveal h1, .reveal h2, .reveal h3, .reveal h4, .reveal h5, .reveal h6 {{
    color: {colors["heading"]} !important;
}}
.reveal a {{
    color: {colors["link"]};
}}
.reveal a:hover {{
    color: {colors["link_hover"]};
}}
.reveal code {{
    background: {colors["code_bg"]};
    color: {colors["code_text"]};
}}
.reveal pre {{
    background: {colors["pre_bg"]};
}}
.reveal table {{
    background: {colors["table_bg"]};
}}
.reveal table th {{
    background: {colors["table_th_bg"]};
    color: {colors["table_th_text"]};
    border-color: {colors["table_border"]};
}}
.reveal table td {{
    border-color: {colors["table_border"]};
}}
.reveal table tr:nth-child(even) {{
    background: {colors["table_even"]};
}}
.reveal blockquote {{
    border-left-color: {colors["blockquote_border"]};
}}
.reveal mark {{
    background: {colors["mark_bg"]};
    color: {colors["mark_text"]};
}}
"""

        html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
{reveal_css}
{theme_css}
{custom_css}
{katex_css}
    </style>
</head>
<body>
    <div class="reveal">
        <div class="slides">
{slides_html}
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
            hash: {str(self.hash).lower()},
            slideNumber: '{self.slide_number}',
            progress: {str(self.show_progress).lower()},
            controls: {str(self.show_controls).lower()},
            width: {self.width},
            height: {self.height},
            margin: 0.06,
            transition: '{self.transition}',
            transitionSpeed: '{self.transition_speed}',
            center: {str(self.center).lower()},
        }});
        mermaid.initialize({{
            startOnLoad: true,
            theme: '{mermaid_theme}',
            securityLevel: 'loose',
        }});
        hljs.highlightAll();
        renderMathInElement(document.body, {{
            delimiters: [
                {{left: '$$', right: '$$', display: true}},
                {{left: '$', right: '$', display: false}},
                {{left: '\\\\[', right: '\\\\]', display: true}},
                {{left: '\\\\(', right: '\\\\)', display: false}}
            ],
            throwOnError: false
        }});
    </script>
</body>
</html>"""
        return html

    def _generate_cdn_html(self, slides_html: str, title: str) -> str:
        """生成使用 CDN 链接的 HTML"""
        colors = self._get_theme_colors()
        mermaid_theme = "dark" if colors["is_dark"] else "default"

        theme_css = f"""
/* Theme Colors */
.reveal-viewport {{
    background: {colors["bg"]} !important;
    color: {colors["text"]} !important;
}}
.reveal {{
    background: {colors["bg"]} !important;
    color: {colors["text"]} !important;
}}
.reveal h1, .reveal h2, .reveal h3, .reveal h4, .reveal h5, .reveal h6 {{
    color: {colors["heading"]} !important;
}}
.reveal a {{
    color: {colors["link"]};
}}
.reveal a:hover {{
    color: {colors["link_hover"]};
}}
.reveal code {{
    background: {colors["code_bg"]};
    color: {colors["code_text"]};
}}
.reveal pre {{
    background: {colors["pre_bg"]};
}}
.reveal table {{
    background: {colors["table_bg"]};
}}
.reveal table th {{
    background: {colors["table_th_bg"]};
    color: {colors["table_th_text"]};
    border-color: {colors["table_border"]};
}}
.reveal table td {{
    border-color: {colors["table_border"]};
}}
.reveal table tr:nth-child(even) {{
    background: {colors["table_even"]};
}}
.reveal blockquote {{
    border-left-color: {colors["blockquote_border"]};
}}
.reveal mark {{
    background: {colors["mark_bg"]};
    color: {colors["mark_text"]};
}}
"""

        custom_css = self._get_base_styles()

        html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/reveal.js@4.6.1/dist/reveal.min.css">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.css">
    <style>
{theme_css}
{custom_css}
    </style>
</head>
<body>
    <div class="reveal">
        <div class="slides">
{slides_html}
        </div>
    </div>
    <script src="https://cdn.jsdelivr.net/npm/reveal.js@4.6.1/dist/reveal.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/highlight.js@11.9.0/highlight.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/contrib/auto-render.min.js"></script>
    <script>
        Reveal.initialize({{
            hash: {str(self.hash).lower()},
            slideNumber: '{self.slide_number}',
            progress: {str(self.show_progress).lower()},
            controls: {str(self.show_controls).lower()},
            width: {self.width},
            height: {self.height},
            margin: 0.06,
            transition: '{self.transition}',
            transitionSpeed: '{self.transition_speed}',
            center: {str(self.center).lower()},
        }});
        mermaid.initialize({{
            startOnLoad: true,
            theme: '{mermaid_theme}',
            securityLevel: 'loose',
        }});
        hljs.highlightAll();
        renderMathInElement(document.body, {{
            delimiters: [
                {{left: '$$', right: '$$', display: true}},
                {{left: '$', right: '$', display: false}},
                {{left: '\\\\[', right: '\\\\]', display: true}},
                {{left: '\\\\(', right: '\\\\)', display: false}}
            ],
            throwOnError: false
        }});
    </script>
</body>
</html>"""
        return html

    def convert_file(
        self, input_path: str, output_path: str | None = None, use_cdn: bool = False
    ) -> str:
        """转换文件"""
        input_p = Path(input_path)
        with open(input_p, encoding="utf-8") as f:
            md_content = f.read()

        if output_path is None:
            output_path = str(input_p.with_suffix(".html"))

        self.image_base_path = input_p.parent
        html = self.convert(md_content, title=input_p.stem, use_cdn=use_cdn)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html)

        return output_path
