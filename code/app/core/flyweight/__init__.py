# -*- coding: utf-8 -*-
"""
上海宇羲伏天智能科技有限公司出品

文件级注释：享元模式模块
内部逻辑：共享相同内容的文档片段，减少内存占用
设计模式：享元模式（Flyweight Pattern）
设计原则：SOLID - 单一职责原则
"""

from .chunk_flyweight import ChunkFlyweight, ChunkFlyweightFactory

__all__ = ["ChunkFlyweight", "ChunkFlyweightFactory"]
