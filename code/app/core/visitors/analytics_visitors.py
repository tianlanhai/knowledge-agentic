# -*- coding: utf-8 -*-
"""
上海宇羲伏天智能科技有限公司出品

文件级注释：分析访问者实现类
内部逻辑：实现文档统计、分析、搜索等访问者
设计模式：访问者模式（Visitor Pattern）- 具体访问者
设计原则：SOLID - 单一职责原则、开闭原则
"""

import re
from typing import Any, List, Dict, Set, Tuple, Optional
from dataclasses import dataclass, field
from datetime import datetime
from collections import Counter
from loguru import logger

from app.core.visitors.document_visitor import (
    DocumentVisitor,
    Document,
    DocumentChunk,
    DocumentCollection,
    ExportResult,
    VisitorRegistry,
)


@dataclass
class DocumentStatistics:
    """
    类级注释：文档统计结果
    职责：存储文档分析的统计数据
    """
    # 文档数量
    document_count: int = 0
    # 总字符数
    total_chars: int = 0
    # 总单词数
    total_words: int = 0
    # 总段落数
    total_paragraphs: int = 0
    # 平均文档长度
    avg_document_length: float = 0.0
    # 最长文档
    longest_document: Optional[str] = None
    # 最短文档
    shortest_document: Optional[str] = None
    # 文件类型分布
    file_type_distribution: Dict[str, int] = field(default_factory=dict)
    # 关键词频率
    keyword_frequency: Dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "document_count": self.document_count,
            "total_chars": self.total_chars,
            "total_words": self.total_words,
            "total_paragraphs": self.total_paragraphs,
            "avg_document_length": self.avg_document_length,
            "longest_document": self.longest_document,
            "shortest_document": self.shortest_document,
            "file_type_distribution": self.file_type_distribution,
            "keyword_frequency": self.keyword_frequency,
        }


class StatisticsVisitor(DocumentVisitor):
    """
    类级注释：统计访问者
    设计模式：访问者模式（Visitor Pattern）- 具体访问者
    职责：统计文档的各种指标
    """

    def __init__(self, top_keywords: int = 10):
        """
        函数级注释：初始化统计访问者
        参数：
            top_keywords: 返回的高频关键词数量
        """
        self.top_keywords = top_keywords
        self._stats = DocumentStatistics()
        self._all_lengths: List[int] = []

    def visit_document(self, document: Document) -> DocumentStatistics:
        """
        函数级注释：统计单个文档
        返回值：当前统计结果
        """
        # 内部逻辑：更新文档计数
        self._stats.document_count += 1

        # 内部逻辑：统计字符数
        char_count = len(document.content)
        self._stats.total_chars += char_count
        self._all_lengths.append(char_count)

        # 内部逻辑：统计单词数（支持中文和英文）
        words = re.findall(r'[\u4e00-\u9fff]+|[a-zA-Z]+', document.content)
        self._stats.total_words += len(words)

        # 内部逻辑：统计段落数
        paragraphs = [p for p in document.content.split('\n') if p.strip()]
        self._stats.total_paragraphs += len(paragraphs)

        # 内部逻辑：更新最长/最短文档
        if self._stats.longest_document is None or char_count > max(self._all_lengths[:-1]):
            self._stats.longest_document = document.title

        if self._stats.shortest_document is None or char_count < min(self._all_lengths[:-1]):
            self._stats.shortest_document = document.title

        # 内部逻辑：统计文件类型
        file_type = document.file_type or "unknown"
        self._stats.file_type_distribution[file_type] = \
            self._stats.file_type_distribution.get(file_type, 0) + 1

        # 内部逻辑：统计关键词频率
        self._update_keyword_frequency(words)

        # 内部逻辑：计算平均文档长度
        if self._all_lengths:
            self._stats.avg_document_length = sum(self._all_lengths) / len(self._all_lengths)

        return self._stats

    def visit_chunk(self, chunk: DocumentChunk) -> DocumentStatistics:
        """
        函数级注释：统计文档片段
        返回值：当前统计结果
        """
        # 片段统计：只统计字符和单词
        self._stats.total_chars += len(chunk.content)

        words = re.findall(r'[\u4e00-\u9fff]+|[a-zA-Z]+', chunk.content)
        self._stats.total_words += len(words)

        self._update_keyword_frequency(words)

        return self._stats

    def visit_collection(self, collection: DocumentCollection) -> DocumentStatistics:
        """
        函数级注释：统计文档集合
        返回值：统计结果
        """
        # 内部逻辑：遍历所有文档进行统计
        for doc in collection.documents:
            self.visit_document(doc)

        # 内部逻辑：截取Top关键词
        sorted_keywords = sorted(
            self._stats.keyword_frequency.items(),
            key=lambda x: x[1],
            reverse=True
        )[:self.top_keywords]
        self._stats.keyword_frequency = dict(sorted_keywords)

        return self._stats

    def _update_keyword_frequency(self, words: List[str]) -> None:
        """更新关键词频率"""
        word_counter = Counter(words)
        for word, count in word_counter.items():
            self._stats.keyword_frequency[word] = \
                self._stats.keyword_frequency.get(word, 0) + count

    def get_statistics(self) -> DocumentStatistics:
        """获取统计结果"""
        return self._stats


@dataclass
class SearchResult:
    """
    类级注释：搜索结果
    职责：存储搜索匹配信息
    """
    document_id: int
    document_title: str
    matches: List[str]  # 匹配到的文本片段
    match_count: int  # 匹配次数
    context: str  # 匹配上下文


class SearchVisitor(DocumentVisitor):
    """
    类级注释：搜索访问者
    设计模式：访问者模式（Visitor Pattern）- 具体访问者
    职责：在文档中搜索关键词
    """

    def __init__(
        self,
        keywords: List[str],
        case_sensitive: bool = False,
        use_regex: bool = False,
        context_length: int = 50
    ):
        """
        函数级注释：初始化搜索访问者
        参数：
            keywords: 关键词列表
            case_sensitive: 是否区分大小写
            use_regex: 是否使用正则表达式
            context_length: 上下文长度
        """
        self.keywords = keywords
        self.case_sensitive = case_sensitive
        self.use_regex = use_regex
        self.context_length = context_length
        self._results: List[SearchResult] = []

        # 内部逻辑：编译正则表达式
        if self.use_regex:
            flags = 0 if self.case_sensitive else re.IGNORECASE
            self._patterns = [re.compile(kw, flags) for kw in keywords]
        else:
            self._patterns = None

    def visit_document(self, document: Document) -> List[SearchResult]:
        """
        函数级注释：搜索单个文档
        返回值：搜索结果列表
        """
        content = document.content if self.case_sensitive else document.content.lower()
        search_keywords = self.keywords if self.case_sensitive else [kw.lower() for kw in self.keywords]
        matches: List[str] = []
        match_positions: List[Tuple[int, int]] = []

        # 内部逻辑：搜索匹配
        for i, keyword in enumerate(search_keywords):
            if self.use_regex:
                for match in self._patterns[i].finditer(document.content):
                    matches.append(match.group())
                    match_positions.append(match.span())
            else:
                start = 0
                while True:
                    pos = content.find(keyword, start)
                    if pos == -1:
                        break
                    matches.append(document.content[pos:pos + len(keyword)])
                    match_positions.append((pos, pos + len(keyword)))
                    start = pos + 1

        if matches:
            # 内部逻辑：提取匹配上下文
            contexts = self._extract_contexts(document.content, match_positions)

            result = SearchResult(
                document_id=document.id,
                document_title=document.title,
                matches=matches,
                match_count=len(matches),
                context=contexts[0] if contexts else ""
            )
            self._results.append(result)

        return self._results

    def visit_chunk(self, chunk: DocumentChunk) -> List[SearchResult]:
        """
        函数级注释：搜索文档片段
        返回值：搜索结果列表
        """
        # 片段搜索：简化处理
        content = chunk.content if self.case_sensitive else chunk.content.lower()
        search_keywords = self.keywords if self.case_sensitive else [kw.lower() for kw in self.keywords]

        match_count = 0
        for keyword in search_keywords:
            match_count += content.count(keyword)

        if match_count > 0:
            result = SearchResult(
                document_id=chunk.document_id,
                document_title=f"Chunk {chunk.chunk_index}",
                matches=[],
                match_count=match_count,
                context=chunk.content[:self.context_length * 2]
            )
            self._results.append(result)

        return self._results

    def visit_collection(self, collection: DocumentCollection) -> List[SearchResult]:
        """
        函数级注释：搜索文档集合
        返回值：所有搜索结果
        """
        self._results = []
        for doc in collection.documents:
            self.visit_document(doc)
        return self._results

    def _extract_contexts(self, content: str, positions: List[Tuple[int, int]]) -> List[str]:
        """提取匹配上下文"""
        contexts = []
        for start, end in positions:
            context_start = max(0, start - self.context_length)
            context_end = min(len(content), end + self.context_length)
            context = content[context_start:context_end]
            contexts.append(context)
        return contexts

    def get_results(self) -> List[SearchResult]:
        """获取搜索结果"""
        return self._results

    def clear_results(self) -> None:
        """清除搜索结果"""
        self._results = []


@dataclass
class ValidationIssue:
    """
    类级注释：验证问题
    职责：存储文档验证发现的问题
    """
    severity: str  # 严重程度: error, warning, info
    message: str  # 问题描述
    location: Optional[str] = None  # 位置信息
    suggestion: Optional[str] = None  # 修复建议


class ValidationVisitor(DocumentVisitor):
    """
    类级注释：验证访问者
    设计模式：访问者模式（Visitor Pattern）- 具体访问者
    职责：验证文档的完整性和质量
    """

    def __init__(
        self,
        check_empty_content: bool = True,
        check_min_length: int = 10,
        check_max_length: Optional[int] = None,
        check_encoding: bool = True
    ):
        """
        函数级注释：初始化验证访问者
        参数：
            check_empty_content: 是否检查空内容
            check_min_length: 最小长度检查
            check_max_length: 最大长度检查
            check_encoding: 是否检查编码问题
        """
        self.check_empty_content = check_empty_content
        self.check_min_length = check_min_length
        self.check_max_length = check_max_length
        self.check_encoding = check_encoding
        self._issues: List[ValidationIssue] = []

    def visit_document(self, document: Document) -> List[ValidationIssue]:
        """
        函数级注释：验证单个文档
        返回值：问题列表
        """
        # 内部逻辑：检查空内容
        if self.check_empty_content and not document.content.strip():
            self._issues.append(ValidationIssue(
                severity="error",
                message="文档内容为空",
                location=f"文档 ID: {document.id}",
                suggestion="请添加文档内容"
            ))

        # 内部逻辑：检查最小长度
        if self.check_min_length and len(document.content) < self.check_min_length:
            self._issues.append(ValidationIssue(
                severity="warning",
                message=f"文档内容过短（{len(document.content)} 字符）",
                location=f"文档: {document.title}",
                suggestion=f"建议至少包含 {self.check_min_length} 个字符"
            ))

        # 内部逻辑：检查最大长度
        if self.check_max_length and len(document.content) > self.check_max_length:
            self._issues.append(ValidationIssue(
                severity="info",
                message=f"文档内容过长（{len(document.content)} 字符）",
                location=f"文档: {document.title}",
                suggestion=f"建议控制在 {self.check_max_length} 字符以内"
            ))

        # 内部逻辑：检查编码问题
        if self.check_encoding:
            try:
                document.content.encode('utf-8')
            except UnicodeEncodeError as e:
                self._issues.append(ValidationIssue(
                    severity="error",
                    message=f"文档包含无法编码的字符: {e}",
                    location=f"文档: {document.title}",
                    suggestion="请检查并移除特殊字符"
                ))

        return self._issues

    def visit_chunk(self, chunk: DocumentChunk) -> List[ValidationIssue]:
        """
        函数级注释：验证文档片段
        返回值：问题列表
        """
        if not chunk.content.strip():
            self._issues.append(ValidationIssue(
                severity="warning",
                message="文档片段为空",
                location=f"Chunk {chunk.chunk_index}",
                suggestion="请检查分块逻辑"
            ))
        return self._issues

    def visit_collection(self, collection: DocumentCollection) -> List[ValidationIssue]:
        """
        函数级注释：验证文档集合
        返回值：所有问题列表
        """
        self._issues = []

        # 内部逻辑：验证集合
        if not collection.documents:
            self._issues.append(ValidationIssue(
                severity="warning",
                message="文档集合为空",
                location=f"集合: {collection.name}",
                suggestion="请添加文档到集合"
            ))

        # 内部逻辑：验证每个文档
        for doc in collection.documents:
            self.visit_document(doc)

        return self._issues

    def get_issues(self) -> List[ValidationIssue]:
        """获取所有问题"""
        return self._issues

    def get_issues_by_severity(self, severity: str) -> List[ValidationIssue]:
        """按严重程度获取问题"""
        return [issue for issue in self._issues if issue.severity == severity]

    def has_errors(self) -> bool:
        """是否有错误"""
        return any(issue.severity == "error" for issue in self._issues)

    def clear_issues(self) -> None:
        """清除问题列表"""
        self._issues = []


class TransformVisitor(DocumentVisitor):
    """
    类级注释：转换访问者
    设计模式：访问者模式（Visitor Pattern）- 具体访问者
    职责：对文档进行转换操作
    """

    def __init__(
        self,
        remove_extra_whitespace: bool = True,
        normalize_line_breaks: bool = True,
        trim_lines: bool = True
    ):
        """
        函数级注释：初始化转换访问者
        参数：
            remove_extra_whitespace: 是否移除多余空白
            normalize_line_breaks: 是否规范化换行符
            trim_lines: 是否去除行首尾空白
        """
        self.remove_extra_whitespace = remove_extra_whitespace
        self.normalize_line_breaks = normalize_line_breaks
        self.trim_lines = trim_lines
        self._transformed_documents: Dict[int, str] = {}

    def visit_document(self, document: Document) -> str:
        """
        函数级注释：转换单个文档
        返回值：转换后的内容
        """
        content = document.content

        # 内部逻辑：规范化换行符
        if self.normalize_line_breaks:
            content = re.sub(r'\r\n|\r', '\n', content)

        # 内部逻辑：去除行首尾空白
        if self.trim_lines:
            lines = content.split('\n')
            content = '\n'.join(line.strip() for line in lines)

        # 内部逻辑：移除多余空白
        if self.remove_extra_whitespace:
            content = re.sub(r' +', ' ', content)
            content = re.sub(r'\n\s*\n', '\n\n', content)

        self._transformed_documents[document.id] = content
        return content

    def visit_chunk(self, chunk: DocumentChunk) -> str:
        """
        函数级注释：转换文档片段
        返回值：转换后的内容
        """
        content = chunk.content

        if self.remove_extra_whitespace:
            content = re.sub(r'\s+', ' ', content).strip()

        return content

    def visit_collection(self, collection: DocumentCollection) -> Dict[int, str]:
        """
        函数级注释：转换文档集合
        返回值：文档ID到转换内容的映射
        """
        self._transformed_documents = {}
        for doc in collection.documents:
            self.visit_document(doc)
        return self._transformed_documents

    def get_transformed_content(self, document_id: int) -> Optional[str]:
        """获取转换后的内容"""
        return self._transformed_documents.get(document_id)


# 内部逻辑：自动注册所有分析访问者
VisitorRegistry.register("statistics", StatisticsVisitor)
VisitorRegistry.register("search", SearchVisitor)
VisitorRegistry.register("validation", ValidationVisitor)
VisitorRegistry.register("transform", TransformVisitor)

# 导出所有公共接口
__all__ = [
    # 数据类
    'DocumentStatistics',
    'SearchResult',
    'ValidationIssue',
    # 访问者类
    'StatisticsVisitor',
    'SearchVisitor',
    'ValidationVisitor',
    'TransformVisitor',
]
