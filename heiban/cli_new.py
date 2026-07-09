"""Unified CLI — markdown to DOCX/PPTX/XLSX converter.

Usage::

    python -m heiban input.md -o output.docx    # Auto-detect format by extension
    python -m heiban input.md -o output.pptx
    python -m heiban input.md -o output.xlsx
    python -m heiban input.md -t docx           # Explicit format

    echo "# Hello" | python -m heiban - -o output.docx  # Read from stdin
"""

import argparse
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(
        description="HeiBan — Markdown to Office (DOCX/PPTX/XLSX) converter",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  heiban readme.md -o readme.docx        # Convert to Word
  heiban slides.md -o slides.pptx        # Convert to PowerPoint
  heiban data.md -o data.xlsx            # Convert to Excel
  heiban input.md -o output.docx -f html # Also output HTML preview
  echo "# Title" | heiban - -o out.docx  # Read from stdin
        """,
    )

    parser.add_argument("input", help="Input markdown file (use '-' for stdin)")
    parser.add_argument("-o", "--output", required=True, help="Output file path")
    parser.add_argument(
        "-t", "--type",
        choices=["docx", "pptx", "xlsx"],
        help="Output format (auto-detected from output extension if not specified)",
    )
    parser.add_argument(
        "-f", "--html",
        metavar="HTML_OUTPUT",
        help="Also output reveal.js HTML preview (uses original converter)",
    )
    parser.add_argument(
        "--theme",
        default="default",
        help="Theme name (for HTML output: black, white, league, sky, etc.)",
    )
    parser.add_argument(
        "--version", action="version",
        version="%(prog)s 0.4.0",
    )

    args = parser.parse_args()

    # Determine format
    fmt = args.type
    if fmt is None:
        ext = Path(args.output).suffix.lower().lstrip(".")
        if ext in ("docx", "pptx", "xlsx"):
            fmt = ext
        else:
            print(f"Error: Cannot determine output format from extension '.{ext}'")
            print("Use -t docx/pptx/xlsx to specify format explicitly.")
            sys.exit(1)

    # Read input
    if args.input == "-":
        text = sys.stdin.read()
    else:
        input_path = Path(args.input)
        if not input_path.exists():
            print(f"Error: Input file not found: {args.input}")
            sys.exit(1)
        text = input_path.read_text(encoding="utf-8")

    # Convert
    try:
        if fmt == "docx":
            from heiban.docx import generate_docx
            data = generate_docx(text)
        elif fmt == "pptx":
            from heiban.pptx import generate_pptx
            data = generate_pptx(text)
        elif fmt == "xlsx":
            from heiban.xlsx import generate_xlsx
            data = generate_xlsx(text)
        else:
            print(f"Error: Unknown format: {fmt}")
            sys.exit(1)

        # Write output
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(data)
        print(f"✓ Converted to {fmt.upper()}: {output_path} ({len(data):,} bytes)")

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

    # Optional HTML output
    if args.html:
        try:
            from heiban.v2.converter import MarkdownToSlideConverterV2
            converter = MarkdownToSlideConverterV2(theme=args.theme)
            html = converter.convert(text)
            Path(args.html).write_text(html, encoding="utf-8")
            print(f"✓ HTML preview: {args.html}")
        except ImportError as e:
            print(f"Warning: HTML preview not available: {e}")


if __name__ == "__main__":
    main()
