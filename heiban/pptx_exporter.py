"""基于 python-pptx 的 PPTX 导出器

将解析后的 Markdown 幻灯片转换为 PowerPoint (.pptx) 文件。
数学公式通过 pdflatex+PyMuPDF 渲染为高质量图片(回退到 matplotlib)，
Mermaid 通过 mmdc 渲染为 SVG/PNG，代码块带真实背景色，表格/列表/引用块完整支持。
"""

import base64
import io
import os
import re
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List, Optional

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN
from pptx.util import Inches, Pt

from heiban.v2.md_parser import Slide

THEME_COLORS: Dict[str, dict] = {
    "black": {
        "bg": RGBColor(0x00, 0x00, 0x00),
        "text": RGBColor(0xF0, 0xF0, 0xF0),
        "heading": RGBColor(0x4D, 0xA6, 0xFF),
        "code_bg": RGBColor(0x1A, 0x1A, 0x1A),
        "code_text": RGBColor(0xCC, 0xCC, 0xCC),
        "accent": RGBColor(0x4D, 0xA6, 0xFF),
        "block_bg": RGBColor(0x14, 0x14, 0x14),
    },
    "white": {
        "bg": RGBColor(0xFF, 0xFF, 0xFF),
        "text": RGBColor(0x24, 0x29, 0x2E),
        "heading": RGBColor(0x00, 0x5C, 0xC5),
        "code_bg": RGBColor(0xF6, 0xF8, 0xFA),
        "code_text": RGBColor(0x24, 0x29, 0x2E),
        "accent": RGBColor(0x00, 0x5C, 0xC5),
        "block_bg": RGBColor(0xF0, 0xF4, 0xF8),
    },
    "league": {
        "bg": RGBColor(0x2B, 0x2B, 0x2B),
        "text": RGBColor(0xEE, 0xEE, 0xEE),
        "heading": RGBColor(0x13, 0xDA, 0xEC),
        "code_bg": RGBColor(0x33, 0x33, 0x33),
        "code_text": RGBColor(0xCC, 0xCC, 0xCC),
        "accent": RGBColor(0x13, 0xDA, 0xEC),
        "block_bg": RGBColor(0x20, 0x20, 0x20),
    },
    "beige": {
        "bg": RGBColor(0xF7, 0xF3, 0xDE),
        "text": RGBColor(0x33, 0x33, 0x33),
        "heading": RGBColor(0x8B, 0x74, 0x3D),
        "code_bg": RGBColor(0xED, 0xE6, 0xCE),
        "code_text": RGBColor(0x33, 0x33, 0x33),
        "accent": RGBColor(0x8B, 0x74, 0x3D),
        "block_bg": RGBColor(0xED, 0xE6, 0xCE),
    },
    "sky": {
        "bg": RGBColor(0xF7, 0xFB, 0xFC),
        "text": RGBColor(0x33, 0x33, 0x33),
        "heading": RGBColor(0x3B, 0x75, 0x9E),
        "code_bg": RGBColor(0xE8, 0xF4, 0xFA),
        "code_text": RGBColor(0x33, 0x33, 0x33),
        "accent": RGBColor(0x3B, 0x75, 0x9E),
        "block_bg": RGBColor(0xE0, 0xEF, 0xF8),
    },
    "night": {
        "bg": RGBColor(0x00, 0x00, 0x00),
        "text": RGBColor(0xF0, 0xF0, 0xF0),
        "heading": RGBColor(0x4D, 0xA6, 0xFF),
        "code_bg": RGBColor(0x1A, 0x1A, 0x1A),
        "code_text": RGBColor(0xCC, 0xCC, 0xCC),
        "accent": RGBColor(0x4D, 0xA6, 0xFF),
        "block_bg": RGBColor(0x14, 0x14, 0x14),
    },
    "moon": {
        "bg": RGBColor(0x00, 0x2B, 0x36),
        "text": RGBColor(0x93, 0xA1, 0xA1),
        "heading": RGBColor(0xEE, 0xE8, 0xD5),
        "code_bg": RGBColor(0x07, 0x36, 0x42),
        "code_text": RGBColor(0x93, 0xA1, 0xA1),
        "accent": RGBColor(0x26, 0x8B, 0xD2),
        "block_bg": RGBColor(0x07, 0x36, 0x42),
    },
    "solarized": {
        "bg": RGBColor(0xFD, 0xF6, 0xE3),
        "text": RGBColor(0x65, 0x7B, 0x83),
        "heading": RGBColor(0x58, 0x6E, 0x75),
        "code_bg": RGBColor(0xEE, 0xE8, 0xD5),
        "code_text": RGBColor(0x65, 0x7B, 0x83),
        "accent": RGBColor(0x26, 0x8B, 0xD2),
        "block_bg": RGBColor(0xEE, 0xE8, 0xD5),
    },
    "blood": {
        "bg": RGBColor(0x22, 0x22, 0x22),
        "text": RGBColor(0xEE, 0xEE, 0xEE),
        "heading": RGBColor(0xFF, 0xFF, 0xFF),
        "code_bg": RGBColor(0x2A, 0x2A, 0x2A),
        "code_text": RGBColor(0xCC, 0xCC, 0xCC),
        "accent": RGBColor(0xF4, 0x43, 0x36),
        "block_bg": RGBColor(0x1A, 0x1A, 0x1A),
    },
    "dracula": {
        "bg": RGBColor(0x28, 0x2A, 0x36),
        "text": RGBColor(0xF8, 0xF8, 0xF2),
        "heading": RGBColor(0xBD, 0x93, 0xF9),
        "code_bg": RGBColor(0x44, 0x47, 0x5A),
        "code_text": RGBColor(0xF8, 0xF8, 0xF2),
        "accent": RGBColor(0xFF, 0x79, 0xC6),
        "block_bg": RGBColor(0x34, 0x37, 0x47),
    },
    "serif": {
        "bg": RGBColor(0xF1, 0xEF, 0xEA),
        "text": RGBColor(0x00, 0x00, 0x00),
        "heading": RGBColor(0x33, 0x33, 0x33),
        "code_bg": RGBColor(0xEA, 0xE6, 0xDA),
        "code_text": RGBColor(0x00, 0x00, 0x00),
        "accent": RGBColor(0x51, 0x48, 0x3D),
        "block_bg": RGBColor(0xEA, 0xE6, 0xDA),
    },
    "simple": {
        "bg": RGBColor(0xFF, 0xFF, 0xFF),
        "text": RGBColor(0x24, 0x29, 0x2E),
        "heading": RGBColor(0x00, 0x5C, 0xC5),
        "code_bg": RGBColor(0xF6, 0xF8, 0xFA),
        "code_text": RGBColor(0x24, 0x29, 0x2E),
        "accent": RGBColor(0x00, 0x5C, 0xC5),
        "block_bg": RGBColor(0xF0, 0xF4, 0xF8),
    },
}


GITHUB_DARK_COLORS = {
    "keyword": "#FF7B72",
    "keyword_declaration": "#FF7B72",
    "keyword_namespace": "#FF7B72",
    "keyword_type": "#FF7B72",
    "name_function": "#D2A8FF",
    "name_class": "#FFA657",
    "name_builtin": "#FFA657",
    "name_decorator": "#D2A8FF",
    "name_variable": "#FFA657",
    "name_constant": "#79C0FF",
    "name_attribute": "#7EE787",
    "string": "#A5D6FF",
    "string_doc": "#A5D6FF",
    "string_interpol": "#A5D6FF",
    "string_escape": "#A5D6FF",
    "number": "#79C0FF",
    "number_float": "#79C0FF",
    "operator": "#FF7B72",
    "operator_word": "#FF7B72",
    "comment": "#8B949E",
    "comment_single": "#8B949E",
    "comment_multiline": "#8B949E",
    "comment_special": "#8B949E",
    "punctuation": "#C9D1D9",
    "generic_deleted": "#FFA198",
    "generic_inserted": "#7EE787",
    "generic_heading": "#D2A8FF",
    "generic_subheading": "#D2A8FF",
    "default": "#C9D1D9",
}

GITHUB_LIGHT_COLORS = {
    "keyword": "#CF222E",
    "keyword_declaration": "#CF222E",
    "keyword_namespace": "#CF222E",
    "keyword_type": "#CF222E",
    "name_function": "#8250DF",
    "name_class": "#953800",
    "name_builtin": "#953800",
    "name_decorator": "#8250DF",
    "name_variable": "#953800",
    "name_constant": "#0550AE",
    "name_attribute": "#116327",
    "string": "#0A3069",
    "string_doc": "#0A3069",
    "string_interpol": "#0A3069",
    "string_escape": "#0A3069",
    "number": "#0550AE",
    "number_float": "#0550AE",
    "operator": "#CF222E",
    "operator_word": "#CF222E",
    "comment": "#6E7781",
    "comment_single": "#6E7781",
    "comment_multiline": "#6E7781",
    "comment_special": "#6E7781",
    "punctuation": "#24292F",
    "generic_deleted": "#82071E",
    "generic_inserted": "#116327",
    "generic_heading": "#8250DF",
    "generic_subheading": "#8250DF",
    "default": "#24292F",
}

DARK_THEMES = {"black", "league", "dracula", "moon", "night", "blood"}


def _token_to_color_key(tok) -> str:
    tok_str = str(tok)
    mapping = {
        "Token.Keyword.Declaration": "keyword_declaration",
        "Token.Keyword.Namespace": "keyword_namespace",
        "Token.Keyword.Type": "keyword_type",
        "Token.Keyword": "keyword",
        "Token.Name.Function": "name_function",
        "Token.Name.Class": "name_class",
        "Token.Name.Builtin": "name_builtin",
        "Token.Name.Decorator": "name_decorator",
        "Token.Name.Variable": "name_variable",
        "Token.Name.Constant": "name_constant",
        "Token.Name.Attribute": "name_attribute",
        "Token.Name": "name",
        "Token.Literal.String.Doc": "string_doc",
        "Token.Literal.String.Interpol": "string_interpol",
        "Token.Literal.String.Escape": "string_escape",
        "Token.Literal.String": "string",
        "Token.Literal.Number.Integer": "number",
        "Token.Literal.Number.Float": "number_float",
        "Token.Literal.Number": "number",
        "Token.Operator.Word": "operator_word",
        "Token.Operator": "operator",
        "Token.Comment.Single": "comment_single",
        "Token.Comment.Multiline": "comment_multiline",
        "Token.Comment.Special": "comment_special",
        "Token.Comment": "comment",
        "Token.Generic.Deleted": "generic_deleted",
        "Token.Generic.Inserted": "generic_inserted",
        "Token.Generic.Heading": "generic_heading",
        "Token.Generic.Subheading": "generic_subheading",
        "Token.Punctuation": "punctuation",
    }
    return mapping.get(tok_str, "default")


def _highlight_code(code: str, lang: str, theme: str) -> list:
    from pygments import lex
    from pygments.lexers import TextLexer, get_lexer_by_name
    from pygments.util import ClassNotFound

    color_map = GITHUB_DARK_COLORS if theme in DARK_THEMES else GITHUB_LIGHT_COLORS
    try:
        lexer = get_lexer_by_name(lang)
    except ClassNotFound:
        lexer = TextLexer()

    lines = [[]]
    for tok_type, tok_text in lex(code, lexer):
        color_key = _token_to_color_key(tok_type)
        color_hex = color_map.get(color_key, color_map["default"])
        r, g, b = _hex_to_rgb(color_hex)
        rgb = RGBColor(r, g, b)
        start = 0
        for i, ch in enumerate(tok_text):
            if ch == "\n":
                if i > start:
                    lines[-1].append((tok_text[start:i], rgb))
                lines.append([])
                start = i + 1
            elif ch == "\t":
                if i > start:
                    lines[-1].append((tok_text[start:i], rgb))
                lines[-1].append(("    ", rgb))
                start = i + 1
        if start < len(tok_text):
            lines[-1].append((tok_text[start:], rgb))
    return lines


def _hex_to_rgb(hex_color: str) -> tuple:
    h = hex_color.lstrip("#")
    if len(h) == 3:
        h = h[0] * 2 + h[1] * 2 + h[2] * 2
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def _rgb_to_hex(r: int, g: int, b: int) -> str:
    return f"#{r:02x}{g:02x}{b:02x}"


LATEX_UNICODE_MAP = {
    r"\pm": "±", r"\times": "×", r"\div": "÷", r"\leq": "≤", r"\geq": "≥",
    r"\neq": "≠", r"\approx": "≈", r"\infty": "∞", r"\partial": "∂", r"\nabla": "∇",
    r"\alpha": "α", r"\beta": "β", r"\gamma": "γ", r"\delta": "δ", r"\epsilon": "ε",
    r"\theta": "θ", r"\lambda": "λ", r"\mu": "μ", r"\pi": "π", r"\sigma": "σ",
    r"\omega": "ω", r"\phi": "φ", r"\psi": "ψ", r"\Omega": "Ω", r"\Sigma": "Σ",
    r"\Delta": "Δ", r"\Lambda": "Λ", r"\Pi": "Π", r"\Phi": "Φ", r"\Theta": "Θ",
    r"\rightarrow": "→", r"\leftarrow": "←", r"\Rightarrow": "⇒", r"\Leftarrow": "⇐",
    r"\cdot": "·", r"\ldots": "...", r"\cdots": "⋯", r"\quad": "  ",
    r"\log": "log", r"\ln": "ln", r"\sin": "sin", r"\cos": "cos", r"\tan": "tan",
    r"\exp": "exp", r"\lim": "lim", r"\max": "max", r"\min": "min", r"\det": "det",
    r"\sum": "Σ", r"\prod": "Π", r"\int": "∫", r"\oint": "∮",
}


def _strip_latex_to_unicode(latex: str) -> str:
    s = latex.strip()
    if s.startswith("$$") and s.endswith("$$"):
        s = s[2:-2].strip()
    elif s.startswith("$") and s.endswith("$"):
        s = s[1:-1].strip()
    if s.startswith("\\(") or s.startswith("\\["):
        s = s[2:]
    if s.endswith("\\)") or s.endswith("\\]"):
        s = s[:-2]
    s = s.strip()
    for cmd, uni in sorted(LATEX_UNICODE_MAP.items(), key=lambda x: -len(x[0])):
        s = s.replace(cmd, uni)
    s = re.sub(r"\\frac\{([^}]*)\}\{([^}]*)\}", r"(\1)/(\2)", s)
    s = re.sub(r"\\sqrt\{([^}]*)\}", r"√(\1)", s)
    s = re.sub(r"\\[a-zA-Z]+", "", s)
    s = re.sub(r"[{}]", "", s)
    s = re.sub(r"\^([0-9a-zA-Z])", r"^\1", s)
    s = s.replace("~", " ")
    return s.strip()


def _strip_html(html: str) -> str:
    text = re.sub(r"<br\s*/?>", "\n", html)
    text = re.sub(r"</?(?:p|div|span|section)[^>]*>", "", text)
    text = re.sub(r"<strong[^>]*>(.*?)</strong>", r"\1", text, flags=re.DOTALL)
    text = re.sub(r"<b[^>]*>(.*?)</b>", r"\1", text, flags=re.DOTALL)
    text = re.sub(r"<em[^>]*>(.*?)</em>", r"\1", text, flags=re.DOTALL)
    text = re.sub(r"<i[^>]*>(.*?)</i>", r"\1", text, flags=re.DOTALL)
    text = re.sub(r"<code[^>]*>(.*?)</code>", r"\1", text, flags=re.DOTALL)
    text = re.sub(r"<a[^>]*>(.*?)</a>", r"\1", text, flags=re.DOTALL)
    text = re.sub(r"<s[^>]*>(.*?)</s>", r"\1", text, flags=re.DOTALL)
    text = re.sub(r"<del[^>]*>(.*?)</del>", r"\1", text, flags=re.DOTALL)
    text = re.sub(r"<mark[^>]*>(.*?)</mark>", r"\1", text, flags=re.DOTALL)
    text = re.sub(r"<sup[^>]*>(.*?)</sup>", r"\1", text, flags=re.DOTALL)
    text = re.sub(r"<sub[^>]*>(.*?)</sub>", r"\1", text, flags=re.DOTALL)
    text = re.sub(r"<img[^>]*alt=\"([^\"]*)\"[^>]*/?>", r"[\1]", text)
    text = re.sub(r"<[^>]+>", "", text)
    text = text.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
    text = text.replace("&nbsp;", " ").replace("&quot;", '"').replace("&#39;", "'")
    text = text.replace("&#x27;", "'").replace("&#x2F;", "/")
    return text.strip()


def _fix_latex_backslashes(latex: str) -> str:
    latex = re.sub(r"(?<!\\)\\(\s+[a-z](?![a-zA-Z]))", r"\\\\\1", latex)
    latex = re.sub(r"\}\\", "}\\\\", latex)
    latex = re.sub(r"\\\\(begin|end|frac|int|sum|sqrt|alpha|beta|gamma|delta|epsilon|omega|pi|sigma|mu|lambda|left|right|text|mathrm|mathbb|mathcal|cdot|quad|,|;|infty|partial)", r"\\\1", latex)
    return latex


def _render_latex_to_image(latex_code: str, dpi: int = 150, font_size: int = 28,
                           text_color: str = "#f0f0f0", bg_color: str = "#000000") -> Optional[bytes]:
    cleaned = latex_code.strip()
    if cleaned.startswith("$$") and cleaned.endswith("$$"):
        cleaned = cleaned[2:-2].strip()
    elif cleaned.startswith("$") and cleaned.endswith("$"):
        cleaned = cleaned[1:-1].strip()
    if cleaned.startswith("\\(") or cleaned.startswith("\\["):
        cleaned = cleaned[2:]
    if cleaned.endswith("\\)") or cleaned.endswith("\\]"):
        cleaned = cleaned[:-2]
    cleaned = cleaned.strip()
    if not cleaned:
        return None

    cleaned = _fix_latex_backslashes(cleaned)

    result = _render_latex_pdflatex(cleaned, dpi, font_size, text_color, bg_color)
    if result:
        return result
    return _render_latex_matplotlib(cleaned, dpi, font_size, text_color, bg_color)


def _render_latex_pdflatex(latex: str, dpi: int, font_size: int,
                            text_color: str, bg_color: str) -> Optional[bytes]:
    try:
        import fitz
    except ImportError:
        return None
    try:
        subprocess.run(["which", "pdflatex"], capture_output=True, check=True, timeout=3)
    except Exception:
        return None

    try:
        tex_size = max(int(font_size * 1.2), 14)
        r_val = int(text_color[1:3], 16)
        g_val = int(text_color[3:5], 16)
        b_val = int(text_color[5:7], 16)
        br_val = int(bg_color[1:3], 16)
        bg_val = int(bg_color[3:5], 16)
        bb_val = int(bg_color[5:7], 16)
        tex_src = (
            f"\\documentclass[{tex_size}pt]{{article}}\n"
            f"\\usepackage[margin=2pt, papersize=20in,14in]{{geometry}}\n"
            f"\\usepackage{{amsmath,amssymb}}\n"
            f"\\usepackage{{xcolor}}\n"
            f"\\usepackage{{lmodern}}\n"
            f"\\usepackage[T1]{{fontenc}}\n"
            f"\\renewcommand{{\\familydefault}}{{\\sfdefault}}\n"
            f"\\pagestyle{{empty}}\n"
            f"\\definecolor{{mytext}}{{RGB}}{{{r_val},{g_val},{b_val}}}\n"
            f"\\definecolor{{mybg}}{{RGB}}{{{br_val},{bg_val},{bb_val}}}\n"
            f"\\begin{{document}}\n"
            f"\\noindent\\pagecolor{{mybg}}\\color{{mytext}}\n"
            f"$${latex}$$\n"
            f"\\end{{document}}\n"
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            tex_path = os.path.join(tmpdir, "formula.tex")
            with open(tex_path, "w", encoding="utf-8") as f:
                f.write(tex_src)

            subprocess.run(
                ["pdflatex", "-interaction=nonstopmode", "-output-directory", tmpdir, tex_path],
                capture_output=True, timeout=15,
            )
            pdf_path = os.path.join(tmpdir, "formula.pdf")
            if not os.path.exists(pdf_path):
                return None

            doc = fitz.open(pdf_path)
            page = doc[0]

            blocks = page.get_text("blocks")
            if blocks:
                pad_pts = 12
                cx0 = min(b[0] for b in blocks) - pad_pts
                cy0 = min(b[1] for b in blocks) - pad_pts
                cx1 = max(b[2] for b in blocks) + pad_pts
                cy1 = max(b[3] for b in blocks) + pad_pts
                clip = fitz.Rect(cx0, cy0, cx1, cy1)
            else:
                clip = page.rect

            render_dpi = max(dpi, 200)
            mat = fitz.Matrix(render_dpi / 72, render_dpi / 72)
            pix = page.get_pixmap(matrix=mat, clip=clip)
            png_data = pix.tobytes("png")
            doc.close()

            return png_data
    except Exception:
        return None


def _render_latex_matplotlib(cleaned: str, dpi: int, font_size: int,
                              text_color: str, bg_color: str) -> Optional[bytes]:
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        fig = plt.figure(figsize=(0.01, 0.01))
        fig.text(
            0.5, 0.5, f"${cleaned}$",
            fontsize=font_size, color=text_color,
            ha="center", va="center",
            transform=fig.transFigure,
        )
        fig.patch.set_facecolor(bg_color)

        buf = io.BytesIO()
        fig.savefig(
            buf, format="png", dpi=dpi,
            bbox_inches="tight", pad_inches=0.04,
            facecolor=bg_color,
        )
        plt.close(fig)
        buf.seek(0)
        return buf.getvalue()
    except Exception:
        return None


def _fix_mermaid_syntax(code: str) -> str:
    lines = code.split("\n")
    fixed = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("subgraph") or stripped.startswith("end") or stripped.startswith(("style ", "classDef ", "click ")):
            fixed.append(line)
            continue
        if not stripped or stripped.startswith(("%%", "---", "sequenceDiagram", "flowchart", "graph", "pie", "gantt", "gitGraph", "journey", "stateDiagram", "erDiagram", "classDiagram", "mindmap", "timeline")):
            fixed.append(line)
            continue
        def quote_label(m):
            node_id = m.group(1)
            label = m.group(2)
            if '"' in label or '\u201c' in label or '\u201d' in label:
                return m.group(0)
            return f'{node_id}["{label}"]'
        line = re.sub(r'(\w+)\[([^\[\]]*[\(\)\{\}<>~][^\[\]]*)\]', quote_label, line)
        fixed.append(line)
    return "\n".join(fixed)


def _render_mermaid_to_image(mermaid_code: str, theme: str = "dark",
                              bg_color: str = "#000000") -> Optional[bytes]:
    try:
        import shutil
        if not shutil.which("mmdc"):
            return None
        safe_code = mermaid_code.replace("\u201c", '"').replace("\u201d", '"').replace("\u2018", "'").replace("\u2019", "'")
        safe_code = _fix_mermaid_syntax(safe_code)
        with tempfile.NamedTemporaryFile(mode="w", suffix=".mmd", delete=False, encoding="utf-8") as f:
            f.write(safe_code)
            mmd_file = f.name
        png_file = os.path.splitext(mmd_file)[0] + ".png"
        mmdc_theme = "dark" if theme in DARK_THEMES else "default"
        bg = bg_color if theme in DARK_THEMES else "white"
        result = subprocess.run(
            ["mmdc", "-i", mmd_file, "-o", png_file, "-t", mmdc_theme, "-b", bg,
             "-w", "2400", "--scale", "2"],
            capture_output=True, timeout=30,
        )
        if result.returncode == 0 and Path(png_file).exists():
            data = Path(png_file).read_bytes()
            Path(mmd_file).unlink(missing_ok=True)
            Path(png_file).unlink(missing_ok=True)
            return data
        Path(mmd_file).unlink(missing_ok=True)
        Path(png_file).unlink(missing_ok=True)
    except Exception:
        pass
    return None


def _parse_html_elements(html: str) -> List[dict]:
    elements = []
    consumed = set()

    def add_elem(pos: int, elem: dict):
        consumed.add(pos)
        elem["pos"] = pos
        elements.append(elem)

    for match in re.finditer(r"<h([1-6])[^>]*>(.*?)</h\1>", html, re.DOTALL):
        add_elem(match.start(), {
            "type": "heading", "level": int(match.group(1)),
            "text": _strip_html(match.group(2)).strip(),
        })

    for match in re.finditer(
        r'<pre(?:\s+class="[^"]*")?><code(?:\s+class="language-(\w+)")?>(.*?)</code></pre>',
        html, re.DOTALL,
    ):
        lang = match.group(1) or ""
        code = _strip_html(match.group(2))
        add_elem(match.start(), {"type": "code", "lang": lang, "code": code})

    for match in re.finditer(r"<table[^>]*>(.*?)</table>", html, re.DOTALL):
        table_html = match.group(1)
        rows = []
        for row_m in re.finditer(r"<tr[^>]*>(.*?)</tr>", table_html, re.DOTALL):
            cells = []
            for cell_m in re.finditer(r"<(t[hd])[^>]*>(.*?)</\1>", row_m.group(1), re.DOTALL):
                cells.append({"type": cell_m.group(1), "text": _strip_html(cell_m.group(2)).strip()})
            if cells:
                rows.append(cells)
        add_elem(match.start(), {"type": "table", "rows": rows})

    for match in re.finditer(r"<([uo]l)[^>]*>(.*?)</\1>", html, re.DOTALL):
        tag = match.group(1)
        items = []
        for item_m in re.finditer(r"<li[^>]*>(.*?)</li>", match.group(2), re.DOTALL):
            item_text = _strip_html(item_m.group(1)).strip()
            sub_items = []
            for sub_m in re.finditer(r"<[uo]l[^>]*>(.*?)</[uo]l>", item_m.group(1), re.DOTALL):
                for sub_i in re.finditer(r"<li[^>]*>(.*?)</li>", sub_m.group(1), re.DOTALL):
                    sub_items.append(_strip_html(sub_i.group(1)).strip())
            items.append({"text": item_text, "sub_items": sub_items})
        add_elem(match.start(), {"type": "list", "ordered": tag == "ol", "items": items})

    for match in re.finditer(r"<blockquote[^>]*>(.*?)</blockquote>", html, re.DOTALL):
        add_elem(match.start(), {"type": "blockquote", "text": _strip_html(match.group(1)).strip()})

    for match in re.finditer(r"<img\s+[^>]*src=\"([^\"]+)\"[^>]*/?>", html):
        src = match.group(1)
        alt = ""
        alt_m = re.search(r'alt="([^"]*)"', match.group(0))
        if alt_m:
            alt = alt_m.group(1)
        add_elem(match.start(), {"type": "image", "src": src, "alt": alt})

    for match in re.finditer(r"<p(?:\s[^>]*)?>(.*?)</p>", html, re.DOTALL):
        if match.start() in consumed:
            continue
        p_html = match.group(1)
        p_text = p_html.strip()
        if not p_text or p_text.startswith("<code") or p_text.startswith("<pre"):
            continue
        has_math = bool(re.search(r"\$.+?\$", p_text) or re.search(r"\\\[|\\\(|\\begin\{", p_text))
        if has_math:
            math_blocks = _extract_math_from_text(_strip_html(p_html))
            for mb in math_blocks:
                if mb["type"] == "math":
                    add_elem(match.start(), mb)
                else:
                    add_elem(match.start(), {"type": "paragraph", "text": mb["text"]})
        else:
            text = _strip_html(p_html)
            if text:
                add_elem(match.start(), {"type": "paragraph", "text": text})

    elements.sort(key=lambda x: x.get("pos", 0) if "pos" in x else 999999)

    seen = set()
    deduped = []
    for e in elements:
        key = (e.get("type", ""), str(e)[:80])
        if key not in seen:
            seen.add(key)
            deduped.append(e)
    return deduped


def _extract_math_from_text(text: str) -> List[dict]:
    results = []
    pattern = r"(\$\$[\s\S]+?\$\$|\$[^$\n]+?\$|\\\[.+?\\\]|\\\(.+?\\\))"
    last_end = 0
    for match in re.finditer(pattern, text):
        start = match.start()
        if start > last_end:
            between = text[last_end:start].strip()
            if between:
                results.append({"type": "text", "text": between})
        results.append({"type": "math", "latex": match.group(0)})
        last_end = match.end()
    if last_end < len(text):
        remaining = text[last_end:].strip()
        if remaining:
            results.append({"type": "text", "text": remaining})
    if not results:
        results.append({"type": "text", "text": text})
    return results


class PPTXExporter:
    """Markdown 幻灯片 -> PowerPoint (.pptx)

    支持: 标题、段落、代码块(带背景)、表格、列表、引用块、
    数学公式(渲染为图片)、Mermaid图表(渲染为图片)、图片嵌入。
    """

    def __init__(self):
        self.theme = "black"
        self.font_size = 18
        self.heading_font = "Source Sans 3"
        self.body_font = "Source Sans 3"
        self.code_font = "Source Code Pro"
        self.aspect_ratio = "16:9"
        self._slide_width_inches = 13.333
        self._slide_height_inches = 7.5
        self._margin = 0.5
        self._image_base_path: Optional[Path] = None

    def export(self, slides: List[Slide], output_path: str, title: str = "Presentation") -> str:
        output_p = Path(output_path)
        output_p.parent.mkdir(parents=True, exist_ok=True)
        prs = self._create_presentation()
        colors = THEME_COLORS.get(self.theme, THEME_COLORS["black"])
        for slide_data in slides:
            self._add_slide(prs, slide_data, colors)
        prs.save(str(output_p))
        return str(output_p)

    def export_from_converter(self, converter, md_content: str, output_path: str,
                              title: str = "Presentation") -> str:
        slides = converter.parser.parse(md_content)
        return self.export(slides, output_path, title=title)

    def _create_presentation(self) -> Presentation:
        prs = Presentation()
        if self.aspect_ratio == "4:3":
            w, h = 10, 7.5
        elif self.aspect_ratio == "21:9":
            w, h = 13.333, 5.714
        elif self.aspect_ratio == "3:2":
            w, h = 10, 6.667
        else:
            w, h = 13.333, 7.5
        prs.slide_width = Inches(w)
        prs.slide_height = Inches(h)
        self._slide_width_inches = w
        self._slide_height_inches = h
        return prs

    def _content_width(self) -> float:
        return self._slide_width_inches - 2 * self._margin

    def _add_slide(self, prs: Presentation, slide: Slide, colors: dict):
        layout = prs.slide_layouts[6]
        ppt_slide = prs.slides.add_slide(layout)

        bg_color = colors["bg"]
        if slide.attributes and slide.attributes.background_color:
            try:
                r, g, b = _hex_to_rgb(slide.attributes.background_color)
                bg_color = RGBColor(r, g, b)
            except (ValueError, AttributeError):
                pass
        ppt_slide.background.fill.solid()
        ppt_slide.background.fill.fore_color.rgb = bg_color

        content = slide.content
        if not content.strip():
            return

        elements = _parse_html_elements(content)
        if not elements:
            return

        y = self._margin
        bottom = self._slide_height_inches - self._margin
        col_gap = 0.3

        for elem in elements:
            if elem["type"] == "heading":
                y = self._add_heading(ppt_slide, elem["level"], elem["text"], colors, y)

        body_elements = [e for e in elements if e["type"] != "heading"]

        total_body_height = sum(self._estimate_element_height(e) for e in body_elements)
        available = bottom - y

        if len(body_elements) >= 2 and total_body_height > available * 0.75:
            mid = len(body_elements) // 2
            left_elements = body_elements[:mid]
            right_elements = body_elements[mid:]

            left_y = y
            col_width = (self._content_width() - col_gap) / 2
            left_x = self._margin
            right_x = self._margin + col_width + col_gap

            for elem in left_elements:
                if left_y >= bottom - 0.1:
                    break
                left_y = self._add_element_in_column(ppt_slide, elem, colors, left_x, left_y, col_width, bottom)

            right_y = y
            for elem in right_elements:
                if right_y >= bottom - 0.1:
                    break
                right_y = self._add_element_in_column(ppt_slide, elem, colors, right_x, right_y, col_width, bottom)
        else:
            for elem in body_elements:
                if y >= bottom - 0.1:
                    break
                y = self._add_element_full(ppt_slide, elem, colors, y)

    def _add_element_full(self, slide, elem, colors, y):
        if elem["type"] == "paragraph":
            return self._add_paragraph(slide, elem["text"], colors, y)
        elif elem["type"] == "code":
            if elem["lang"] == "mermaid":
                return self._add_mermaid(slide, elem["code"], colors, y)
            return self._add_code_block(slide, elem["code"], elem["lang"], colors, y)
        elif elem["type"] == "table":
            return self._add_table(slide, elem["rows"], colors, y)
        elif elem["type"] == "list":
            return self._add_list(slide, elem["items"], elem["ordered"], colors, y)
        elif elem["type"] == "blockquote":
            return self._add_blockquote(slide, elem["text"], colors, y)
        elif elem["type"] == "math":
            return self._add_math(slide, elem["latex"], colors, y)
        elif elem["type"] == "image":
            return self._add_image(slide, elem["src"], colors, y)
        return y

    def _add_element_in_column(self, slide, elem, colors, x, y, width, bottom):
        if elem["type"] == "paragraph":
            return self._add_paragraph(slide, elem["text"], colors, y, x_offset=x, col_width=width)
        elif elem["type"] == "code":
            if elem["lang"] == "mermaid":
                return self._add_mermaid(slide, elem["code"], colors, y, x_offset=x, max_w=width)
            return self._add_code_block(slide, elem["code"], elem["lang"], colors, y, x_offset=x, col_width=width)
        elif elem["type"] == "table":
            return self._add_table(slide, elem["rows"], colors, y, x_offset=x, col_width=width)
        elif elem["type"] == "list":
            return self._add_list(slide, elem["items"], elem["ordered"], colors, y, x_offset=x, col_width=width)
        elif elem["type"] == "blockquote":
            return self._add_blockquote(slide, elem["text"], colors, y, x_offset=x, col_width=width)
        elif elem["type"] == "math":
            return self._add_math(slide, elem["latex"], colors, y, x_offset=x, max_w=width)
        elif elem["type"] == "image":
            return self._add_image(slide, elem["src"], colors, y, x_offset=x, max_w=width)
        return y

    def _estimate_element_height(self, elem: dict, scale: float = 1.0) -> float:
        etype = elem["type"]
        if etype == "heading":
            h_scale = self.HEADING_SCALE.get(elem.get("level", 2), 1.0)
            sz = max(int(self.font_size * h_scale * scale), 10)
            return sz * 1.5 / 72.0 + 0.1
        elif etype == "paragraph":
            sz = max(int(self.font_size * scale), 8)
            return sz * 1.5 / 72.0 + 0.15
        elif etype == "code":
            if elem["lang"] == "mermaid":
                return 2.5 * scale
            code_fs = max(int(self.font_size * self.CODE_SCALE * scale), 7)
            line_h = code_fs * 1.6 / 72.0
            nl = len(elem["code"].strip().split("\n"))
            header_h = code_fs / 72.0 if elem.get("lang") else 0
            return min(line_h * nl * scale + 0.2 * scale + header_h, 5.5)
        elif etype == "math":
            is_d = elem["latex"].strip().startswith("$$")
            return (0.9 if is_d else 0.35) + 0.15
        elif etype == "table":
            nrows = len(elem.get("rows", []))
            cell_fs = max(int(self.font_size * self.TABLE_CELL_SCALE * scale), 7)
            row_h = max(cell_fs * 2.0 / 72.0, 0.2)
            return row_h * nrows + 0.15
        elif etype == "list":
            total = len(elem["items"]) + sum(len(it.get("sub_items", [])) for it in elem["items"])
            list_fs = max(int(self.font_size * scale), 8)
            line_h = list_fs * 1.6 / 72.0
            return min(line_h * total + 0.2, 5.0)
        elif etype == "blockquote":
            bq_fs = max(int(self.font_size * self.BLOCKQUOTE_SCALE * scale), 8)
            return max(bq_fs * 1.6 / 72.0 + 0.2, 0.5)
        elif etype == "image":
            return 2.0 * scale
        return 0.4

    HEADING_SCALE = {1: 2.2, 2: 1.8, 3: 1.4, 4: 1.2, 5: 1.0, 6: 0.9}
    CODE_SCALE = 0.6
    TABLE_HEADER_SCALE = 0.8
    TABLE_CELL_SCALE = 0.75
    BLOCKQUOTE_SCALE = 0.9
    MATH_DISPLAY_SCALE = 2.0
    MATH_INLINE_SCALE = 1.3
    LABEL_SCALE = 0.55

    def _add_heading(self, slide, level: int, text: str, colors: dict, y: float, font_scale: float = 1.0) -> float:
        scale = self.HEADING_SCALE.get(level, 1.0) * font_scale
        sz = max(int(self.font_size * scale), 10)
        h = sz * 1.5 / 72.0 + 0.1
        tb = slide.shapes.add_textbox(Inches(self._margin), Inches(y), Inches(self._content_width()), Inches(h))
        tf = tb.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = text
        p.font.size = Pt(sz)
        p.font.bold = True
        p.font.color.rgb = colors["heading"]
        p.font.name = self.heading_font
        p.alignment = PP_ALIGN.LEFT
        p.space_after = Pt(4)
        return y + h

    def _add_paragraph(self, slide, text: str, colors: dict, y: float,
                       font_scale: float = 1.0, x_offset: float = None, col_width: float = None) -> float:
        x = x_offset if x_offset is not None else self._margin
        w = col_width if col_width is not None else self._content_width()
        sz = max(int(self.font_size * font_scale), 8)
        h = max(sz * 1.5 / 72.0 + 0.1, 0.2)
        tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
        tf = tb.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = text
        p.font.size = Pt(sz)
        p.font.color.rgb = colors["text"]
        p.font.name = self.body_font
        p.space_after = Pt(4)
        return y + h + 0.05

    def _add_code_block(self, slide, code: str, lang: str, colors: dict, y: float,
                        font_scale: float = 1.0, x_offset: float = None, col_width: float = None) -> float:
        x = x_offset if x_offset is not None else self._margin
        w = col_width if col_width is not None else self._content_width()
        lines = code.strip().split("\n")
        num_lines = max(len(lines), 1)
        code_fs = max(int(self.font_size * self.CODE_SCALE * font_scale), 7)
        line_h = code_fs * 1.6 / 72.0
        header_h = (code_fs + 6) / 72.0 if lang else 0
        h = min(line_h * num_lines + 0.2 * font_scale + header_h, 5.5)

        shape = slide.shapes.add_shape(
            MSO_SHAPE.ROUNDED_RECTANGLE,
            Inches(x), Inches(y), Inches(w), Inches(h),
        )
        shape.fill.solid()
        shape.fill.fore_color.rgb = colors["code_bg"]
        shape.line.fill.background()
        shape.shadow.inherit = False

        left_margin = x + 0.15
        inner_w = w - 0.3

        if lang:
            lbl_fs = max(int(self.font_size * self.LABEL_SCALE * font_scale), 7)
            lbl = slide.shapes.add_textbox(Inches(left_margin), Inches(y + 0.05), Inches(inner_w), Inches(0.3))
            lbl_tf = lbl.text_frame
            lbl_tf.word_wrap = False
            lp = lbl_tf.paragraphs[0]
            lp.text = lang.upper()
            lp.font.size = Pt(lbl_fs)
            lp.font.color.rgb = colors["accent"]
            lp.font.name = self.body_font
            lp.font.bold = True
            code_y = y + header_h + 0.05
            code_h = h - header_h - 0.1
        else:
            code_y = y + 0.1
            code_h = h - 0.2

        tb = slide.shapes.add_textbox(Inches(left_margin), Inches(code_y), Inches(inner_w), Inches(code_h))
        tf = tb.text_frame
        tf.word_wrap = False

        if lang:
            highlighted = _highlight_code(code, lang, self.theme)
        else:
            default_color = colors["code_text"]
            highlighted = []
            for line in code.strip().split("\n"):
                highlighted.append([(line, default_color)])

        for i, line_tokens in enumerate(highlighted):
            para = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
            para.space_after = Pt(0)
            para.line_spacing = Pt(code_fs + 2)
            if not line_tokens:
                run = para.add_run()
                run.text = " "
                run.font.size = Pt(code_fs)
                run.font.name = self.code_font
                run.font.color.rgb = colors["code_text"]
                continue
            for text, color in line_tokens:
                if not text:
                    continue
                run = para.add_run()
                run.text = text
                run.font.size = Pt(code_fs)
                run.font.name = self.code_font
                run.font.color.rgb = color

        return y + h + 0.15

    def _add_mermaid(self, slide, mermaid_code: str, colors: dict, y: float,
                     x_offset: float = None, max_w: float = None) -> float:
        bg_hex = _rgb_to_hex(*_hex_to_rgb(str(colors["bg"])))
        img_data = _render_mermaid_to_image(mermaid_code, self.theme, bg_color=bg_hex)
        w = max_w if max_w is not None else self._content_width()
        if img_data:
            return self._add_image_from_bytes(slide, img_data, y, max_w=w, max_h=4.5, render_dpi=150,
                                               x_offset=x_offset)
        return self._add_code_block(slide, mermaid_code, "mermaid", colors, y,
                                    x_offset=x_offset, col_width=w)

    def _add_math(self, slide, latex: str, colors: dict, y: float,
                   x_offset: float = None, max_w: float = None) -> float:
        text_hex = _rgb_to_hex(*_hex_to_rgb(str(colors["text"])))
        bg_hex = _rgb_to_hex(*_hex_to_rgb(str(colors["bg"])))
        is_display = latex.strip().startswith("$$") or latex.strip().startswith("\\[")
        fs = max(int(self.font_size * self.MATH_DISPLAY_SCALE), 14) if is_display else max(int(self.font_size * self.MATH_INLINE_SCALE), 10)
        render_dpi = 200
        min_h = 0.7 if is_display else 0.4
        max_h_val = 1.5 if is_display else 0.7
        mw = max_w if max_w is not None else self._content_width()
        img_data = _render_latex_to_image(latex, dpi=render_dpi, font_size=fs, text_color=text_hex, bg_color=bg_hex)
        if img_data:
            return self._add_image_from_bytes(
                slide, img_data, y,
                max_w=mw, min_h=min_h, max_h=max_h_val, render_dpi=render_dpi,
                x_offset=x_offset,
            )
        cleaned = latex.strip()
        if cleaned.startswith("$$") and cleaned.endswith("$$"):
            cleaned = cleaned[2:-2].strip()
        elif cleaned.startswith("$") and cleaned.endswith("$"):
            cleaned = cleaned[1:-1].strip()
        if cleaned.startswith("\\(") or cleaned.startswith("\\["):
            cleaned = cleaned[2:]
        if cleaned.endswith("\\)") or cleaned.endswith("\\]"):
            cleaned = cleaned[:-2]
        cleaned = cleaned.strip()
        p_fs = fs
        x = x_offset if x_offset is not None else self._margin
        w = max_w if max_w is not None else self._content_width()
        tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(min_h + 0.05))
        tf = tb.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = cleaned
        p.font.size = Pt(p_fs)
        p.font.color.rgb = colors["text"]
        p.font.name = self.body_font
        if is_display:
            p.alignment = PP_ALIGN.CENTER
        return y + min_h + 0.15

    def _add_image_from_bytes(self, slide, img_data: bytes, y: float,
                               max_w: float = 12.0, max_h: float = 4.0,
                               min_h: float = 0.0,
                               render_dpi: int = 150,
                               x_offset: float = None) -> float:
        try:
            from PIL import Image
            img = Image.open(io.BytesIO(img_data))
            iw, ih = img.size
            if ih == 0 or iw == 0:
                return y + 0.2
            aspect = iw / ih
            display_w = max_w
            display_h = display_w / aspect
            if display_h > max_h:
                display_h = max_h
                display_w = display_h * aspect
            if display_h < min_h:
                display_h = min_h
                display_w = min(display_h * aspect, max_w)
            x = x_offset if x_offset is not None else self._margin
            slide.shapes.add_picture(
                io.BytesIO(img_data),
                Inches(x), Inches(y),
                Inches(display_w), Inches(display_h),
            )
            return y + display_h + 0.1
        except Exception:
            return y + 0.3

    def _add_table(self, slide, rows: List[list], colors: dict, y: float, font_scale: float = 1.0,
                    x_offset: float = None, col_width: float = None) -> float:
        if not rows:
            return y
        x = x_offset if x_offset is not None else self._margin
        w = col_width if col_width is not None else self._content_width()
        num_cols = max(len(row) for row in rows)
        num_rows = len(rows)
        header_fs = max(int(self.font_size * self.TABLE_HEADER_SCALE * font_scale), 8)
        cell_fs = max(int(self.font_size * self.TABLE_CELL_SCALE * font_scale), 7)
        row_h = max(cell_fs * 2.0 / 72.0, 0.2)
        table_h = row_h * num_rows
        table_w = w

        shape = slide.shapes.add_table(num_rows, num_cols, Inches(x), Inches(y), Inches(table_w), Inches(table_h))
        table = shape.table

        for col_idx in range(num_cols):
            table.columns[col_idx].width = Inches(table_w / num_cols)

        for i, row in enumerate(rows):
            for j, cell_data in enumerate(row):
                if j >= num_cols:
                    continue
                cell = table.cell(i, j)
                cell.vertical_anchor = 1
                cell_text = cell_data.get("text", "")

                math_segments = _extract_math_from_text(cell_text)
                if any(ms["type"] == "math" for ms in math_segments):
                    para = cell.text_frame.paragraphs[0]
                    para.font.name = self.body_font
                    para.font.size = Pt(cell_fs)
                    para.font.color.rgb = colors["text"]

                    for seg in math_segments:
                        if seg["type"] == "text":
                            clean = seg["text"].strip()
                            if clean:
                                run = para.add_run()
                                run.text = clean
                                run.font.size = Pt(cell_fs)
                                run.font.name = self.body_font
                                run.font.color.rgb = colors["text"]
                        elif seg["type"] == "math":
                            run = para.add_run()
                            unicode_text = _strip_latex_to_unicode(seg["latex"])
                            run.text = " " + unicode_text + " "
                            run.font.size = Pt(cell_fs)
                            run.font.name = self.body_font
                            run.font.italic = True
                            run.font.color.rgb = colors["accent"]
                else:
                    cell.text = cell_text
                    for para in cell.text_frame.paragraphs:
                        para.font.name = self.body_font
                        if cell_data.get("type") == "th":
                            para.font.size = Pt(header_fs)
                            para.font.bold = True
                            para.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
                        else:
                            para.font.size = Pt(cell_fs)
                            para.font.color.rgb = colors["text"]

                if cell_data.get("type") == "th":
                    cell.fill.solid()
                    cell.fill.fore_color.rgb = colors["accent"]
                else:
                    cell.fill.solid()
                    if i % 2 == 0:
                        cell.fill.fore_color.rgb = colors.get("block_bg", colors["bg"])
                    else:
                        cell.fill.fore_color.rgb = colors["bg"]
        return y + table_h + 0.15

    def _add_list(self, slide, items: List[dict], ordered: bool, colors: dict, y: float,
                  font_scale: float = 1.0, x_offset: float = None, col_width: float = None) -> float:
        list_fs = max(int(self.font_size * font_scale), 8)
        sub_fs = max(int(self.font_size * self.BLOCKQUOTE_SCALE * font_scale), 7)
        total = len(items) + sum(len(it.get("sub_items", [])) for it in items)
        line_h = list_fs * 1.6 / 72.0
        h = min(line_h * total + 0.2, 5.5)
        left = (x_offset if x_offset is not None else self._margin) + 0.2
        w = (col_width if col_width is not None else self._content_width()) - 0.4

        tb = slide.shapes.add_textbox(Inches(left), Inches(y), Inches(w), Inches(h))
        tf = tb.text_frame
        tf.word_wrap = True

        for i, item in enumerate(items):
            prefix = f"{i + 1}. " if ordered else "\u2022 "
            text = f"{prefix}{item['text']}"
            p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
            p.text = text
            p.font.size = Pt(list_fs)
            p.font.color.rgb = colors["text"]
            p.font.name = self.body_font
            p.space_after = Pt(3)
            for sub in item.get("sub_items", []):
                sp = tf.add_paragraph()
                sp.text = f"    \u25e6 {sub}"
                sp.font.size = Pt(sub_fs)
                sp.font.color.rgb = colors["text"]
                sp.font.name = self.body_font
                sp.space_after = Pt(2)
        return y + h + 0.05

    def _add_blockquote(self, slide, text: str, colors: dict, y: float,
                        font_scale: float = 1.0, x_offset: float = None, col_width: float = None) -> float:
        x = x_offset if x_offset is not None else self._margin
        w = col_width if col_width is not None else self._content_width()
        bq_fs = max(int(self.font_size * self.BLOCKQUOTE_SCALE * font_scale), 8)
        h = max(bq_fs * 1.6 / 72.0 + 0.2, 0.5)
        shape = slide.shapes.add_shape(
            MSO_SHAPE.RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h)
        )
        shape.fill.solid()
        shape.fill.fore_color.rgb = colors.get("block_bg", colors["bg"])
        shape.line.fill.background()

        bar = slide.shapes.add_shape(
            MSO_SHAPE.RECTANGLE, Inches(x), Inches(y), Inches(0.08), Inches(h)
        )
        bar.fill.solid()
        bar.fill.fore_color.rgb = colors["accent"]
        bar.line.fill.background()

        tb = slide.shapes.add_textbox(
            Inches(x + 0.2), Inches(y + 0.1), Inches(w - 0.3), Inches(h - 0.2)
        )
        tf = tb.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = text
        p.font.size = Pt(bq_fs)
        p.font.color.rgb = colors["text"]
        p.font.name = self.body_font
        p.font.italic = True
        return y + h + 0.1

    def _add_image(self, slide, src: str, colors: dict, y: float,
                   x_offset: float = None, max_w: float = None) -> float:
        stream = None
        if src.startswith("data:"):
            try:
                header, data = src.split(",", 1)
                stream = io.BytesIO(base64.b64decode(data))
            except Exception:
                return y
        elif src.startswith(("http://", "https://")):
            try:
                import urllib.request
                resp = urllib.request.urlopen(src, timeout=10)
                stream = io.BytesIO(resp.read())
            except Exception:
                return y
        else:
            img_path = Path(src)
            if not img_path.is_absolute() and self._image_base_path:
                img_path = self._image_base_path / src
            if img_path.exists():
                stream = io.BytesIO(img_path.read_bytes())
        if stream is None:
            return y
        try:
            x = x_offset if x_offset is not None else self._margin
            max_w_val = max_w if max_w is not None else self._content_width()
            max_h_val = 4.0
            stream.seek(0)
            from PIL import Image
            img = Image.open(stream)
            iw, ih = img.size
            if ih == 0 or iw == 0:
                return y
            aspect = iw / ih
            display_w = max_w_val
            display_h = display_w / aspect
            if display_h > max_h_val:
                display_h = max_h_val
                display_w = display_h * aspect
            stream.seek(0)
            slide.shapes.add_picture(stream, Inches(x), Inches(y), Inches(display_w), Inches(display_h))
            return y + display_h + 0.2
        except Exception:
            return y


def export_pptx(slides: List[Slide], output_path: str, theme: str = "black",
                aspect_ratio: str = "16:9") -> str:
    exporter = PPTXExporter()
    exporter.theme = theme
    exporter.aspect_ratio = aspect_ratio
    return exporter.export(slides, output_path)
