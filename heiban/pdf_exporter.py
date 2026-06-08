"""PDF 导出器 - 支持多种后端

优先级: WeasyPrint (轻量) > Playwright (高质量, JS 完整渲染)
两者自动检测安装情况。

关键: Playwright 模式使用 reveal.js ?print-pdf，等待 KaTeX/Mermaid JS 完成渲染后才导出。
"""

from pathlib import Path
from typing import Optional


def _detect_backend() -> str:
    try:
        import weasyprint  # noqa: F401
        return "weasyprint"
    except ImportError:
        pass
    try:
        from playwright.sync_api import sync_playwright  # noqa: F401
        return "playwright"
    except ImportError:
        pass
    return "none"


class PDFExporter:
    """PDF 导出器

    WeasyPrint: 轻量, 无 JS 执行, 适合纯文本/表格幻灯片
    Playwright: 完整 JS 执行, KaTeX/Mermaid 完美渲染, 使用 reveal.js print-pdf 模式
    """

    def __init__(self, backend: Optional[str] = None):
        self.paper_size = "A4"
        self.landscape = True
        self.margin = {"top": "0", "bottom": "0", "left": "0", "right": "0"}
        self.print_background = True
        self.wait_time = 8000

        if backend is None:
            self._backend = _detect_backend()
        elif backend in ("weasyprint", "playwright"):
            self._backend = backend
        else:
            self._backend = _detect_backend()

    @property
    def backend_name(self) -> str:
        return self._backend

    def export_html_file(
        self, html_path: str, output_path: Optional[str] = None, wait_time: Optional[int] = None
    ) -> str:
        html_path = Path(html_path)
        if not html_path.exists():
            raise FileNotFoundError(f"HTML 文件不存在: {html_path}")

        if output_path is None:
            output_path = str(html_path.with_suffix(".pdf"))

        output_p = Path(output_path)
        output_p.parent.mkdir(parents=True, exist_ok=True)

        html_content = html_path.read_text(encoding="utf-8")
        html_content = self._prepare_html_for_pdf(html_content)

        if self._backend == "weasyprint":
            return self._export_weasyprint(html_content, output_p)
        elif self._backend == "playwright":
            actual_wait = wait_time if wait_time is not None else self.wait_time
            prepared_path = self._write_temp_html(html_content, output_p.parent)
            try:
                return self._export_playwright(prepared_path, output_p, actual_wait)
            finally:
                prepared_path.unlink(missing_ok=True)
        else:
            raise RuntimeError(
                "无可用的 PDF 后端。请安装:\n"
                "  pip install weasyprint      (轻量推荐)\n"
                "  pip install playwright && playwright install chromium  (高质量)"
            )

    def export_html_content(
        self, html_content: str, output_path: str, wait_time: Optional[int] = None
    ) -> str:
        output_p = Path(output_path)
        output_p.parent.mkdir(parents=True, exist_ok=True)

        html_content = self._prepare_html_for_pdf(html_content)

        if self._backend == "weasyprint":
            return self._export_weasyprint(html_content, output_p)
        else:
            prepared_path = self._write_temp_html(html_content, output_p.parent)
            try:
                actual_wait = wait_time if wait_time is not None else self.wait_time
                return self._export_playwright(prepared_path, output_p, actual_wait)
            finally:
                prepared_path.unlink(missing_ok=True)

    def export_from_converter(
        self, converter, md_content: str, output_path: str,
        title: str = "Presentation", use_cdn: bool = False, wait_time: Optional[int] = None,
    ) -> str:
        output_p = Path(output_path)
        output_p.parent.mkdir(parents=True, exist_ok=True)

        html_content = converter.convert(md_content, title=title, use_cdn=use_cdn)
        html_content = self._prepare_html_for_pdf(html_content)

        if self._backend == "weasyprint":
            return self._export_weasyprint(html_content, output_p)
        else:
            prepared_path = self._write_temp_html(html_content, output_p.parent)
            try:
                actual_wait = wait_time if wait_time is not None else self.wait_time
                return self._export_playwright(prepared_path, output_p, actual_wait)
            finally:
                prepared_path.unlink(missing_ok=True)

    def _write_temp_html(self, html_content: str, parent: Path) -> Path:
        tmp = parent / "_heiban_pdf_temp.html"
        tmp.write_text(html_content, encoding="utf-8")
        return tmp

    def _prepare_html_for_pdf(self, html_content: str) -> str:
        pdf_css = """
<style>
@media print {
    .reveal .slides section {
        page-break-after: always !important;
        page-break-inside: avoid !important;
    }
    .reveal .slides section:last-child {
        page-break-after: avoid !important;
    }
    html, body, .reveal, .reveal-viewport {
        -webkit-print-color-adjust: exact !important;
        color-adjust: exact !important;
        print-color-adjust: exact !important;
    }
    .reveal .progress, .reveal .controls, .reveal .slide-number {
        display: none !important;
    }
}
</style>
"""
        if "</head>" in html_content:
            html_content = html_content.replace("</head>", pdf_css + "\n</head>")
        return html_content

    def _export_weasyprint(self, html_content: str, output_path: Path) -> str:
        try:
            from weasyprint import CSS, HTML
        except ImportError:
            raise ImportError("WeasyPrint 未安装。请运行: pip install weasyprint") from None

        orientation = "landscape" if self.landscape else "portrait"
        base_css = CSS(
            string=f"""
@page {{
    size: A4 {orientation};
    margin: 0;
}}
.reveal .slides section {{
    page-break-after: always;
    page-break-inside: avoid;
}}
.reveal .slides section:last-child {{
    page-break-after: avoid;
}}
.reveal .progress, .reveal .controls, .reveal .slide-number {{
    display: none;
}}
.reveal .slides {{
    position: static !important;
    width: 100% !important;
    height: auto !important;
    overflow: visible !important;
    transform: none !important;
}}
.reveal .slides section {{
    position: relative !important;
    display: block !important;
    width: 100% !important;
    height: auto !important;
    overflow: visible !important;
    visibility: visible !important;
    opacity: 1 !important;
    transform: none !important;
    margin: 0 !important;
    padding: 1em !important;
}}
"""
        )

        html_doc = HTML(string=html_content, base_url=str(output_path.parent))
        html_doc.write_pdf(str(output_path), stylesheets=[base_css])
        return str(output_path)

    def _export_playwright(self, html_path: Path, output_path: Path, wait_time: int) -> str:
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            raise ImportError(
                "Playwright 未安装。请运行: pip install playwright && playwright install chromium"
            ) from None

        file_url = html_path.resolve().as_uri()

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(viewport={"width": 1920, "height": 1080})
            page = context.new_page()

            page.goto(file_url, wait_until="load", timeout=60000)
            page.wait_for_timeout(3000)

            force_render_js = """() => {
                try {
                    if (typeof renderMathInElement !== 'undefined') {
                        renderMathInElement(document.body, {
                            delimiters: [
                                {left: '$$', right: '$$', display: true},
                                {left: '$', right: '$', display: false},
                                {left: '\\\\[', right: '\\\\]', display: true},
                                {left: '\\\\(', right: '\\\\)', display: false}
                            ],
                            throwOnError: false
                        });
                    }
                } catch(e) {}
                try {
                    if (typeof mermaid !== 'undefined') {
                        mermaid.initialize({ startOnLoad: false, securityLevel: 'loose' });
                        const els = document.querySelectorAll('.mermaid');
                        els.forEach(el => {
                            try {
                                const id = 'mermaid-' + Math.random().toString(36).substr(2, 9);
                                const svg = mermaid.render(id, el.textContent);
                                el.innerHTML = svg;
                            } catch(e) {}
                        });
                    }
                } catch(e) {}
                try {
                    if (typeof hljs !== 'undefined') {
                        hljs.highlightAll();
                    }
                } catch(e) {}
            }"""

            page.evaluate(force_render_js)
            page.wait_for_timeout(3000)

            pdf_url = f"{file_url}?print-pdf"
            page.goto(pdf_url, wait_until="load", timeout=60000)
            page.wait_for_timeout(2000)

            page.evaluate(force_render_js)
            page.wait_for_timeout(2000)

            width_val = "11in" if self.landscape else "8.27in"
            height_val = "8.5in" if self.landscape else "11.69in"

            page.pdf(
                path=str(output_path),
                width=width_val,
                height=height_val,
                margin=self.margin,
                print_background=self.print_background,
                prefer_css_page_size=True,
            )
            browser.close()

        return str(output_path)


def export_pdf(html_path: str, output_path: Optional[str] = None,
                landscape: bool = True, wait_time: int = 8000) -> str:
    exporter = PDFExporter()
    exporter.landscape = landscape
    exporter.wait_time = wait_time
    return exporter.export_html_file(html_path, output_path)
