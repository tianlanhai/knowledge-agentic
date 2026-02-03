"""
上海宇羲伏天智能科技有限公司出品

文件级注释：LLM工厂类
内部逻辑：使用抽象工厂模式根据配置创建不同提供商的LLM实例，支持运行时热切换
设计模式：抽象工厂模式 + 桥接模式（桥接到 ai_provider 模块）
参考项目：easy-dataset-file

重构说明：
    - 使用新的 ai_provider 模块创建实例，消除 if-else 分支
    - 保持原有接口不变，确保向后兼容
    - 内部通过 AIProviderFactoryRegistry 动态获取工厂
"""

from typing import Dict, Any, TYPE_CHECKING
from langchain_core.language_models import BaseChatModel
from app.core.config import settings
from app.core.base_factory import BaseFactory
from app.core.endpoint_utils import EndpointUtils
from app.core.ai_provider import (
    AIProviderType,
    AIProviderConfig,
    AIProviderFactoryRegistry,
    create_ai_provider,
)
from loguru import logger

# 内部逻辑：类型注解导入，仅在类型检查时导入，避免循环依赖
if TYPE_CHECKING:
    from langchain_community.chat_models import ChatOllama
    from langchain_community.chat_models import ChatZhipuAI

# 内部逻辑：运行时导入 ChatOpenAI（用于 moonshot 和 openai 提供商）
try:
    from langchain_openai import ChatOpenAI
except ImportError:
    ChatOpenAI = None


class LLMFactory(BaseFactory[BaseChatModel]):
    """
    类级注释：LLM工厂类，负责根据配置创建不同类型的LLM实例
    设计模式：抽象工厂模式 + 桥接模式（桥接到 ai_provider）
    职责：
        1. 根据提供商创建对应的LLM实例
        2. 支持运行时配置热切换（继承自 BaseFactory）
        3. 实例缓存优化性能（继承自 BaseFactory）
        4. 桥接到 ai_provider 模块，消除 if-else 分支
    """

    # 内部常量：支持的LLM提供商列表
    SUPPORTED_PROVIDERS = {
        "ollama": "Ollama本地模型",
        "zhipuai": "智谱AI",
        "minimax": "MiniMax",
        "moonshot": "月之暗面",
        "openai": "OpenAI",
        "deepseek": "DeepSeek"
    }

    # 内部常量：提供商到枚举的映射
    _PROVIDER_ENUM_MAP = {
        "ollama": AIProviderType.OLLAMA,
        "zhipuai": AIProviderType.ZHIPUAI,
        "minimax": AIProviderType.MINIMAX,
        "moonshot": AIProviderType.MOONSHOT,
        "openai": AIProviderType.OPENAI,
        "deepseek": AIProviderType.DEEPSEEK,
    }

    # ========================================================================
    # 实现基类抽象方法
    # ========================================================================

    @classmethod
    def _get_default_config(cls) -> Dict[str, Any]:
        """
        函数级注释：获取默认配置（实现基类抽象方法）
        内部逻辑：从环境变量 settings 获取默认配置
        返回值：默认配置字典
        """
        return {
            "provider": settings.LLM_PROVIDER.lower(),
            "model": settings.CHAT_MODEL,
            "endpoint": settings.OLLAMA_BASE_URL,
            "api_key": "",
            "temperature": 0,
            "num_gpu": settings.OLLAMA_NUM_GPU
        }

    @classmethod
    def _create_by_provider(cls, provider: str, config: Dict[str, Any], **kwargs) -> BaseChatModel:
        """
        函数级注释：根据提供商创建对应的LLM实例（实现基类抽象方法）
        内部逻辑：使用 ai_provider 模块的注册表获取工厂，消除 if-else 分支
        设计模式：抽象工厂模式 + 注册表模式
        参数：
            provider: 提供商ID
            config: 配置字典
            **kwargs: 额外参数（如 streaming）
        返回值：LLM实例
        """
        # 内部逻辑：将提供商字符串转换为枚举类型
        provider_enum = cls._get_provider_enum(provider)

        # 内部逻辑：构建 AIProviderConfig
        ai_config = AIProviderConfig(
            provider_type=provider_enum,
            api_key=config.get("api_key"),
            base_url=config.get("endpoint"),
            model=config.get("model"),
            temperature=config.get("temperature", 0),
            max_tokens=config.get("max_tokens"),
            top_p=config.get("top_p"),
            **kwargs
        )

        # 内部逻辑：从注册表获取工厂并创建实例（替代 if-else 分支）
        factory = AIProviderFactoryRegistry.get_factory(provider_enum)
        llm = factory.create_llm(ai_config)

        # 内部逻辑：如果需要流式输出，重新创建支持流式的实例
        if kwargs.get("streaming") and hasattr(llm, "model_kwargs"):
            llm.streaming = True

        return llm

    @classmethod
    def _get_provider_enum(cls, provider: str) -> AIProviderType:
        """
        函数级注释：将提供商字符串转换为枚举类型
        内部逻辑：使用映射表，避免 if-else 分支
        参数：
            provider: 提供商ID字符串
        返回值：AIProviderType 枚举
        """
        provider_lower = provider.lower()
        if provider_lower not in cls._PROVIDER_ENUM_MAP:
            supported_list = list(cls.SUPPORTED_PROVIDERS.keys())
            raise ValueError(
                f"不支持的LLM提供商: {provider}。"
                f"支持的提供商: {supported_list}"
            )
        return cls._PROVIDER_ENUM_MAP[provider_lower]

    # ========================================================================
    # 公共接口方法
    # ========================================================================

    @classmethod
    def create_llm(cls, streaming: bool = False) -> BaseChatModel:
        """
        函数级注释：根据配置创建LLM实例（支持热切换）
        内部逻辑：解析配置 -> 检查缓存 -> 创建/返回实例
        参数：
            streaming: 是否启用流式输出，默认False
        返回值：BaseChatModel - LLM实例
        异常：ValueError - 当配置的提供商不支持或缺少必要配置时
        """
        # 内部逻辑：解析配置（使用基类方法）
        config = cls._resolve_config()
        provider = config.get("provider", "ollama")

        # 内部逻辑：Guard Clauses - 验证提供商是否支持
        if not cls._is_supported_provider(provider):
            supported_list = list(cls.SUPPORTED_PROVIDERS.keys())
            raise ValueError(
                f"不支持的LLM提供商: {provider}。"
                f"支持的提供商: {supported_list}"
            )

        # 内部逻辑：非流式模式下检查缓存
        cache_key = cls._get_cache_key(config)
        if not streaming and cache_key in cls._instance_cache:
            logger.debug(f"使用缓存的LLM实例: {cache_key}")
            return cls._instance_cache[cache_key]

        # 内部逻辑：根据提供商创建对应的LLM实例
        try:
            llm = cls._create_by_provider(provider, config, streaming=streaming)

            # 内部逻辑：缓存非流式实例
            if not streaming:
                cls._instance_cache[cache_key] = llm

            return llm
        except Exception as e:
            # 内部逻辑：捕获并记录创建失败的信息
            logger.error(f"创建{provider} LLM实例失败: {str(e)}")
            raise

    @classmethod
    def create_from_model_config(cls, model_config, streaming: bool = False) -> BaseChatModel:
        """
        函数级注释：从模型配置对象创建LLM实例
        内部逻辑：将配置对象转为字典 -> 设置运行时配置 -> 创建实例
        参数：
            model_config: ModelConfig对象
            streaming: 是否流式输出
        返回值：LLM实例
        """
        config_dict = {
            "provider": model_config.provider_id,
            "model": model_config.model_name,
            "endpoint": model_config.endpoint,
            "api_key": model_config.api_key,
            "temperature": model_config.temperature,
            "max_tokens": model_config.max_tokens,
            "top_p": model_config.top_p
        }
        cls.set_runtime_config(config_dict)
        return cls.create_llm(streaming=streaming)

    @staticmethod
    def get_current_provider() -> str:
        """
        函数级注释：获取当前配置的LLM提供商
        返回值：str - 提供商名称
        """
        return settings.LLM_PROVIDER.lower()

    @classmethod
    def get_current_model(cls) -> str:
        """
        函数级注释：获取当前配置的模型名称
        内部逻辑：使用映射表，避免 if-else 分支
        返回值：str - 模型名称
        """
        provider = cls.get_current_provider()

        # 内部逻辑：使用映射表获取模型配置名称
        setting_name = cls._get_model_setting_name(provider)

        # 内部逻辑：从 settings 获取模型值
        return cls._get_model_value(setting_name)

    # ========================================================================
    # 内部辅助方法
    # ========================================================================

    # 内部常量：提供商模型名称映射表（替代 if-else 分支）
    _PROVIDER_MODEL_MAP = {
        "ollama": "CHAT_MODEL",
        "zhipuai": "ZHIPUAI_MODEL",
        "minimax": "MINIMAX_MODEL",
        "moonshot": "MOONSHOT_MODEL",
        "openai": "OPENAI_MODEL",
        "deepseek": "DEEPSEEK_MODEL",
    }

    @classmethod
    def _get_model_setting_name(cls, provider: str) -> str:
        """
        函数级注释：获取提供商对应的模型配置名称
        内部逻辑：使用映射表，避免 if-else 分支
        参数：
            provider: 提供商ID
        返回值：配置名称
        """
        return cls._PROVIDER_MODEL_MAP.get(provider, "CHAT_MODEL")

    @classmethod
    def _get_model_value(cls, setting_name: str) -> str:
        """
        函数级注释：从 settings 获取模型值
        参数：
            setting_name: 配置名称
        返回值：模型名称
        """
        return getattr(settings, setting_name, "unknown")

    # ========================================================================
    # 提供商特定的创建方法（私有方法）
    # ========================================================================

    @classmethod
    def _create_ollama_llm(cls, config: Dict[str, Any], streaming: bool = False) -> BaseChatModel:
        """
        函数级注释：创建Ollama LLM实例
        内部逻辑：构造Ollama配置 -> 规范化endpoint -> 传递GPU参数 -> 返回ChatOllama实例
        参数：
            config: 配置字典
            streaming: 是否启用流式输出
        返回值：ChatOllama实例
        """
        # 内部变量：构造Ollama配置选项
        ollama_options: Dict[str, Any] = {}

        # 内部逻辑：添加GPU配置（Guard Clause）
        num_gpu = config.get("num_gpu", settings.OLLAMA_NUM_GPU)
        if num_gpu > 0:
            ollama_options.update({
                "num_gpu": num_gpu,
                "num_thread": num_gpu
            })

        # 内部逻辑：使用 EndpointUtils 规范化 endpoint
        # Ollama API 格式：http://host:port/api/chat，所以 base 应该是 http://host:port
        endpoint = config.get("endpoint", settings.OLLAMA_BASE_URL)
        normalized_endpoint = EndpointUtils.normalize_ollama_endpoint(endpoint)

        # 内部变量：创建并返回ChatOllama实例
        llm = ChatOllama(
            base_url=normalized_endpoint,
            model=config.get("model", settings.CHAT_MODEL),
            temperature=config.get("temperature", 0),
            streaming=streaming,
            options=ollama_options if ollama_options else None
        )

        logger.info(f"已创建Ollama LLM实例，模型: {config.get('model')}, endpoint: {normalized_endpoint}")
        return llm

    @classmethod
    def _create_zhipuai_llm(cls, config: Dict[str, Any], streaming: bool = False) -> BaseChatModel:
        """
        函数级注释：创建智谱AI LLM实例
        内部逻辑：验证API密钥 -> 规范化端点路径 -> 构造配置 -> 返回ChatZhipuAI实例
        参数：
            config: 配置字典
            streaming: 是否启用流式输出
        返回值：ChatZhipuAI实例
        异常：ValueError - 当API密钥为空时
        """
        api_key = config.get("api_key", settings.zhipuai_llm_api_key)

        # 内部逻辑：Guard Clauses - 验证API密钥
        if not api_key:
            raise ValueError("使用智谱AI需要配置API密钥。")

        # 内部逻辑：使用 EndpointUtils 规范化智谱AI端点路径
        # 支持用户只配置 base URL（如 https://open.bigmodel.cn/api/coding/paas/v4）
        # 或完整路径（如 https://open.bigmodel.cn/api/paas/v4/chat/completions）
        endpoint = config.get("endpoint", settings.zhipuai_llm_base_url)
        normalized_endpoint = EndpointUtils.normalize_zhipuai_endpoint(endpoint, "/chat/completions")

        # 内部变量：创建并返回ChatZhipuAI实例
        # 内部逻辑：注意 ChatZhipuAI 使用 api_base 参数而非 base_url
        llm = ChatZhipuAI(
            api_key=api_key,
            model=config.get("model", settings.ZHIPUAI_MODEL),
            api_base=normalized_endpoint,
            temperature=config.get("temperature", 0),
            streaming=streaming
        )

        logger.info(f"已创建智谱AI LLM实例，模型: {config.get('model')}, 端点: {normalized_endpoint}")
        return llm

    @classmethod
    def _create_minimax_llm(cls, config: Dict[str, Any], streaming: bool = False) -> BaseChatModel:
        """
        函数级注释：创建MiniMax LLM实例
        内部逻辑：验证API密钥和Group ID -> 导入MiniMax客户端 -> 构造配置 -> 返回实例
        参数：
            config: 配置字典
            streaming: 是否启用流式输出
        返回值：MiniMax LLM实例
        异常：ValueError - 当API密钥或Group ID为空时
        """
        # 内部逻辑：Guard Clauses - 验证API密钥和Group ID
        api_key = config.get("api_key", settings.MINIMAX_API_KEY)
        if not api_key:
            raise ValueError("使用MiniMax需要配置API密钥")

        group_id = config.get("group_id", settings.MINIMAX_GROUP_ID)
        if not group_id:
            raise ValueError("使用MiniMax需要配置Group ID")

        try:
            # 内部逻辑：动态导入MiniMax客户端（避免未安装时导入失败）
            from langchain_community.chat_models import MiniMaxChat
        except ImportError:
            raise ImportError("未找到MiniMax依赖")

        # 内部变量：创建并返回MiniMaxChat实例
        llm = MiniMaxChat(
            api_key=api_key,
            group_id=group_id,
            model=config.get("model", settings.MINIMAX_MODEL),
            temperature=config.get("temperature", 0),
            streaming=streaming
        )

        logger.info(f"已创建MiniMax LLM实例，模型: {config.get('model')}")
        return llm

    @classmethod
    def _create_moonshot_llm(cls, config: Dict[str, Any], streaming: bool = False) -> BaseChatModel:
        """
        函数级注释：创建月之暗面（Moonshot）LLM实例
        内部逻辑：验证API密钥 -> 使用OpenAI兼容接口 -> 构造配置 -> 返回实例
        参数：
            config: 配置字典
            streaming: 是否启用流式输出
        返回值：ChatOpenAI实例（配置为Moonshot端点）
        异常：ValueError - 当API密钥为空时
        异常：ImportError - 当langchain_openai未安装时
        """
        # 内部逻辑：Guard Clauses - 检查依赖
        if ChatOpenAI is None:
            raise ImportError("使用月之暗面需要安装 langchain_openai: pip install langchain-openai")

        api_key = config.get("api_key", settings.MOONSHOT_API_KEY)

        # 内部逻辑：Guard Clauses - 验证API密钥
        if not api_key:
            raise ValueError("使用月之暗面需要配置API密钥")

        # 内部变量：创建并返回ChatOpenAI实例（配置Moonshot端点）
        llm = ChatOpenAI(
            api_key=api_key,
            base_url=config.get("endpoint", "https://api.moonshot.cn/v1"),
            model=config.get("model", settings.MOONSHOT_MODEL),
            temperature=config.get("temperature", 0),
            streaming=streaming
        )

        logger.info(f"已创建月之暗面LLM实例，模型: {config.get('model')}")
        return llm

    @classmethod
    def _create_openai_llm(cls, config: Dict[str, Any], streaming: bool = False) -> BaseChatModel:
        """
        函数级注释：创建OpenAI LLM实例
        参数：
            config: 配置字典
            streaming: 是否启用流式输出
        返回值：OpenAI LLM实例
        """
        api_key = config.get("api_key", "")

        # 内部逻辑：Guard Clauses - 验证API密钥
        if not api_key:
            raise ValueError("使用OpenAI需要配置API密钥")

        try:
            from langchain_openai import ChatOpenAI as OpenAIChat
        except ImportError:
            raise ImportError("未找到OpenAI依赖，请运行: pip install langchain-openai")

        llm = OpenAIChat(
            api_key=api_key,
            model=config.get("model", "gpt-4o"),
            base_url=config.get("endpoint", "https://api.openai.com/v1"),
            temperature=config.get("temperature", 0),
            streaming=streaming
        )

        logger.info(f"已创建OpenAI LLM实例，模型: {config.get('model')}")
        return llm

    @classmethod
    def _create_deepseek_llm(cls, config: Dict[str, Any], streaming: bool = False) -> BaseChatModel:
        """
        函数级注释：创建DeepSeek LLM实例（使用OpenAI兼容接口）
        参数：
            config: 配置字典
            streaming: 是否启用流式输出
        返回值：DeepSeek LLM实例
        """
        api_key = config.get("api_key", "")

        # 内部逻辑：Guard Clauses - 验证API密钥
        if not api_key:
            raise ValueError("使用DeepSeek需要配置API密钥")

        try:
            from langchain_openai import ChatOpenAI as OpenAIChat
        except ImportError:
            raise ImportError("未找到OpenAI依赖，请运行: pip install langchain-openai")

        llm = OpenAIChat(
            api_key=api_key,
            model=config.get("model", "deepseek-chat"),
            base_url=config.get("endpoint", "https://api.deepseek.com/v1"),
            temperature=config.get("temperature", 0),
            streaming=streaming
        )

        logger.info(f"已创建DeepSeek LLM实例，模型: {config.get('model')}")
        return llm
