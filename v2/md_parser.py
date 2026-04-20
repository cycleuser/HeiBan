"""基于 markdown-it-py 的 Markdown 解析器，支持 GFM 和 reveal.js 扩展语法"""

import re
from dataclasses import dataclass, field
from typing import List, Optional

from markdown_it import MarkdownIt
from mdit_py_plugins.attrs import attrs_plugin
from mdit_py_plugins.footnote import footnote_plugin
from mdit_py_plugins.front_matter import front_matter_plugin
from mdit_py_plugins.subscript import sub_plugin
from mdit_py_plugins.tasklists import tasklists_plugin


@dataclass
class SlideAttributes:
    """单个幻灯片的 reveal.js 属性"""

    background_color: Optional[str] = None
    background_image: Optional[str] = None
    background_size: Optional[str] = None
    background_position: Optional[str] = None
    background_repeat: Optional[str] = None
    background_opacity: Optional[float] = None
    background_video: Optional[str] = None
    background_video_loop: Optional[bool] = None
    background_video_muted: Optional[bool] = None
    transition: Optional[str] = None
    transition_speed: Optional[str] = None
    background_transition: Optional[str] = None
    auto_animate: bool = False
    auto_animate_duration: Optional[float] = None
    auto_animate_easing: Optional[str] = None
    id: Optional[str] = None
    state: Optional[str] = None
    extra_attrs: dict = field(default_factory=dict)

    def to_data_attrs(self) -> dict:
        """转换为 reveal.js data-* 属性字典"""
        attrs = {}
        if self.background_color:
            attrs["data-background-color"] = self.background_color
        if self.background_image:
            attrs["data-background-image"] = self.background_image
        if self.background_size:
            attrs["data-background-size"] = self.background_size
        if self.background_position:
            attrs["data-background-position"] = self.background_position
        if self.background_repeat:
            attrs["data-background-repeat"] = self.background_repeat
        if self.background_opacity is not None:
            attrs["data-background-opacity"] = str(self.background_opacity)
        if self.background_video:
            attrs["data-background-video"] = self.background_video
        if self.background_video_loop is not None:
            attrs["data-background-video-loop"] = "true" if self.background_video_loop else "false"
        if self.background_video_muted is not None:
            attrs["data-background-video-muted"] = (
                "true" if self.background_video_muted else "false"
            )
        if self.transition:
            attrs["data-transition"] = self.transition
        if self.transition_speed:
            attrs["data-transition-speed"] = self.transition_speed
        if self.background_transition:
            attrs["data-background-transition"] = self.background_transition
        if self.auto_animate:
            attrs["data-auto-animate"] = ""
        if self.auto_animate_duration is not None:
            attrs["data-auto-animate-duration"] = str(self.auto_animate_duration)
        if self.auto_animate_easing:
            attrs["data-auto-animate-easing"] = self.auto_animate_easing
        if self.id:
            attrs["id"] = self.id
        if self.state:
            attrs["data-state"] = self.state
        attrs.update(self.extra_attrs)
        return attrs


@dataclass
class Slide:
    """解析后的单个幻灯片"""

    content: str
    is_vertical: bool = False
    attributes: Optional[SlideAttributes] = None
    notes: Optional[str] = None
    fragments: List[dict] = field(default_factory=list)


def _parse_slide_comment(comment: str) -> Optional[SlideAttributes]:
    """解析 reveal.js 幻灯片属性注释
    格式: <!-- .slide: data-background="#ff0000" data-transition="zoom" -->
    """
    if not comment.startswith(".slide:"):
        return None

    attrs = SlideAttributes()
    content = comment[len(".slide:") :].strip()

    patterns = {
        "data-background-color": r'data-background-color=["\']?([^"\'>\s]+)["\']?',
        "data-background": r'(?<!-)data-background=["\']?([^"\'>\s]+)["\']?',
        "data-background-image": r'data-background-image=["\']?([^"\'>\s]+)["\']?',
        "data-background-size": r'data-background-size=["\']?([^"\'>\s]+)["\']?',
        "data-background-position": r'data-background-position=["\']?([^"\'>\s]+)["\']?',
        "data-background-repeat": r'data-background-repeat=["\']?([^"\'>\s]+)["\']?',
        "data-background-opacity": r'data-background-opacity=["\']?([\d.]+)["\']?',
        "data-background-video": r'data-background-video=["\']?([^"\'>\s]+)["\']?',
        "data-background-video-loop": r'data-background-video-loop=["\']?(true|false)["\']?',
        "data-background-video-muted": r'data-background-video-muted=["\']?(true|false)["\']?',
        "data-transition": r'data-transition=["\']?([^"\'>\s]+)["\']?',
        "data-transition-speed": r'data-transition-speed=["\']?([^"\'>\s]+)["\']?',
        "data-background-transition": r'data-background-transition=["\']?([^"\'>\s]+)["\']?',
        "data-auto-animate": r'data-auto-animate(?:=["\']?([^"\'>\s]*)["\']?)?',
        "data-auto-animate-duration": r'data-auto-animate-duration=["\']?([\d.]+)["\']?',
        "data-auto-animate-easing": r'data-auto-animate-easing=["\']?([^"\'>\s]+)["\']?',
        "id": r'id=["\']?([^"\'>\s]+)["\']?',
        "data-state": r'data-state=["\']?([^"\'>\s]+)["\']?',
    }

    for key, pattern in patterns.items():
        match = re.search(pattern, content)
        if match:
            value = match.group(1) if match.lastindex else ""
            if key == "data-background-opacity":
                attrs.background_opacity = float(value)
            elif key == "data-background-video-loop":
                attrs.background_video_loop = value == "true"
            elif key == "data-background-video-muted":
                attrs.background_video_muted = value == "true"
            elif key == "data-auto-animate":
                attrs.auto_animate = True
                if value:
                    attrs.auto_animate_duration = (
                        float(value) if value.replace(".", "").isdigit() else None
                    )
            elif key == "data-auto-animate-duration":
                attrs.auto_animate_duration = float(value)
            elif key == "data-background-color":
                attrs.background_color = value
            elif key == "data-background":
                if value.startswith(("http://", "https://", "/", "./", "../")):
                    attrs.background_image = value
                else:
                    attrs.background_color = value
            elif key == "data-background-image":
                attrs.background_image = value
            elif key == "data-background-size":
                attrs.background_size = value
            elif key == "data-background-position":
                attrs.background_position = value
            elif key == "data-background-repeat":
                attrs.background_repeat = value
            elif key == "data-background-video":
                attrs.background_video = value
            elif key == "data-transition":
                attrs.transition = value
            elif key == "data-transition-speed":
                attrs.transition_speed = value
            elif key == "data-background-transition":
                attrs.background_transition = value
            elif key == "data-auto-animate-easing":
                attrs.auto_animate_easing = value
            elif key == "id":
                attrs.id = value
            elif key == "data-state":
                attrs.state = value

    for attr_match in re.finditer(r'(data-[\w-]+)=["\']?([^"\'>\s]+)["\']?', content):
        key = attr_match.group(1)
        value = attr_match.group(2)
        if key not in patterns:
            attrs.extra_attrs[key] = value

    return attrs


def _parse_element_comment(comment: str) -> Optional[dict]:
    """解析元素 fragment 注释
    格式: <!-- .element: class="fragment fade-in" data-fragment-index="1" -->
    """
    if not comment.startswith(".element:"):
        return None

    content = comment[len(".element:") :].strip()
    result = {}

    class_match = re.search(r'class=["\']?([^"\'>\s]+(?:\s+[^"\'>\s]+)*)["\']?', content)
    if class_match:
        result["class"] = class_match.group(1)

    index_match = re.search(r'data-fragment-index=["\']?(\d+)["\']?', content)
    if index_match:
        result["data-fragment-index"] = int(index_match.group(1))

    for attr_match in re.finditer(r'(data-[\w-]+)=["\']?([^"\'>\s]+)["\']?', content):
        result[attr_match.group(1)] = attr_match.group(2)

    return result


def _parse_notes(html: str) -> tuple[str, Optional[str]]:
    """提取 speaker notes 并返回 (清理后的HTML, notes内容)"""
    notes_match = re.search(r'<aside\s+class="notes">(.*?)</aside>', html, re.DOTALL)
    notes = notes_match.group(1).strip() if notes_match else None
    if notes_match:
        html = html[: notes_match.start()] + html[notes_match.end() :]
    return html, notes


def _add_fragments_to_html(html: str, fragments: List[dict]) -> str:
    """将 fragment 属性应用到 HTML 元素"""
    if not fragments:
        return html

    fragment_idx = 0
    for _frag in fragments:
        if fragment_idx >= len(fragments):
            break

        frag_info = fragments[fragment_idx]
        if "class" in frag_info:
            classes = frag_info["class"]
            index = frag_info.get("data-fragment-index", "")

            for tag in [
                "p>",
                "ul>",
                "ol>",
                "li>",
                "h1>",
                "h2>",
                "h3>",
                "h4>",
                "h5>",
                "h6>",
                "table>",
                "pre>",
                "blockquote>",
                "img ",
                "div>",
            ]:
                tag_name = tag.rstrip(">")
                replacement = f'{tag_name} class="{classes}"'
                if index:
                    replacement += f' data-fragment-index="{index}"'
                if f"<{tag}" in html and "class=" not in html.split(f"<{tag}")[1].split(">")[0]:
                    html = html.replace(f"<{tag}", f"<{replacement}>", 1)
                    break
        fragment_idx += 1

    return html


class MarkdownSlideParser:
    """Markdown 幻灯片解析器

    支持语法:
    - `---` 水平幻灯片分隔
    - `----` 垂直幻灯片分隔
    - `<!-- .slide: data-background="#ff0000" -->` 幻灯片属性
    - `<!-- .element: class="fragment fade-in" -->` 元素 fragment
    - `<aside class="notes">演讲者备注</aside>` 演讲者备注
    - 所有 GFM 语法 (表格、任务列表、删除线等)
    - Front Matter (YAML)
    - 脚注、标记、上下标等扩展
    """

    def __init__(self):
        self.md = self._create_markdown_it()

    def _create_markdown_it(self) -> MarkdownIt:
        """创建配置好的 markdown-it 实例"""
        md = (
            MarkdownIt("gfm-like")
            .use(front_matter_plugin)
            .use(footnote_plugin)
            .use(sub_plugin)
            .use(attrs_plugin)
            .use(tasklists_plugin)
        )
        md.enable(["table"])
        return md

    def parse(self, content: str) -> List[Slide]:
        """解析 Markdown 内容为幻灯片列表"""
        content = content.strip()
        if not content:
            return []

        slides = []
        current_slide_lines = []
        current_attrs = None
        current_fragments = []
        is_in_vertical_section = False

        lines = content.split("\n")
        i = 0
        while i < len(lines):
            line = lines[i]
            stripped = line.strip()

            if stripped in ("---", "***", "___"):
                if current_slide_lines:
                    slides.append(
                        self._create_slide(
                            "\n".join(current_slide_lines),
                            is_vertical=is_in_vertical_section,
                            attributes=current_attrs,
                            fragments=current_fragments,
                        )
                    )
                    current_slide_lines = []
                    current_attrs = None
                    current_fragments = []
                is_in_vertical_section = False
                i += 1
                continue

            if stripped == "----":
                if current_slide_lines:
                    slides.append(
                        self._create_slide(
                            "\n".join(current_slide_lines),
                            is_vertical=is_in_vertical_section,
                            attributes=current_attrs,
                            fragments=current_fragments,
                        )
                    )
                    current_slide_lines = []
                    current_attrs = None
                    current_fragments = []
                is_in_vertical_section = True
                i += 1
                continue

            if stripped == "----":
                if current_slide_lines:
                    slides.append(
                        self._create_slide(
                            "\n".join(current_slide_lines),
                            is_vertical=is_in_vertical_section,
                            attributes=current_attrs,
                            fragments=current_fragments,
                        )
                    )
                    current_slide_lines = []
                    current_attrs = None
                    current_fragments = []
                is_in_vertical_section = True
                i += 1
                continue

            slide_comment = self._extract_slide_comment(stripped)
            if slide_comment:
                current_attrs = slide_comment
                i += 1
                continue

            element_comment = _parse_element_comment(stripped[4:-3].strip())
            if element_comment:
                current_fragments.append(element_comment)
                i += 1
                continue

            current_slide_lines.append(line)
            i += 1

        if current_slide_lines:
            slides.append(
                self._create_slide(
                    "\n".join(current_slide_lines),
                    is_vertical=is_in_vertical_section,
                    attributes=current_attrs,
                    fragments=current_fragments,
                )
            )

        return slides

    def _extract_slide_comment(self, line: str) -> Optional[SlideAttributes]:
        """从行中提取幻灯片属性注释"""
        comment_match = re.match(r"<!--\s*(.+?)\s*-->", line)
        if comment_match:
            return _parse_slide_comment(comment_match.group(1))
        return None

    def _create_slide(
        self,
        content: str,
        is_vertical: bool = False,
        attributes: Optional[SlideAttributes] = None,
        fragments: Optional[List[dict]] = None,
    ) -> Slide:
        """创建解析后的幻灯片对象"""
        html = self.md.render(content)
        html, notes = _parse_notes(html)

        if fragments:
            html = _add_fragments_to_html(html, fragments)

        return Slide(
            content=html.strip(),
            is_vertical=is_vertical,
            attributes=attributes,
            notes=notes,
            fragments=fragments or [],
        )

    def render_to_html(self, content: str) -> str:
        """直接将 Markdown 渲染为 HTML（不分幻灯片）"""
        return self.md.render(content)
