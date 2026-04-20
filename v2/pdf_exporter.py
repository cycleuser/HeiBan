"""基于 Playwright 的矢量完美 PDF 导出器"""

import tempfile
from pathlib import Path


class PDFExporter:
    """使用 Playwright (Chromium) 导出矢量完美 PDF

    优势:
    - 完整 JavaScript 执行 (Mermaid, KaTeX, reveal.js)
    - 矢量字体渲染 (KaTeX 数学公式)
    - 矢量 SVG 图形 (Mermaid 图表)
    - 使用 reveal.js print-pdf 模式，完美分页
    - 支持暗色/亮色主题
    """

    def __init__(self):
        self.paper_size = "A4"
        self.landscape = True
        self.margin = {"top": "0", "bottom": "0", "left": "0", "right": "0"}
        self.print_background = True
        self.wait_time = 3000

    def export_html_file(
        self, html_path: str, output_path: str | None = None, wait_time: int | None = None
    ) -> str:
        """从 HTML 文件导出 PDF

        Args:
            html_path: 输入的 HTML 文件路径
            output_path: 输出的 PDF 文件路径，默认为同名 .pdf
            wait_time: 等待渲染的时间（毫秒），默认 3000ms

        Returns:
            输出的 PDF 文件路径
        """
        html_path = Path(html_path)
        if not html_path.exists():
            raise FileNotFoundError(f"HTML 文件不存在: {html_path}")

        if output_path is None:
            output_path = str(html_path.with_suffix(".pdf"))

        output_p = Path(output_path)
        output_p.parent.mkdir(parents=True, exist_ok=True)

        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            raise ImportError(
                "Playwright 未安装。请运行: pip install playwright && playwright install chromium"
            ) from None

        file_url = html_path.resolve().as_uri()
        pdf_url = f"{file_url}?print-pdf"

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                viewport={
                    "width": self.width if hasattr(self, "width") else 1920,
                    "height": self.height if hasattr(self, "height") else 1080,
                },
            )
            page = context.new_page()

            page.goto(pdf_url, wait_until="networkidle", timeout=60000)

            actual_wait = wait_time if wait_time is not None else self.wait_time
            page.wait_for_timeout(actual_wait)

            page.pdf(
                path=str(output_p),
                format="A4" if not self.landscape else None,
                width="11in" if self.landscape else "8.27in",
                height="8.5in" if self.landscape else "11.69in",
                margin=self.margin,
                print_background=self.print_background,
                prefer_css_page_size=True,
            )

            browser.close()

        return str(output_p)

    def export_html_content(
        self, html_content: str, output_path: str, wait_time: int | None = None
    ) -> str:
        """从 HTML 内容导出 PDF

        Args:
            html_content: HTML 内容字符串
            output_path: 输出的 PDF 文件路径
            wait_time: 等待渲染的时间（毫秒）

        Returns:
            输出的 PDF 文件路径
        """
        output_p = Path(output_path)
        output_p.parent.mkdir(parents=True, exist_ok=True)

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".html", delete=False, encoding="utf-8"
        ) as f:
            f.write(html_content)
            temp_html = f.name

        try:
            return self.export_html_file(temp_html, output_path, wait_time)
        finally:
            Path(temp_html).unlink(missing_ok=True)

    def export_from_converter(
        self,
        converter,
        md_content: str,
        output_path: str,
        title: str = "演示文稿",
        use_cdn: bool = False,
        wait_time: int | None = None,
    ) -> str:
        """从 Markdown 内容直接导出 PDF

        Args:
            converter: MarkdownToSlideConverterV2 实例
            md_content: Markdown 内容
            output_path: 输出的 PDF 文件路径
            title: 演示文稿标题
            use_cdn: 是否使用 CDN 模式生成中间 HTML
            wait_time: 等待渲染的时间（毫秒）

        Returns:
            输出的 PDF 文件路径
        """
        output_p = Path(output_path)
        output_p.parent.mkdir(parents=True, exist_ok=True)

        html_content = converter.convert(md_content, title=title, use_cdn=use_cdn)

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".html", delete=False, encoding="utf-8"
        ) as f:
            f.write(html_content)
            temp_html = f.name

        try:
            return self.export_html_file(temp_html, output_path, wait_time)
        finally:
            Path(temp_html).unlink(missing_ok=True)


def export_pdf(
    html_path: str, output_path: str | None = None, landscape: bool = True, wait_time: int = 3000
) -> str:
    """便捷函数：直接从 HTML 文件导出 PDF

    Args:
        html_path: 输入的 HTML 文件路径
        output_path: 输出的 PDF 文件路径
        landscape: 是否横向
        wait_time: 等待渲染的时间（毫秒）

    Returns:
        输出的 PDF 文件路径
    """
    exporter = PDFExporter()
    exporter.landscape = landscape
    exporter.wait_time = wait_time
    return exporter.export_html_file(html_path, output_path)
