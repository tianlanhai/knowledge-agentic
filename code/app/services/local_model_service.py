# -*- coding: utf-8 -*-
"""
上海宇羲伏天智能科技有限公司出品

文件级注释：本地模型扫描服务
内部逻辑：扫描本地模型目录，识别可用的Embedding模型
参考项目：easy-dataset-file
"""

import os
from pathlib import Path
from typing import List, Dict, Any
from loguru import logger
from app.core.config import settings


class LocalModelService:
    """
    类级注释：本地模型扫描服务类
    职责：
        1. 扫描本地模型目录
        2. 识别有效的Embedding模型
        3. 返回可用模型列表
    """

    # 内部类常量：常见的Embedding模型名称模式
    EMBEDDING_PATTERNS = [
        "embed",
        "bge",
        "e5",
        "gte",
        "sentence",
        "paraphrase",
        "mpnet",
        "distilbert",
        "minilm",
    ]

    # 内部类常量：模型权重文件扩展名
    MODEL_FILE_EXTENSIONS = [
        ".bin",
        ".safetensors",
        ".pt",
        ".pth",
    ]

    @staticmethod
    def _get_model_dir() -> Path:
        """
        函数级注释：获取本地模型目录
        内部逻辑：从settings读取模型目录，用于测试时patch
        返回值：模型目录路径
        """
        return Path(settings.LOCAL_MODEL_DIR)

    @staticmethod
    def scan_local_models() -> Dict[str, Any]:
        """
        函数级注释：扫描本地模型目录，返回可用的Embedding模型列表
        内部逻辑：获取模型目录 -> 遍历子目录 -> 验证模型有效性 -> 返回结果
        返回值：包含模型列表和基础目录的字典
        """
        # 内部变量：获取模型基础目录
        model_base_dir = LocalModelService._get_model_dir()

        # 内部逻辑：Guard Clauses - 检查目录是否存在
        if not model_base_dir.exists():
            logger.warning(f"本地模型目录不存在: {model_base_dir}")
            return {
                "models": [],
                "base_dir": str(model_base_dir),
                "error": "模型目录不存在"
            }

        # 内部变量：存储有效模型列表
        valid_models: List[str] = []

        # 内部逻辑：遍历模型目录下的子目录
        for item in model_base_dir.iterdir():
            # 内部逻辑：跳过非目录项和隐藏目录
            if not item.is_dir() or item.name.startswith('.'):
                continue

            # 内部逻辑：验证是否为有效的Embedding模型
            if LocalModelService.is_valid_embedding_model(item):
                valid_models.append(item.name)
                logger.debug(f"发现有效模型: {item.name}")

        # 内部逻辑：按名称排序
        valid_models.sort()

        logger.info(f"扫描本地模型目录完成，发现 {len(valid_models)} 个有效模型")

        return {
            "models": valid_models,
            "base_dir": str(model_base_dir)
        }

    @staticmethod
    def is_valid_embedding_model(model_dir: Path) -> bool:
        """
        函数级注释：验证目录是否为有效的Embedding模型
        内部逻辑：检查目录名 -> 检查config.json -> 检查模型文件
        参数：
            model_dir: 模型目录路径
        返回值：是否为有效的Embedding模型
        """
        # 内部逻辑：检查目录名是否匹配Embedding模型模式
        name_match = LocalModelService._check_name_pattern(model_dir.name)

        # 内部逻辑：检查是否存在config.json文件
        has_config = LocalModelService._has_config_file(model_dir)

        # 内部逻辑：检查是否存在模型权重文件
        has_model_file = LocalModelService._has_model_files(model_dir)

        # 内部逻辑：目录名匹配 且 (有配置文件 或 有模型文件)
        is_valid = name_match and (has_config or has_model_file)

        if is_valid:
            logger.debug(f"模型 {model_dir.name} 验证通过: "
                        f"名称匹配={name_match}, 配置文件={has_config}, 模型文件={has_model_file}")

        return is_valid

    @staticmethod
    def _check_name_pattern(dir_name: str) -> bool:
        """
        函数级注释：检查目录名是否匹配Embedding模型模式
        内部逻辑：检查名称中是否包含常见的Embedding关键词
        参数：
            dir_name: 目录名称
        返回值：是否匹配
        """
        dir_name_lower = dir_name.lower()

        # 内部逻辑：检查是否包含任意一个Embedding关键词
        for pattern in LocalModelService.EMBEDDING_PATTERNS:
            if pattern in dir_name_lower:
                return True

        return False

    @staticmethod
    def _has_config_file(model_dir: Path) -> bool:
        """
        函数级注释：检查目录中是否存在config.json文件
        内部逻辑：检查config.json或config.yaml文件
        参数：
            model_dir: 模型目录路径
        返回值：是否存在配置文件
        """
        # 内部逻辑：检查常见的配置文件
        config_files = ["config.json", "config.yaml", "config.yml"]

        for config_file in config_files:
            if (model_dir / config_file).exists():
                return True

        return False

    @staticmethod
    def _has_model_files(model_dir: Path) -> bool:
        """
        函数级注释：检查目录中是否存在模型权重文件
        内部逻辑：检查常见扩展名的模型文件
        参数：
            model_dir: 模型目录路径
        返回值：是否存在模型文件
        """
        # 内部逻辑：遍历目录中的文件
        for file in model_dir.iterdir():
            # 内部逻辑：跳过非文件项
            if not file.is_file():
                continue

            # 内部逻辑：检查文件扩展名
            for ext in LocalModelService.MODEL_FILE_EXTENSIONS:
                if file.suffix == ext or file.name.endswith(ext):
                    return True

        return False

    @staticmethod
    def get_model_info(model_name: str) -> Dict[str, Any]:
        """
        函数级注释：获取指定模型的详细信息
        内部逻辑：检查模型目录 -> 读取配置文件 -> 计算大小 -> 返回信息
        参数：
            model_name: 模型名称（目录名）
        返回值：模型信息字典
        """
        # 内部变量：模型目录路径
        model_dir = LocalModelService._get_model_dir() / model_name

        # 内部逻辑：Guard Clauses - 检查目录是否存在
        if not model_dir.exists():
            return {
                "name": model_name,
                "exists": False
            }

        # 内部变量：计算模型大小
        total_size = 0
        file_count = 0

        for file in model_dir.rglob('*'):
            if file.is_file():
                total_size += file.stat().st_size
                file_count += 1

        # 内部变量：转换为MB
        size_mb = round(total_size / (1024 * 1024), 2)

        # 内部变量：读取配置文件
        config_data = None
        config_file = model_dir / "config.json"
        if config_file.exists():
            try:
                import json
                with open(config_file, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
            except Exception as e:
                logger.warning(f"读取配置文件失败: {e}")

        return {
            "name": model_name,
            "exists": True,
            "path": str(model_dir),
            "size_mb": size_mb,
            "file_count": file_count,
            "has_config": config_file.exists(),
            "config": config_data
        }
