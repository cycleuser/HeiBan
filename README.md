# HeiBan - Markdown to HTML Slides Generator

English | [中文](README.md)

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![License](https://img.shields.io/badge/License-GPL--3.0-green.svg)
![PyPI](https://img.shields.io/badge/PyPI-heiban-orange.svg)
![Version](https://img.shields.io/badge/Version-0.1.33-blue.svg)

A PySide6-based desktop application that converts Markdown documents (with Mermaid diagrams) into reveal.js HTML slides and supports PDF export.

## Features

### Core Features
- **Markdown to Slides** - Use `---` to separate slides, supports headings, lists, code blocks, tables, etc.
- **Mermaid Diagrams** - Automatically renders flowcharts, sequence diagrams, Gantt charts, etc.
- **Code Highlighting** - GitHub-style syntax highlighting for multiple programming languages
- **Math Formulas** - KaTeX support for mathematical expressions (`$...$` and `$$...$$`)

### Theme Support
- **Dark/Light Themes** - Complete dark and light theme support
- **Custom Settings** - Adjustable font size, aspect ratio, Mermaid themes, etc.
- **Style Preservation** - PDF export preserves all styles (background colors, text colors, etc.)

### Export Features
- **HTML Export** - Generates self-contained HTML files with no external dependencies
- **PDF Export** - Uses Qt built-in functionality to generate PDF, preserving all styles
- **Auto Pagination** - Each slide automatically becomes one page

## Installation

### Install from PyPI

```bash
pip install heiban
```

### Install from Source

```bash
git clone https://github.com/yourusername/HeiBan.git
cd HeiBan
pip install -e .
```

## Usage

### GUI Mode

```bash
heiban
```

#### GUI Features

1. **Open Markdown File** - Load `.md` files
2. **Save HTML File** - Export as self-contained HTML slides
3. **Export PDF** - Generate PDF files with perfect style preservation

#### Settings Menu

- **Aspect Ratio** - 16:9 (widescreen), 4:3 (standard), 21:9 (ultrawide), 3:2 (standard)
- **Font Size** - 16px to 40px
- **Mermaid Theme** - default, neutral, dark, base
- **Code Highlight Theme** - dark, light

### Command Line Mode

```bash
# Basic usage
heiban input.md -o output.html

# Specify dimensions
heiban input.md --width 1920 --height 1080

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
│   ├── converter.py         # Core converter
│   ├── gui.py               # GUI interface
│   └── data/
│       └── lib/             # JS/CSS resources
│           ├── js/
│           │   ├── reveal.min.js
│           │   ├── mermaid.min.js
│           │   ├── highlight.min.js
│           │   └── katex.min.js
│           └── css/
│               ├── reveal.min.css
│               ├── katex.min.css
│               └── ...
├── tests/                   # Test files
├── pyproject.toml          # Project configuration
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
- **Qt Print Support** - PDF generation

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

## Known Limitations

1. **PDF Export** - No support for JavaScript animations, Mermaid diagrams need pre-rendering
2. **Resource Size** - Generated HTML files are large (~4MB) as they contain all JS/CSS resources
3. **Browser Compatibility** - Modern browsers recommended (Chrome, Firefox, Safari)

## Changelog

### v0.1.33 (2026-04-09)
- Fixed QTextDocument print method name (print_ instead of print)
- Improved PDF export functionality

### v0.1.32 (2026-04-09)
- Fixed PDF export enum type error
- Improved Qt printing functionality
- Better error handling

### v0.1.30 (2026-04-09)
- Simplified GUI interface, removed preview tab
- Use Qt QTextDocument for PDF generation
- Improved documentation

## License

GPL-3.0-or-later

## Contributing

Issues and Pull Requests are welcome!

## Contact

- Project: https://github.com/yourusername/HeiBan
- Issues: https://github.com/yourusername/HeiBan/issues