"""External renderers — LaTeX, Mermaid, and code highlighting support.

Reuses the existing HeiBan rendering infrastructure (mmdc, pdflatex,
Pygments) from the original project but adapted for the new architecture.
"""

import base64
import io
import os
import subprocess
import tempfile
from typing import List, Optional, Tuple


# --- Mermaid rendering ---

def render_mermaid(diagram: str, theme: str = "default") -> Optional[bytes]:
    """Render a Mermaid diagram to PNG bytes using mmdc CLI.

    Args:
        diagram: Mermaid diagram source code.
        theme: Mermaid theme name (default, forest, dark, neutral).

    Returns:
        PNG image bytes, or None if rendering failed.
    """
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".mmd", delete=False, encoding="utf-8"
        ) as f:
            f.write(diagram)
            mmd_path = f.name

        png_path = mmd_path + ".png"

        result = subprocess.run(
            ["mmdc", "-i", mmd_path, "-o", png_path,
             "-b", "transparent", "-t", theme],
            capture_output=True, timeout=30,
        )

        os.unlink(mmd_path)

        if result.returncode == 0 and os.path.exists(png_path):
            with open(png_path, "rb") as f:
                data = f.read()
            os.unlink(png_path)
            return data

        if os.path.exists(png_path):
            os.unlink(png_path)
    except Exception:
        pass
    return None


# --- LaTeX rendering ---

def render_latex(latex: str, dpi: int = 150) -> Optional[bytes]:
    """Render LaTeX math to PNG bytes.

    Tries pdflatex + PyMuPDF first, falls back to matplotlib.

    Args:
        latex: LaTeX math expression (without surrounding $$).
        dpi: Render resolution for matplotlib fallback.

    Returns:
        PNG image bytes, or None if rendering failed.
    """
    # Try pdflatex + PyMuPDF pipeline
    result = _render_latex_pdflatex(latex)
    if result is not None:
        return result

    # Fallback to matplotlib
    return _render_latex_matplotlib(latex, dpi)


def _render_latex_pdflatex(latex: str) -> Optional[bytes]:
    """Render LaTeX using pdflatex → PyMuPDF pipeline."""
    try:
        import fitz  # PyMuPDF
    except ImportError:
        return None

    try:
        doc_template = r"""\documentclass[12pt,preview,border=5pt]{standalone}
\usepackage{amsmath,amssymb,amsfonts}
\usepackage[UTF8]{ctex}
\begin{document}
$%s$
\end{document}"""

        with tempfile.TemporaryDirectory() as tmpdir:
            tex_path = os.path.join(tmpdir, "math.tex")
            with open(tex_path, "w", encoding="utf-8") as f:
                f.write(doc_template % latex)

            result = subprocess.run(
                ["pdflatex", "-interaction=nonstopmode", "-output-directory", tmpdir, tex_path],
                capture_output=True, timeout=15,
                cwd=tmpdir,
            )

            pdf_path = os.path.join(tmpdir, "math.pdf")
            if result.returncode == 0 and os.path.exists(pdf_path):
                doc = fitz.open(pdf_path)
                page = doc[0]
                pix = page.get_pixmap(dpi=200)
                data = pix.tobytes("png")
                doc.close()
                return data
    except Exception:
        pass
    return None


def _render_latex_matplotlib(latex: str, dpi: int = 150) -> Optional[bytes]:
    """Render LaTeX using matplotlib (no external deps)."""
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        text = f"${latex}$"
        # Estimate figure size
        w = max(2, len(latex) * 0.15 + 0.5)
        h = 0.8

        fig, ax = plt.subplots(figsize=(w, h))
        ax.text(0.5, 0.5, text, fontsize=14, ha="center", va="center",
                transform=ax.transAxes)
        ax.axis("off")

        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=dpi, bbox_inches="tight", pad_inches=0.1)
        plt.close(fig)
        return buf.getvalue()
    except Exception:
        pass
    return None


# --- Code highlighting (Pygments) ---

def highlight_code(code: str, language: str = "text") -> List[Tuple[str, str]]:
    """Highlight code using Pygments.

    Args:
        code: Source code text.
        language: Programming language identifier.

    Returns:
        List of (text, token_type) tuples for colored rendering.
        Token types include: Keyword, String, Comment, Number, Operator,
        Name, Punctuation, Generic, Text, etc.
    """
    try:
        from pygments import highlight
        from pygments.lexers import get_lexer_by_name, TextLexer
        from pygments.formatters import RawTokenFormatter

        try:
            lexer = get_lexer_by_name(language, stripall=True)
        except Exception:
            lexer = TextLexer()

        tokens = list(lexer.get_tokens(code))
        result = []
        for token_type, text in tokens:
            # Simplify token type to major category
            category = str(token_type).split(".")[0]
            result.append((text, category))
        return result
    except ImportError:
        return [(code, "Text")]


# --- Image utilities ---

def load_image(src: str) -> Optional[bytes]:
    """Load an image from a file path, URL, or base64 data URI.

    Returns raw image bytes.
    """
    if src.startswith("data:"):
        header, b64 = src.split(",", 1)
        return base64.b64decode(b64)
    elif src.startswith(("http://", "https://")):
        import urllib.request
        try:
            return urllib.request.urlopen(src, timeout=10).read()
        except Exception:
            return None
    elif src and os.path.exists(src):
        with open(src, "rb") as f:
            return f.read()
    return None
