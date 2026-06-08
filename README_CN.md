# HeiBan - Markdown 转幻灯片生成器

[English](README.md) | 中文

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![License](https://img.shields.io/badge/License-GPL--3.0-green.svg)
![PyPI](https://img.shields.io/badge/PyPI-heiban-orange.svg)
![Version](https://img.shields.io/badge/Version-0.3.0-blue.svg)

一款基于 PySide6 的桌面应用，将 Markdown 文档转换为 reveal.js HTML 幻灯片，并支持高质量 PPTX 和 PDF 导出。

## 特性

### 核心功能
- **Markdown 转幻灯片** - 使用 `---` 分隔幻灯片，支持标题、列表、代码块、表格、引用块、图片
- **Mermaid 图表** - 自动识别并渲染流程图、时序图、甘特图等
- **代码高亮** - GitHub 风格语法高亮，支持 100+ 编程语言
- **数学公式** - 完整 LaTeX 数学支持（`$...$` 行内、`$$...$$` 独立显示），通过 pdflatex 渲染为高质量图片

### PPTX 导出（v0.3 全新）
- **LaTeX 数学渲染** - pdflatex + PyMuPDF 管线：LaTeX → PDF → 高清 PNG，无 pdflatex 时自动 fallback 到 matplotlib
- **GitHub 风格语法高亮** - 基于 Pygments 的逐 token 着色，完美匹配 GitHub 暗色/亮色主题
- **Mermaid 图表渲染** - mmdc 渲染为 PNG；含特殊字符的节点标签自动加引号修复
- **12 套内置主题** - black, white, dracula, league, beige, sky, night, moon, solarized, blood, serif, simple
- **双列自动布局** - 内容密集时自动分双列，而非缩小字体
- **开源字体** - 正文/标题用 Source Sans 3，代码用 Source Code Pro（均 SIL 开源协议）
- **统一排版比例** - 所有字号基于单一基础字号（默认 18pt）的比例派生
- **表格公式** - 表格单元格中的 LaTeX 命令转为 Unicode + 斜体强调色

### 主题支持
- **暗色/亮色主题** - 完整的深色和浅色主题支持
- **12 套主题** - black, white, dracula, league, beige, sky, night, moon, solarized, blood, serif, simple
- **自定义设置** - 可调整字体大小、宽高比、Mermaid 主题等

### 导出功能
- **HTML 导出** - 生成自包含的 HTML 文件，无外部依赖
- **PPTX 导出** - 高质量 PowerPoint 导出：真实数学渲染、语法高亮、Mermaid 图表
- **PDF 导出** - 使用 Qt 内置功能或 Playwright 生成 PDF，保留所有样式
- **自动分页** - 每张幻灯片自动分成一页

## 安装

### 从 PyPI 安装

```bash
pip install heiban
```

### 最佳 PPTX 质量（可选）

```bash
pip install heiban[pptx-hq]
```

安装 PyMuPDF 以获取高质量数学渲染。缺省时使用 matplotlib fallback。还需 `pdflatex`（TeX Live 或 MiKTeX）和 `mmdc`（mermaid-cli）以获得最佳效果。

### 从源码安装

```bash
git clone https://github.com/cycleuser/HeiBan.git
cd HeiBan
pip install -e ".[dev]"
```

## 使用方法

### GUI 模式

```bash
heiban
```

### 命令行模式

```bash
# 导出 HTML
heiban input.md -o output.html

# 导出 PPTX
heiban input.md --pptx output.pptx

# 导出 PDF
heiban input.md --pdf output.pdf

# 指定主题
heiban input.md --pptx output.pptx --theme dracula

# 查看帮助
heiban --help
```

## 更新日志

### v0.3.0 (2026-06-08)
- **新增**：完整 PPTX 导出引擎，支持数学/代码/Mermaid 渲染
- **新增**：pdflatex + PyMuPDF 管线：LaTeX → PDF → 高清 PNG
- **新增**：GitHub 风格 Pygments 语法高亮
- **新增**：Mermaid 图表通过 mmdc 渲染，含特殊字符的标签自动修复
- **新增**：12 套内置主题
- **新增**：内容密集时自动双列布局
- **新增**：Source Sans 3 + Source Code Pro 开源字体
- **新增**：统一排版比例体系
- **新增**：表格中 LaTeX→Unicode 转换 + 斜体强调
- **修复**：元素按文档顺序排列（不再标题和正文分组）
- **修复**：图片宽高比在所有上下文中保持
- **修复**：Mermaid 节点标签含 `()` 自动加引号
- **修复**：`<pre>` 不再被误匹配为 `<p>`

### v0.2.0 (2026-04-09)
- v2 转换器及改进的 Markdown 解析器
- PDF 导出改进

## 许可证

GPL-3.0-or-later

## 贡献

欢迎提交 Issue 和 Pull Request！

## 联系方式

- 项目地址：https://github.com/cycleuser/HeiBan
- 问题反馈：https://github.com/cycleuser/HeiBan/issues