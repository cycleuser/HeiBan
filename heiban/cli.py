#!/usr/bin/env python3
"""
HeiBan CLI - 命令行接口
"""

import sys
import argparse
from pathlib import Path

from .converter import MarkdownToSlideConverter
from .gui import run_gui


def main():
    """命令行入口"""
    parser = argparse.ArgumentParser(
        description="HeiBan - Markdown 转 reveal.js 幻灯片生成器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s input.md -o output.html
  %(prog)s input.md --v2 -o output.html
  %(prog)s input.md --v2 --pdf output.pdf
  %(prog)s input.md --width 1920 --height 1080
  %(prog)s --gui

v2 新功能:
  - 完整 GFM Markdown 支持 (表格、任务列表、删除线、脚注等)
  - 垂直幻灯片 (使用 ---- 分隔)
  - 幻灯片属性 (背景、转场等)
  - Fragment 动画
  - 演讲者备注
  - 矢量完美 PDF 导出 (基于 Playwright)
        """,
    )

    parser.add_argument("input", nargs="?", help="输入的Markdown文件")
    parser.add_argument("-o", "--output", help="输出的HTML文件")
    parser.add_argument("--width", type=int, default=1280, help="幻灯片宽度 (默认: 1280)")
    parser.add_argument("--height", type=int, default=720, help="幻灯片高度 (默认: 720)")
    parser.add_argument("--font-size", type=int, default=26, help="字体大小 (默认: 26)")
    parser.add_argument(
        "--theme",
        choices=["default", "neutral", "dark", "base"],
        default="default",
        help="Mermaid主题 (默认: default)",
    )
    parser.add_argument("--gui", action="store_true", help="启动GUI界面")

    v2_group = parser.add_argument_group("v2 选项")
    v2_group.add_argument("--v2", action="store_true", help="使用 v2 转换器 (推荐)")
    v2_group.add_argument(
        "--reveal-theme",
        choices=[
            "black",
            "white",
            "league",
            "beige",
            "sky",
            "night",
            "serif",
            "simple",
            "solarized",
            "blood",
            "moon",
        ],
        default="black",
        help="reveal.js 主题 (v2, 默认: black)",
    )
    v2_group.add_argument(
        "--transition",
        choices=["none", "fade", "slide", "convex", "concave", "zoom"],
        default="slide",
        help="转场效果 (v2, 默认: slide)",
    )
    v2_group.add_argument(
        "--aspect-ratio",
        choices=["16:9", "4:3", "21:9", "3:2"],
        default="16:9",
        help="宽高比 (v2, 默认: 16:9)",
    )
    v2_group.add_argument("--cdn", action="store_true", help="使用 CDN 链接 (v2)")
    v2_group.add_argument("--pdf", help="导出为 PDF (v2, 需要 Playwright)")
    v2_group.add_argument(
        "--pdf-wait",
        type=int,
        default=3000,
        help="PDF 导出等待渲染时间/毫秒 (v2, 默认: 3000)",
    )
    v2_group.add_argument(
        "--landscape",
        action="store_true",
        default=True,
        help="PDF 横向 (v2, 默认)",
    )
    v2_group.add_argument(
        "--portrait",
        action="store_true",
        help="PDF 纵向 (v2)",
    )

    args = parser.parse_args()

    if args.gui or args.input is None:
        run_gui()
        return 0

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"错误: 文件不存在 '{args.input}'", file=sys.stderr)
        return 1

    if args.v2:
        return _run_v2(input_path, args)
    else:
        return _run_v1(input_path, args)


def _run_v1(input_path: Path, args) -> int:
    """运行 v1 转换器"""
    converter = MarkdownToSlideConverter()
    converter.width = args.width
    converter.height = args.height
    converter.font_size = args.font_size
    converter.mermaid_theme = args.theme

    output_path = converter.convert_file(str(input_path), args.output)
    print(f"转换完成: {output_path}")
    return 0


def _run_v2(input_path: Path, args) -> int:
    """运行 v2 转换器"""
    from .v2.converter import MarkdownToSlideConverterV2

    converter = MarkdownToSlideConverterV2()
    converter.set_aspect_ratio(args.aspect_ratio)
    converter.font_size = args.font_size
    converter.theme = args.reveal_theme
    converter.transition = args.transition

    html_output = args.output
    if html_output is None:
        html_output = str(input_path.with_suffix(".html"))

    converter.image_base_path = input_path.parent
    html_content = converter.convert(
        input_path.read_text(encoding="utf-8"),
        title=input_path.stem,
        use_cdn=args.cdn,
    )

    Path(html_output).write_text(html_content, encoding="utf-8")
    print(f"HTML 转换完成: {html_output}")

    if args.pdf:
        from .v2.pdf_exporter import PDFExporter

        exporter = PDFExporter()
        exporter.landscape = not args.portrait
        exporter.wait_time = args.pdf_wait

        pdf_path = exporter.export_html_file(html_output, args.pdf)
        print(f"PDF 导出完成: {pdf_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
