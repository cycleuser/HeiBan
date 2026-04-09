#!/usr/bin/env python3
"""
HeiBan测试 - converter模块
"""

import pytest
from heiban.converter import MarkdownToSlideConverter


class TestConverter:
    """转换器测试"""

    def setup_method(self):
        """每个测试方法前运行"""
        self.converter = MarkdownToSlideConverter()

    def test_simple_heading(self):
        """测试简单标题转换"""
        md = """# 主标题

## 二级标题
"""
        result = self.converter.generate_html(md, "测试")
        assert "<h1>主标题</h1>" in result
        assert "<h2>二级标题</h2>" in result

    def test_code_block(self):
        """测试代码块转换"""
        md = """# 标题

```c
int main() { return 0; }
```
"""
        result = self.converter.generate_html(md, "测试")
        assert 'class="language-c"' in result
        assert "int main() { return 0; }" in result

    def test_list(self):
        """测试列表转换"""
        md = """# 标题

- 第一项
- 第二项
- 第三项
"""
        result = self.converter.generate_html(md, "测试")
        assert "<ul>" in result
        assert "<li>第一项</li>" in result
        assert "<li>第二项</li>" in result

    def test_inline_code(self):
        """测试行内代码转换"""
        md = """# 标题

这是 `inline code` 示例
"""
        result = self.converter.generate_html(md, "测试")
        assert "<code>inline code</code>" in result

    def test_inline_bold(self):
        """测试粗体转换"""
        md = """# 标题

这是 **bold text** 示例
"""
        result = self.converter.generate_html(md, "测试")
        assert "<strong>bold text</strong>" in result

    def test_slide_separator(self):
        """测试幻灯片分隔"""
        md = """# 第一页

内容1

---

# 第二页

内容2
"""
        result = self.converter.generate_html(md, "测试")
        assert result.count("<section>") == 2

    def test_table(self):
        """测试表格转换"""
        md = """| 姓名 | 年龄 |
|------|------|
| 张三 | 20 |
| 李四 | 25 |
"""
        result = self.converter.generate_html(md, "测试")
        assert "<table>" in result
        assert "<th>姓名</th>" in result
        assert "<td>张三</td>" in result

    def test_mermaid(self):
        """测试Mermaid图表"""
        md = """# 标题

```mermaid
flowchart LR
    A --> B
```
"""
        result = self.converter.generate_html(md, "测试")
        assert 'class="mermaid"' in result
        assert "flowchart LR" in result

    def test_custom_size(self):
        """测试自定义尺寸"""
        self.converter.width = 1920
        self.converter.height = 1080
        md = "# 标题"
        result = self.converter.generate_html(md, "测试")
        assert "width: 1920" in result
        assert "height: 1080" in result

    def test_custom_font_size(self):
        """测试自定义字体大小"""
        self.converter.font_size = 32
        md = "# 标题"
        result = self.converter.generate_html(md, "测试")
        assert "font-size: 32px" in result


class TestConverterParse:
    """转换器解析测试"""

    def setup_method(self):
        self.converter = MarkdownToSlideConverter()

    def test_parse_empty(self):
        """测试空输入"""
        slides = self.converter.parse_markdown("")
        assert len(slides) == 0

    def test_parse_single_slide(self):
        """测试单个幻灯片"""
        md = "# 标题\n\n内容"
        slides = self.converter.parse_markdown(md)
        assert len(slides) == 1

    def test_parse_multiple_slides(self):
        """测试多个幻灯片"""
        md = """# 第一页

内容1

---

# 第二页

内容2

---

# 第三页

内容3
"""
        slides = self.converter.parse_markdown(md)
        assert len(slides) == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
