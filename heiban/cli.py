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
        description="HeiBan - Mermaid转HTML幻灯片生成器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s input.md -o output.html
  %(prog)s input.md --width 1920 --height 1080
  %(prog)s --gui

使用 %%mermaid 分隔图表:
  ```mermaid
  flowchart LR
      A --> B
  ```
        """,
    )

    parser.add_argument("input", nargs="?", help="输入的Markdown文件")
    parser.add_argument("-o", "--output", help="输出的HTML文件")
    parser.add_argument(
        "--width", type=int, default=1280, help="幻灯片宽度 (默认: 1280)"
    )
    parser.add_argument(
        "--height", type=int, default=720, help="幻灯片高度 (默认: 720)"
    )
    parser.add_argument("--font-size", type=int, default=26, help="字体大小 (默认: 26)")
    parser.add_argument(
        "--theme",
        choices=["default", "neutral", "dark", "base"],
        default="default",
        help="Mermaid主题 (默认: default)",
    )
    parser.add_argument("--gui", action="store_true", help="启动GUI界面")

    args = parser.parse_args()

    # 如果指定了 --gui 或者没有输入文件，启动GUI
    if args.gui or args.input is None:
        run_gui()
        return 0

    # 命令行模式转换
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"错误: 文件不存在 '{args.input}'", file=sys.stderr)
        return 1

    converter = MarkdownToSlideConverter()
    converter.width = args.width
    converter.height = args.height
    converter.font_size = args.font_size
    converter.mermaid_theme = args.theme

    output_path = converter.convert_file(str(input_path), args.output)
    print(f"转换完成: {output_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
