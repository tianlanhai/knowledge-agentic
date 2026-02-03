# -*- coding: utf-8 -*-
"""
上海宇羲伏天智能科技有限公司出品

文件级注释：local_model_service 模块单元测试
内部逻辑：测试本地模型扫描服务
覆盖范围：模型扫描、验证、信息获取
"""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from app.services.local_model_service import LocalModelService
import tempfile
import shutil


class TestLocalModelService:
    """
    类级注释：测试 LocalModelService 类的功能
    """

    def setup_method(self):
        """
        函数级注释：每个测试前的设置
        内部逻辑：创建临时目录用于测试
        """
        # 内部变量：创建临时目录
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """
        函数级注释：每个测试后的清理
        内部逻辑：删除临时目录
        """
        if hasattr(self, 'temp_dir') and Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)

    def test_scan_local_models_directory_not_exist(self):
        """
        函数级注释：测试模型目录不存在时的行为
        内部逻辑：patch _get_model_dir 返回不存在的路径
        """
        # 内部逻辑：使用 patch 来模拟不存在的目录
        with patch('app.services.local_model_service.LocalModelService._get_model_dir', return_value=Path('/nonexistent/path')):
            # 内部逻辑：执行扫描
            result = LocalModelService.scan_local_models()

            # 内部逻辑：验证结果
            assert result["models"] == []
            assert "error" in result
            assert "不存在" in result["error"]

    def test_scan_local_models_success(self, tmp_path):
        """
        函数级注释：测试成功扫描模型
        内部逻辑：创建包含有效模型的目录，验证正确识别
        参数：
            tmp_path: pytest临时路径fixture
        """
        # 内部逻辑：创建模型目录
        model_dir = tmp_path / "bge-large-zh"
        model_dir.mkdir()

        # 内部逻辑：创建config.json
        (model_dir / "config.json").write_text('{"model_type": "embedding"}')

        # 内部逻辑：创建模型文件
        (model_dir / "model.bin").write_bytes(b"fake model")

        # 内部逻辑：创建一个非模型的目录
        other_dir = tmp_path / "other-model"
        other_dir.mkdir()
        (other_dir / "file.txt").write_text("not a model")

        # 内部逻辑：创建隐藏目录
        hidden_dir = tmp_path / ".hidden"
        hidden_dir.mkdir()

        # 内部逻辑：patch _get_model_dir
        with patch('app.services.local_model_service.LocalModelService._get_model_dir', return_value=tmp_path):
            # 内部逻辑：执行扫描
            result = LocalModelService.scan_local_models()

            # 内部逻辑：验证结果
            assert "bge-large-zh" in result["models"]
            assert "other-model" not in result["models"]  # 不包含embedding关键词
            assert ".hidden" not in result["models"]  # 隐藏目录被跳过

    def test_is_valid_embedding_model_name_match(self, tmp_path):
        """
        函数级注释：测试模型名称匹配验证
        内部逻辑：创建包含embedding关键词的目录，验证验证通过
        参数：
            tmp_path: pytest临时路径fixture
        """
        # 内部逻辑：创建包含embedding关键词的目录
        model_dir = tmp_path / "bge-base-model"
        model_dir.mkdir()

        # 内部逻辑：创建config.json
        (model_dir / "config.json").write_text("{}")

        # 内部逻辑：验证模型
        result = LocalModelService.is_valid_embedding_model(model_dir)

        # 内部逻辑：验证通过
        assert result is True

    def test_is_valid_embedding_model_with_config_file(self, tmp_path):
        """
        函数级注释：测试有config文件的模型验证
        内部逻辑：创建包含config的目录
        参数：
            tmp_path: pytest临时路径fixture
        """
        model_dir = tmp_path / "embedding-model"
        model_dir.mkdir()
        (model_dir / "config.json").write_text("{}")

        result = LocalModelService.is_valid_embedding_model(model_dir)
        assert result is True

    def test_is_valid_embedding_model_with_yaml_config(self, tmp_path):
        """
        函数级注释：测试yaml config文件的验证
        内部逻辑：创建包含config.yaml的目录
        参数：
            tmp_path: pytest临时路径fixture
        """
        model_dir = tmp_path / "sentence-transformer"
        model_dir.mkdir()
        (model_dir / "config.yaml").write_text("model: test")

        result = LocalModelService.is_valid_embedding_model(model_dir)
        assert result is True

    def test_is_valid_embedding_model_with_model_file(self, tmp_path):
        """
        函数级注释：测试有模型文件的验证
        内部逻辑：创建包含.bin文件的目录
        参数：
            tmp_path: pytest临时路径fixture
        """
        model_dir = tmp_path / "e5-model"
        model_dir.mkdir()
        (model_dir / "model.bin").write_bytes(b"data")

        result = LocalModelService.is_valid_embedding_model(model_dir)
        assert result is True

    def test_is_valid_embedding_model_with_safetensors(self, tmp_path):
        """
        函数级注释：测试safetensors文件的验证
        内部逻辑：创建包含.safetensors文件的目录
        参数：
            tmp_path: pytest临时路径fixture
        """
        model_dir = tmp_path / "gte-model"
        model_dir.mkdir()
        (model_dir / "model.safetensors").write_bytes(b"data")

        result = LocalModelService.is_valid_embedding_model(model_dir)
        assert result is True

    def test_is_valid_embedding_model_no_name_match(self, tmp_path):
        """
        函数级注释：测试名称不匹配时的验证
        内部逻辑：创建不包含embedding关键词的目录
        参数：
            tmp_path: pytest临时路径fixture
        """
        model_dir = tmp_path / "llama-model"
        model_dir.mkdir()
        (model_dir / "config.json").write_text("{}")

        result = LocalModelService.is_valid_embedding_model(model_dir)
        assert result is False

    def test_is_valid_embedding_model_no_files(self, tmp_path):
        """
        函数级注释：测试没有有效文件的验证
        内部逻辑：创建空目录
        参数：
            tmp_path: pytest临时路径fixture
        """
        model_dir = tmp_path / "embed-model"
        model_dir.mkdir()

        result = LocalModelService.is_valid_embedding_model(model_dir)
        assert result is False

    def test_check_name_pattern(self):
        """
        函数级注释：测试名称模式匹配
        内部逻辑：测试各种名称模式
        """
        # 内部逻辑：测试匹配的名称
        matching_names = [
            "bge-large-zh",
            "e5-base-v2",
            "gte-small",
            "sentence-transformer",
            "mpnet-base",
            "distilbert-model",
            "minilm-l6",
            "embedding-model",
            "EMBEDDING-MODEL",  # 大写也应该匹配
        ]

        for name in matching_names:
            result = LocalModelService._check_name_pattern(name)
            assert result is True, f"Failed for: {name}"

        # 内部逻辑：测试不匹配的名称
        non_matching_names = [
            "llama-2-7b",
            "mistral-7b",
            "gpt-4",
            "chat-model",
        ]

        for name in non_matching_names:
            result = LocalModelService._check_name_pattern(name)
            assert result is False, f"Should not match: {name}"

    def test_has_config_file(self, tmp_path):
        """
        函数级注释：测试config文件检测
        内部逻辑：创建不同类型的config文件
        参数：
            tmp_path: pytest临时路径fixture
        """
        # 内部逻辑：测试config.json
        dir1 = tmp_path / "dir1"
        dir1.mkdir()
        (dir1 / "config.json").write_text("{}")
        assert LocalModelService._has_config_file(dir1) is True

        # 内部逻辑：测试config.yaml
        dir2 = tmp_path / "dir2"
        dir2.mkdir()
        (dir2 / "config.yaml").write_text("test: value")
        assert LocalModelService._has_config_file(dir2) is True

        # 内部逻辑：测试config.yml
        dir3 = tmp_path / "dir3"
        dir3.mkdir()
        (dir3 / "config.yml").write_text("test: value")
        assert LocalModelService._has_config_file(dir3) is True

        # 内部逻辑：测试没有config文件
        dir4 = tmp_path / "dir4"
        dir4.mkdir()
        assert LocalModelService._has_config_file(dir4) is False

    def test_has_model_files(self, tmp_path):
        """
        函数级注释：测试模型文件检测
        内部逻辑：创建不同类型的模型文件
        参数：
            tmp_path: pytest临时路径fixture
        """
        # 内部逻辑：测试.bin文件
        dir1 = tmp_path / "dir1"
        dir1.mkdir()
        (dir1 / "model.bin").write_bytes(b"data")
        assert LocalModelService._has_model_files(dir1) is True

        # 内部逻辑：测试.safetensors文件
        dir2 = tmp_path / "dir2"
        dir2.mkdir()
        (dir2 / "model.safetensors").write_bytes(b"data")
        assert LocalModelService._has_model_files(dir2) is True

        # 内部逻辑：测试.pt文件
        dir3 = tmp_path / "dir3"
        dir3.mkdir()
        (dir3 / "model.pt").write_bytes(b"data")
        assert LocalModelService._has_model_files(dir3) is True

        # 内部逻辑：测试.pth文件
        dir4 = tmp_path / "dir4"
        dir4.mkdir()
        (dir4 / "model.pth").write_bytes(b"data")
        assert LocalModelService._has_model_files(dir4) is True

        # 内部逻辑：测试没有模型文件
        dir5 = tmp_path / "dir5"
        dir5.mkdir()
        (dir5 / "text.txt").write_text("not a model")
        assert LocalModelService._has_model_files(dir5) is False

    def test_get_model_info_not_exist(self):
        """
        函数级注释：测试获取不存在模型的信息
        内部逻辑：mock 目录不存在
        """
        with patch('app.services.local_model_service.LocalModelService._get_model_dir', return_value=Path('/nonexistent')):
            result = LocalModelService.get_model_info("test-model")

            assert result["name"] == "test-model"
            assert result["exists"] is False

    def test_get_model_info_success(self, tmp_path):
        """
        函数级注释：测试成功获取模型信息
        内部逻辑：创建模型目录和文件
        参数：
            tmp_path: pytest临时路径fixture
        """
        model_dir = tmp_path / "bge-model"
        model_dir.mkdir()

        # 内部逻辑：创建文件
        (model_dir / "config.json").write_text('{"model_type": "embedding"}')
        (model_dir / "model.bin").write_bytes(b"x" * 1000)  # 1KB
        (model_dir / "readme.txt").write_text("test")

        with patch('app.services.local_model_service.LocalModelService._get_model_dir', return_value=tmp_path):
            result = LocalModelService.get_model_info("bge-model")

            assert result["name"] == "bge-model"
            assert result["exists"] is True
            assert result["file_count"] == 3
            assert result["has_config"] is True
            assert "config" in result

    def test_get_model_info_with_json_config(self, tmp_path):
        """
        函数级注释：测试获取带JSON config的模型信息
        内部逻辑：创建包含config.json的目录
        参数：
            tmp_path: pytest临时路径fixture
        """
        model_dir = tmp_path / "e5-model"
        model_dir.mkdir()

        config_content = '{"model_type": "embedding", "hidden_size": 768}'
        (model_dir / "config.json").write_text(config_content)

        with patch('app.services.local_model_service.LocalModelService._get_model_dir', return_value=tmp_path):
            result = LocalModelService.get_model_info("e5-model")

            assert result["exists"] is True
            assert result["config"] is not None
            assert result["config"]["model_type"] == "embedding"

    def test_get_model_info_invalid_json(self, tmp_path):
        """
        函数级注释：测试config.json为无效JSON时的行为
        内部逻辑：创建包含无效JSON的config文件
        参数：
            tmp_path: pytest临时路径fixture
        """
        model_dir = tmp_path / "embed-model"
        model_dir.mkdir()

        (model_dir / "config.json").write_text("invalid json {{{")

        with patch('app.services.local_model_service.LocalModelService._get_model_dir', return_value=tmp_path):
            result = LocalModelService.get_model_info("embed-model")

            assert result["exists"] is True
            assert result["has_config"] is True
            assert result["config"] is None  # JSON解析失败

    def test_scan_local_models_sorted(self, tmp_path):
        """
        函数级注释：测试模型列表按名称排序
        内部逻辑：创建多个模型目录，验证排序
        参数：
            tmp_path: pytest临时路径fixture
        """
        # 内部逻辑：创建模型目录（非字母顺序，使用embedding相关名称）
        for name in ["z-embedding", "a-embed", "m-bge-model"]:
            model_dir = tmp_path / name
            model_dir.mkdir()
            (model_dir / "config.json").write_text("{}")

        with patch('app.services.local_model_service.LocalModelService._get_model_dir', return_value=tmp_path):
            result = LocalModelService.scan_local_models()

            # 内部逻辑：验证排序（按字母顺序）
            assert result["models"] == ["a-embed", "m-bge-model", "z-embedding"]

    def test_scan_local_models_skips_hidden_directories(self, tmp_path):
        """
        函数级注释：测试跳过隐藏目录
        内部逻辑：创建隐藏目录，验证被跳过
        参数：
            tmp_path: pytest临时路径fixture
        """
        # 内部逻辑：创建隐藏目录
        hidden_dir = tmp_path / ".hidden-model"
        hidden_dir.mkdir()
        (hidden_dir / "config.json").write_text("{}")

        # 内部逻辑：创建普通目录
        normal_dir = tmp_path / "embedding-model"
        normal_dir.mkdir()
        (normal_dir / "config.json").write_text("{}")

        with patch('app.services.local_model_service.LocalModelService._get_model_dir', return_value=tmp_path):
            result = LocalModelService.scan_local_models()

            assert ".hidden-model" not in result["models"]
            assert "embedding-model" in result["models"]

    def test_scan_local_models_skips_files(self, tmp_path):
        """
        函数级注释：测试跳过文件（只处理目录）
        内部逻辑：在根目录创建文件，验证被跳过
        参数：
            tmp_path: pytest临时路径fixture
        """
        # 内部逻辑：在根目录创建文件
        (tmp_path / "file.txt").write_text("not a directory")

        with patch('app.services.local_model_service.LocalModelService._get_model_dir', return_value=tmp_path):
            result = LocalModelService.scan_local_models()

            assert result["models"] == []

    def test_embedding_patterns_constant(self):
        """
        函数级注释：测试EMBEDDING_PATTERNS常量
        内部逻辑：验证常量包含预期的模式
        """
        patterns = LocalModelService.EMBEDDING_PATTERNS

        assert "embed" in patterns
        assert "bge" in patterns
        assert "e5" in patterns
        assert "gte" in patterns
        assert "sentence" in patterns
        assert "paraphrase" in patterns
        assert "mpnet" in patterns
        assert "distilbert" in patterns
        assert "minilm" in patterns

    def test_model_file_extensions_constant(self):
        """
        函数级注释：测试MODEL_FILE_EXTENSIONS常量
        内部逻辑：验证常量包含预期的扩展名
        """
        extensions = LocalModelService.MODEL_FILE_EXTENSIONS

        assert ".bin" in extensions
        assert ".safetensors" in extensions
        assert ".pt" in extensions
        assert ".pth" in extensions

    def test_get_model_info_size_calculation(self, tmp_path):
        """
        函数级注释：测试模型大小计算
        内部逻辑：创建不同大小的文件，验证计算正确
        参数：
            tmp_path: pytest临时路径fixture
        """
        model_dir = tmp_path / "test-model"
        model_dir.mkdir()

        # 内部逻辑：创建文件（1MB + 500KB）
        (model_dir / "file1.bin").write_bytes(b"x" * (1024 * 1024))
        (model_dir / "file2.bin").write_bytes(b"x" * (500 * 1024))

        with patch('app.services.local_model_service.LocalModelService._get_model_dir', return_value=tmp_path):
            result = LocalModelService.get_model_info("test-model")

            # 内部逻辑：验证大小约1.5MB
            assert 1.4 < result["size_mb"] < 1.6

    def test_is_valid_embedding_model_name_not_match_has_files(self, tmp_path):
        """
        函数级注释：测试名称不匹配但有文件时的验证
        内部逻辑：创建不包含embedding关键词但有模型文件的目录
        参数：
            tmp_path: pytest临时路径fixture
        """
        model_dir = tmp_path / "llama-model"
        model_dir.mkdir()
        (model_dir / "model.bin").write_bytes(b"data")

        result = LocalModelService.is_valid_embedding_model(model_dir)

        # 内部逻辑：名称不匹配，应该返回False
        assert result is False
