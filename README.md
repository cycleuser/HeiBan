# HeiBan - Markdown to Slides Generator

English | [中文](README_CN.md)

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![License](https://img.shields.io/badge/License-GPL--3.0-green.svg)
![PyPI](https://img.shields.io/badge/PyPI-heiban-orange.svg)
![Version](https://img.shields.io/badge/Version-0.3.0-blue.svg)

A PySide6-based desktop application that converts Markdown documents into reveal.js HTML slides, with high-quality PPTX and PDF export.

## Features

### Core Features
- **Markdown to Slides** - Use `---` to separate slides, supports headings, lists, code blocks, tables, blockquotes, images
- **Mermaid Diagrams** - Automatically renders flowcharts, sequence diagrams, Gantt charts, etc.
- **Code Highlighting** - GitHub-style syntax highlighting for 100+ programming languages
- **Math Formulas** - Full LaTeX math support (`$...$` inline, `$$...$$` display) rendered as high-quality images via pdflatex

### PPTX Export (New in v0.3)
- **LaTeX Math Rendering** - pdflatex + PyMuPDF pipeline renders math as crisp, resolution-independent images; matplotlib fallback for systems without pdflatex
- **GitHub-style Syntax Highlighting** - Pygments-based token-level coloring matching GitHub dark/light themes
- **Mermaid Chart Rendering** - mmdc renders Mermaid diagrams as images; auto-fixes node labels with special characters
- **12 Built-in Themes** - black, white, dracula, league, beige, sky, night, moon, solarized, blood, serif, simple
- **Dual-Column Layout** - Automatically splits into two columns when content is dense, instead of shrinking fonts
- **Open Source Typography** - Source Sans 3 for body/heading, Source Code Pro for code (both SIL Open Font License)
- **Unified Type Scale** - All font sizes derived from a single base (18pt default) with consistent ratios
- **Table Math** - LaTeX commands in table cells are converted to Unicode with italic accent styling

### Theme Support
- **Dark/Light Themes** - Complete dark and light theme support
- **12 Themes** - black, white, dracula, league, beige, sky, night, moon, solarized, blood, serif, simple
- **Custom Settings** - Adjustable font size, aspect ratio, Mermaid themes, etc.

### Export Features
- **HTML Export** - Generates self-contained HTML files with no external dependencies
- **PPTX Export** - High-quality PowerPoint export with real math rendering, syntax highlighting, and Mermaid diagrams
- **PDF Export** - Uses Qt built-in functionality or Playwright to generate PDF, preserving all styles
- **Auto Pagination** - Each slide automatically becomes one page

## Installation

### Install from PyPI

```bash
pip install heiban
```

### Full PPTX quality (optional)

```bash
pip install heiban[pptx-hq]
```

This installs PyMuPDF for high-quality math rendering. Without it, matplotlib is used as fallback. You also need `pdflatex` (TeX Live or MiKTeX) and `mmdc` (mermaid-cli) for best results.

### Install from Source

```bash
git clone https://github.com/cycleuser/HeiBan.git
cd HeiBan
pip install -e ".[dev]"
```

## Usage

### GUI Mode

```bash
heiban
```

### Command Line Mode

```bash
# Export HTML
heiban input.md -o output.html

# Export PPTX
heiban input.md --pptx output.pptx

# Export PDF
heiban input.md --pdf output.pdf

# Specify theme
heiban input.md --pptx output.pptx --theme dracula

# Show help
heiban --help
```

## Markdown Format Example

```markdown
# Presentation Title

## Slide 1: Lists and Code

- Item 1
- Item 2
- Item 3

```python
def hello():
    print("Hello, World!")
```

---

## Slide 2: Mermaid Diagram

```mermaid
flowchart LR
    A[Start] --> B[Process]
    B --> C[End]
```

---

## Slide 3: Tables and Formulas

| Item | Quantity | Price |
|------|----------|-------|
| A    | 10       | $100  |
| B    | 20       | $200  |

Math formula: $E = mc^2$

$$
\int_0^\infty e^{-x^2} dx = \frac{\sqrt{\pi}}{2}
$$
```

## Project Structure

```
heiban/
├── heiban/
│   ├── __init__.py          # Package initialization
│   ├── cli.py               # Command-line interface
│   ├── gui.py                # GUI interface
│   ├── converter.py          # v1 converter
│   ├── pptx_exporter.py      # PPTX export engine
│   ├── pdf_exporter.py       # PDF export engine
│   ├── v2/
│   │   ├── md_parser.py      # Markdown parser
│   │   └── converter.py      # v2 HTML converter
│   └── data/
│       └── lib/             # JS/CSS resources
├── tests/                   # Test files
├── pyproject.toml           # Project configuration
└── README.md               # Documentation
```

## Technology Stack

### Frontend
- **reveal.js** - Slideshow framework
- **Mermaid** - Diagram rendering
- **highlight.js** - Code highlighting
- **KaTeX** - Math formula rendering

### Backend
- **Python 3.8+** - Core language
- **PySide6** - Qt GUI framework
- **python-pptx** - PPTX generation
- **Pygments** - Syntax highlighting for PPTX
- **pdflatex + PyMuPDF** - LaTeX math rendering for PPTX

## Development

### Install Development Dependencies

```bash
pip install -e ".[dev]"
```

### Run Tests

```bash
pytest tests/ -v
```

### Code Checking

```bash
ruff check .
ruff format .
```

## Requirements

- Python >= 3.8
- PySide6 >= 6.5.0
- Pygments >= 2.15.0
- Pillow >= 9.0.0
- python-pptx >= 0.6.23

### Optional (for best PPTX quality)
- PyMuPDF >= 1.23.0
- pdflatex (TeX Live or MiKTeX)
- mmdc (mermaid-cli)

## Changelog

### v0.3.0 (2026-06-08)
- **New**: Full PPTX export engine with math/code/mermaid rendering
- **New**: pdflatex + PyMuPDF pipeline for high-quality LaTeX math as images
- **New**: GitHub-style Pygments syntax highlighting in PPTX
- **New**: Mermaid diagram rendering via mmdc, with auto-fix for special chars
- **New**: 12 built-in themes (black, white, dracula, league, beige, sky, night, moon, solarized, blood, serif, simple)
- **New**: Automatic dual-column layout for dense content
- **New**: Source Sans 3 + Source Code Pro open-source typography
- **New**: Unified type scale from single base font size
- **New**: Table math with LaTeX-to-Unicode conversion + italic accent
- **Fix**: Element ordering preserved in document order
- **Fix**: Image aspect ratio preserved in all contexts
- **Fix**: Mermaid node labels with `()` auto-quoted for parsing
- **Fix**: `<pre>` no longer matched as `<p>` in HTML parsing

### v0.2.0 (2026-04-09)
- v2 converter with improved Markdown parser
- PDF export improvements

### v0.1.33 (2026-04-09)
- Fixed QTextDocument print method name
- Improved PDF export functionality

## License

GPL-3.0-or-later

## Contributing

Issues and Pull Requests are welcome!

## Contact

- Project: https://github.com/cycleuser/HeiBan
- Issues: https://github.com/cycleuser/HeiBan/issues