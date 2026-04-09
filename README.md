# HeiBan - Mermaid转HTML幻灯片生成器

[English](README_EN.md) | 中文

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![PyPI](https://img.shields.io/badge/PyPI-heiban-orange.svg)

一款基于PySide6的桌面应用，用于将Markdown文档（含Mermaid图表）转换为reveal.js格式的HTML幻灯片。

## 特性

- **PySide6 GUI** - 现代化图形界面
- **Markdown支持** - 使用`---`分隔幻灯片
- **Mermaid图表** - 自动识别并渲染流程图、时序图等
- **代码高亮** - 使用highlight.js
- **实时预览** - 浏览器预览功能
- **命令行支持** - 批量转换

## 安装

### 从源码安装

```bash
pip install -e .
```

### 使用预构建包

```bash
pip install heiban
```

## 使用方法

### GUI模式

```bash
heiban --gui
# 或直接运行
heiban
```

### 命令行模式

```bash
# 基本用法
heiban input.md -o output.html

# 指定尺寸和主题
heiban input.md --width 1920 --height 1080 --theme dark

# 查看帮助
heiban --help
```

## Markdown格式

```markdown
# 第1章 标题

## 第一节

- 列表项1
- 列表项2

```
int main() { return 0; }
```

---

## 第二节

```mermaid
flowchart LR
    A --> B
```

```

## 目录结构

```
heiban/
├── __init__.py          # 包初始化
├── __main__.py         # 模块入口
├── cli.py               # 命令行接口
├── converter.py         # 转换器核心
├── gui.py               # GUI界面
└── tests/               # 测试
    └── test_converter.py
```

## 开发

```bash
# 安装开发依赖
pip install -e ".[dev]"

# 运行测试
pytest

# 代码格式化
ruff check .
ruff format .
```

## 上传到PyPI

```bash
# Linux/macOS
./upload_pypi.sh

# Windows
upload_pypi.bat
```

## 依赖

- PySide6 >= 6.5.0

## 许可证

MIT License

## 贡献

欢迎提交Issue和Pull Request！