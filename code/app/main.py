"""
上海宇羲伏天智能科技有限公司出品

文件级注释：应用程序入口文件
内部逻辑：初始化 FastAPI 实例，配置路由、中间件和异常处理
"""

import os

# ============================================================================
# 内部逻辑：动态加载环境配置文件
# 加载策略：
#   1. 始终加载 .env（基础配置）
#   2. 如果设置了APP_ENV，再加载 .env.{APP_ENV}（补充配置）
#
# 配置优先级（从高到低）：
#   1. 数据库模型配置（运行时注入）- 通过 ModelConfigService._reload_config
#   2. 环境变量（docker run -e）- 系统环境变量，不被 .env 文件覆盖
#   3. .env.{APP_ENV} - 环境特定配置
#   4. .env - 基础配置文件
#   5. 代码默认值 - BaseSettings 类属性
#
# 注意：必须在导入settings之前执行load_dotenv
# ============================================================================
from dotenv import load_dotenv

# 内部逻辑：先加载基础配置文件（不覆盖已存在的环境变量）
load_dotenv(".env", override=False)

# 内部逻辑：根据APP_ENV环境变量加载额外的环境特定配置
# 注意：使用 os.environ.get() 直接从系统环境读取，避免被 .env 覆盖
app_env = os.environ.get("APP_ENV", "")
if app_env:
    env_file = f".env.{app_env}"
    # 内部逻辑：override=False 确保系统环境变量（docker run -e）优先级最高
    load_dotenv(env_file, override=False)  # 补充同名变量，不覆盖系统环境变量

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.openapi.docs import get_swagger_ui_html
from sqlalchemy.ext.asyncio import AsyncEngine
from loguru import logger
from app.core.config import settings
from app.api.v1.api import api_router
from app.models.models import Base
from app.db.factory import DatabaseFactory
from app.core.di.service_container import get_container, ServiceLifetime
from app.services.chat_service import ChatService
from app.services.ingest_service import IngestService
from app.services.search_service import SearchService
from app.core.middleware import create_validation_middleware, ValidationChainMiddleware, ServiceScopeMiddleware
from app.core.validation_chain import ValidationChainFactory
from app.services.chat.service_initializer import initialize_chat_services


async def init_database():
    """
    函数级注释：异步初始化数据库表结构
    内部逻辑：确保数据目录存在，然后创建所有数据库表
    返回值：无
    """
    # 内部逻辑：确保上传文件目录存在
    os.makedirs(settings.UPLOAD_FILES_PATH, exist_ok=True)

    # 内部逻辑：获取数据库引擎（通过工厂）
    engine: AsyncEngine = await DatabaseFactory.get_engine()

    try:
        # 内部逻辑：创建所有表（如果不存在）
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        provider_name = DatabaseFactory.get_current_provider_name()
        db_address = settings.DB_HOST if settings.DATABASE_PROVIDER == "postgresql" else settings.SQLITE_DB_PATH
        logger.info(f"数据库初始化完成: {provider_name} @ {db_address}")
    except Exception as e:
        # 内部逻辑：异常处理
        error_msg = str(e)
        if "already exists" not in error_msg:
            logger.error(f"数据库初始化失败: {error_msg}")
            raise
        else:
            logger.info("数据库表已存在，跳过初始化")


def init_service_container():
    """
    函数级注释：初始化服务容器（依赖注入）
    设计模式：依赖注入模式 - 集中管理服务注册
    内部逻辑：注册所有核心服务到容器，支持自动依赖注入
    返回值：无
    """
    # 内部变量：获取全局服务容器
    container = get_container()

    # 内部逻辑：注册聊天相关服务（优化：统一初始化）
    # 设计模式：依赖注入模式 + 服务定位器模式
    initialize_chat_services(container)

    # 内部逻辑：注册核心服务（作用域生命周期）
    # 作用域服务：每个请求创建一个实例，同一请求内共享

    # 注册聊天服务（外观模式）
    container.register_scoped(
        service_type=ChatService,
        factory=ChatService
    )

    # 注册数据摄入服务
    container.register_scoped(
        service_type=IngestService,
        factory=IngestService
    )

    # 注册搜索服务
    container.register_scoped(
        service_type=SearchService,
        factory=SearchService
    )

    logger.info("服务容器初始化完成，已注册核心服务")


def create_app() -> FastAPI:
    """
    函数级注释：创建并配置 FastAPI 应用程序实例
    返回值：FastAPI - 配置好的应用程序实例
    """
    # 内部变量：初始化 FastAPI 实例
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        openapi_url=f"{settings.API_V1_STR}/openapi.json"
    )

    # 内部逻辑：配置 CORS 中间件，允许跨域请求
    if settings.BACKEND_CORS_ORIGINS:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    # 内部逻辑：配置服务作用域中间件
    # 设计模式：中间件模式 + 作用域模式
    # 职责：为每个请求自动创建和释放服务作用域
    # 注意：必须在验证链中间件之前注册，确保所有依赖注入可用
    app.add_middleware(ServiceScopeMiddleware)

    # 内部逻辑：配置验证链中间件
    # 设计模式：责任链模式 - 统一API请求验证流程
    # 内部变量：创建不强制认证的验证中间件
    app.add_middleware(
        ValidationChainMiddleware,
        chain_factory=lambda permissions=None: ValidationChainFactory.create_api_chain(permissions, strict=False),
        skip_paths=[
            "/",
            "/health",
            "/api/v1/health",
            "/api/v1/ingest",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/static",
        ]
    )

    # 内部逻辑：包含 API 路由
    app.include_router(api_router, prefix=settings.API_V1_STR)

    # 内部逻辑：添加测试端点，验证路由系统
    @app.get(f"{settings.API_V1_STR}/test-health")
    async def test_health():
        """测试端点"""
        return {"status": "ok", "message": "路由系统正常"}

    # 内部逻辑：挂载静态文件目录（用于本地 Swagger UI 资源）
    # 注意：如果静态目录不存在则跳过挂载
    import os
    static_dir = os.path.join(os.path.dirname(__file__), "static")
    if os.path.exists(static_dir):
        app.mount("/static", StaticFiles(directory=static_dir), name="static")

    # 内部逻辑：配置启动事件，自动初始化数据库、服务容器和预加载配置
    @app.on_event("startup")
    async def startup_event():
        """
        函数级注释：应用启动时执行的事件处理器
        内部逻辑：初始化数据库表结构 + 服务容器 + 预加载模型配置
        设计模式：依赖注入模式 - 在启动时初始化服务容器
        """
        # 1. 初始化数据库表结构
        await init_database()

        # 2. 初始化服务容器（依赖注入）
        # 设计模式：依赖注入模式 - 集中管理服务注册
        init_service_container()

        # 3. 预加载默认配置
        from app.core.initializers import init_default_configs
        import app.db.session as session_module

        # 内部逻辑：确保会话工厂已初始化
        if session_module.AsyncSessionLocal is None:
            await session_module.init_session_factory()

        # 内部逻辑：使用会话工厂创建会话并初始化配置
        # 注意：必须从模块重新获取 AsyncSessionLocal，因为导入时它可能是 None
        async with session_module.AsyncSessionLocal() as db:
            await init_default_configs(db)

        logger.info("应用启动完成")

    @app.on_event("shutdown")
    async def shutdown_event():
        """
        函数级注释：应用关闭时执行的事件处理器
        内部逻辑：关闭数据库引擎
        """
        await DatabaseFactory.dispose_engine()

    @app.get("/")
    async def root():
        """
        函数级注释：根路径健康检查接口
        返回值：dict - 包含欢迎信息和版本号
        """
        return {
            "message": f"欢迎来到 {settings.APP_NAME} API",
            "version": settings.APP_VERSION,
            "status": "online"
        }

    # 内部逻辑：直接定义健康检查端点（不使用 router，避免路由冲突）
    @app.get(f"{settings.API_V1_STR}/health")
    async def health_check():
        """
        函数级注释：健康检查端点
        返回值：dict - 包含健康状态信息
        """
        from datetime import datetime
        logger.info("Health check endpoint called (direct)")
        return {
            "success": True,
            "data": {
                "status": "healthy",
                "service": "knowledge-agentic-api",
                "timestamp": datetime.utcnow().isoformat()
            },
            "message": "系统运行正常"
        }

    # 内部逻辑：自定义 Swagger UI 路由，使用本地静态资源
    # 检测本地资源是否存在，存在则使用本地资源，否则使用默认配置
    @app.get("/docs", include_in_schema=False)
    async def custom_swagger_ui_html():
        """
        函数级注释：自定义 Swagger UI 页面
        内部逻辑：优先使用本地静态资源，避免外部网络依赖
        返回值：HTMLResponse - Swagger UI 页面
        """
        # 内部变量：检查本地静态资源是否存在
        import os
        static_dir = os.path.join(os.path.dirname(__file__), "static")
        use_local = os.path.exists(os.path.join(static_dir, "swagger-ui", "swagger-ui-bundle.js"))

        if use_local:
            # 内部逻辑：使用本地静态资源
            return get_swagger_ui_html(
                openapi_url=f"{settings.API_V1_STR}/openapi.json",
                title=f"{settings.APP_NAME} - Swagger UI",
                oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url,
                swagger_js_url="/static/swagger-ui/swagger-ui-bundle.js",
                swagger_css_url="/static/swagger-ui/swagger-ui.css",
                swagger_favicon_url="/static/swagger-ui/favicon-32x32.png",
            )
        else:
            # 内部逻辑：使用默认配置（需要外部网络）
            # 静默失败，让 FastAPI 使用内置的默认处理
            from fastapi.responses import RedirectResponse
            # 如果本地资源不存在，尝试重定向到 redoc（它通常加载更快）
            return RedirectResponse(url="/redoc")

    return app

# 类级/全局变量：应用实例
app = create_app()

if __name__ == "__main__":
    import uvicorn
    # 启动命令：运行 FastAPI 服务
    uvicorn.run(app, host="0.0.0.0", port=settings.PORT)




