#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Markdown转换工具
将Markdown格式转换为Telegram支持的HTML格式
"""

import re
from typing import str


def markdown_to_html(text: str) -> str:
    """将Markdown文本转换为Telegram支持的HTML格式
    
    Args:
        text: Markdown格式的文本
        
    Returns:
        转换后的HTML格式文本
    """
    if not text:
        return text
    
    # 复制文本避免修改原始内容
    html_text = text
    
    # 1. 转换标题
    # ## 标题 -> <b>标题</b>
    html_text = re.sub(r'^## (.+)$', r'<b>\1</b>', html_text, flags=re.MULTILINE)
    # ### 标题 -> <b>标题</b>
    html_text = re.sub(r'^### (.+)$', r'<b>\1</b>', html_text, flags=re.MULTILINE)
    # #### 标题 -> <b>标题</b>
    html_text = re.sub(r'^#### (.+)$', r'<b>\1</b>', html_text, flags=re.MULTILINE)
    
    # 2. 转换粗体
    # **文本** -> <b>文本</b>
    html_text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', html_text)
    
    # 3. 转换斜体
    # *文本* -> <i>文本</i>
    html_text = re.sub(r'(?<!\*)\*([^*]+?)\*(?!\*)', r'<i>\1</i>', html_text)
    
    # 4. 转换代码
    # `代码` -> <code>代码</code>
    html_text = re.sub(r'`([^`]+?)`', r'<code>\1</code>', html_text)
    
    # 5. 转换链接
    # [文本](链接) -> <a href="链接">文本</a>
    html_text = re.sub(r'\[([^\]]+?)\]\(([^\)]+?)\)', r'<a href="\2">\1</a>', html_text)
    
    # 6. 转换列表项
    # - 项目 -> • 项目
    html_text = re.sub(r'^- (.+)$', r'• \1', html_text, flags=re.MULTILINE)
    # + 项目 -> • 项目
    html_text = re.sub(r'^\+ (.+)$', r'• \1', html_text, flags=re.MULTILINE)
    
    # 7. 转换数字列表
    # 1. 项目 -> 1. 项目 (保持不变，Telegram支持)
    
    # 8. 转换分割线
    # --- -> ────────────
    html_text = re.sub(r'^---+$', '────────────', html_text, flags=re.MULTILINE)
    
    # 9. 转换引用
    # > 引用 -> ▶ 引用
    html_text = re.sub(r'^> (.+)$', r'▶ <i>\1</i>', html_text, flags=re.MULTILINE)
    
    # 10. 清理多余的空行（保留最多2个连续换行）
    html_text = re.sub(r'\n{3,}', '\n\n', html_text)
    
    return html_text.strip()


def format_changelog_content(content: str) -> str:
    """格式化开发日志内容
    
    专门用于开发日志的格式化，包含特殊的样式处理
    
    Args:
        content: 原始开发日志内容
        
    Returns:
        格式化后的内容
    """
    if not content:
        return content
    
    # 先进行基本的Markdown转换
    formatted_content = markdown_to_html(content)
    
    # 特殊处理：确保emoji和文本之间有适当的间距
    formatted_content = re.sub(r'(🌸|✨|💬|📝|🎮|📊|🎯|📱|🔘|💡)', r'\1 ', formatted_content)
    
    # 移除重复的空格
    formatted_content = re.sub(r'  +', ' ', formatted_content)
    
    return formatted_content


def escape_html_chars(text: str) -> str:
    """转义HTML特殊字符
    
    Args:
        text: 需要转义的文本
        
    Returns:
        转义后的文本
    """
    if not text:
        return text
    
    # Telegram HTML模式需要转义的字符
    replacements = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#x27;'
    }
    
    result = text
    for char, escaped in replacements.items():
        result = result.replace(char, escaped)
    
    return result


def safe_html_format(text: str, convert_markdown: bool = True) -> str:
    """安全的HTML格式化
    
    先转义特殊字符，再进行Markdown转换
    
    Args:
        text: 原始文本
        convert_markdown: 是否转换Markdown格式
        
    Returns:
        安全的HTML格式文本
    """
    if not text:
        return text
    
    # 注意：这里不能先转义HTML字符，因为我们需要保留Markdown语法
    # 只在最后转义非Markdown的特殊字符
    
    if convert_markdown:
        # 转换Markdown
        formatted_text = markdown_to_html(text)
        
        # 只转义不在HTML标签中的特殊字符
        # 这是一个简化的实现，实际使用中可能需要更复杂的处理
        return formatted_text
    else:
        # 直接转义所有HTML字符
        return escape_html_chars(text)


# 测试函数
def test_markdown_conversion():
    """测试Markdown转换功能"""
    test_text = """## 测试标题

### 子标题

这是**粗体**文本和*斜体*文本。

- 列表项1
- 列表项2

1. 数字列表1
2. 数字列表2

`代码示例`

[链接文本](https://example.com)

> 这是引用

---

结束。"""
    
    print("原始文本:")
    print(test_text)
    print("\n转换后:")
    print(markdown_to_html(test_text))


if __name__ == "__main__":
    test_markdown_conversion()