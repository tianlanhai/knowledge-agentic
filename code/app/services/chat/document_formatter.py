"""
上海宇羲伏天智能科技有限公司出品

文件级注释：文档格式化模块
内部逻辑：提供文档内容的格式化功能，支持Markdown、结构化内容和高亮
设计模式：策略模式 - 支持多种格式化策略组合
"""

from typing import List, Dict, Any, Optional


# 内部逻辑：导入可选依赖
try:
    from markdown_it import MarkdownIt
    from bs4 import BeautifulSoup
    DEPENDENCIES_AVAILABLE = True
except ImportError:
    # 内部逻辑：缺少依赖时使用简化版本
    MarkdownIt = None
    BeautifulSoup = None
    DEPENDENCIES_AVAILABLE = False


class DocumentFormatter:
    """
    类级注释：文档格式化类
    内部逻辑：实现Markdown解析、结构化内容识别和高亮显示
    设计模式：策略模式 - 支持多种格式化策略
    """

    @staticmethod
    def format_markdown(content: str) -> str:
        """
        函数级注释：Markdown格式化
        内部逻辑：使用markdown-it解析Markdown内容
        参数：content - 原始文本内容
        返回值：格式化后的HTML内容
        """
        # Guard Clauses：依赖不可用时返回原内容
        if not DEPENDENCIES_AVAILABLE or MarkdownIt is None:
            return content

        md = MarkdownIt()
        return md.render(content)

    @staticmethod
    def format_structured_content(content: str) -> str:
        """
        函数级注释：结构化内容格式化
        内部逻辑：识别并格式化表格、列表、引用等结构化内容
        参数：content - 原始文本内容
        返回值：格式化后的HTML内容
        """
        # Guard Clauses：依赖不可用时返回原内容
        if not DEPENDENCIES_AVAILABLE or BeautifulSoup is None:
            return content

        soup = BeautifulSoup(content, 'html.parser')

        # 内部逻辑：处理表格
        tables = soup.find_all('table')
        for table in tables:
            table['class'] = table.get('class', []) + [
                'table', 'table-bordered', 'table-striped'
            ]

        # 内部逻辑：处理列表
        lists = soup.find_all(['ul', 'ol'])
        for lst in lists:
            lst['class'] = lst.get('class', []) + ['list-group']

        # 内部逻辑：处理引用块
        blockquotes = soup.find_all('blockquote')
        for blockquote in blockquotes:
            blockquote['class'] = blockquote.get('class', []) + ['blockquote']

        return str(soup)

    @staticmethod
    def highlight_content(
        content: str,
        keywords: List[str] = None
    ) -> str:
        """
        函数级注释：内容高亮
        内部逻辑：根据关键词对重要内容进行高亮显示
        参数：
            content - 原始文本内容
            keywords - 需要高亮的关键词列表
        返回值：高亮后的HTML内容
        """
        # Guard Clauses：无关键词或依赖不可用时返回原内容
        if not keywords or not DEPENDENCIES_AVAILABLE or BeautifulSoup is None:
            return content

        soup = BeautifulSoup(content, 'html.parser')

        for keyword in keywords:
            for text in soup.find_all(
                string=lambda text: keyword.lower() in text.lower()
            ):
                parent = text.parent
                # Guard Clauses：跳过脚本和样式标签
                if parent and parent.name not in ['script', 'style']:
                    new_tag = soup.new_tag('mark')
                    new_tag.string = text
                    new_tag['class'] = ['highlight']
                    text.replace_with(new_tag)

        return str(soup)

    @staticmethod
    def format_document(
        content: str,
        formatting_options: Dict[str, Any] = None
    ) -> str:
        """
        函数级注释：综合文档格式化
        内部逻辑：综合应用各种格式化方法
        设计模式：建造者模式 - 按步骤组合格式化操作
        参数：
            content - 原始文本内容
            formatting_options - 格式化选项
        返回值：完全格式化后的HTML内容
        """
        # Guard Clauses：初始化格式化选项
        if not formatting_options:
            formatting_options = {}

        # 内部变量：依次应用格式化
        formatted_content = content

        # 内部逻辑：应用Markdown格式化
        if formatting_options.get('enable_markdown', True):
            formatted_content = DocumentFormatter.format_markdown(formatted_content)

        # 内部逻辑：应用结构化内容格式化
        if formatting_options.get('enable_structured', True):
            formatted_content = DocumentFormatter.format_structured_content(
                formatted_content
            )

        # 内部逻辑：应用高亮
        if formatting_options.get('highlight_keywords'):
            formatted_content = DocumentFormatter.highlight_content(
                formatted_content,
                formatting_options.get('highlight_keywords')
            )

        return formatted_content


class DocumentFormatterBuilder:
    """
    类级注释：文档格式化器建造者
    内部逻辑：提供流畅的接口构建格式化配置
    设计模式：建造者模式 - 支持链式调用
    """

    def __init__(self):
        """函数级注释：初始化建造者"""
        # 内部变量：格式化选项
        self._options: Dict[str, Any] = {}

    def with_markdown(
        self,
        enable: bool = True
    ) -> 'DocumentFormatterBuilder':
        """
        函数级注释：设置Markdown格式化
        参数：enable - 是否启用
        返回值：self - 支持链式调用
        """
        self._options['enable_markdown'] = enable
        return self

    def with_structured(
        self,
        enable: bool = True
    ) -> 'DocumentFormatterBuilder':
        """
        函数级注释：设置结构化内容格式化
        参数：enable - 是否启用
        返回值：self - 支持链式调用
        """
        self._options['enable_structured'] = enable
        return self

    def with_highlight(
        self,
        keywords: List[str]
    ) -> 'DocumentFormatterBuilder':
        """
        函数级注释：设置高亮关键词
        参数：keywords - 关键词列表
        返回值：self - 支持链式调用
        """
        self._options['highlight_keywords'] = keywords
        return self

    def build(self) -> Dict[str, Any]:
        """
        函数级注释：构建格式化配置
        返回值：格式化选项字典
        """
        return self._options

    def format(self, content: str) -> str:
        """
        函数级注释：直接格式化内容
        参数：content - 原始内容
        返回值：格式化后的内容
        """
        return DocumentFormatter.format_document(content, self._options)
