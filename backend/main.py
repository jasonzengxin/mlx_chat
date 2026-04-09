"""
FastAPI 应用入口

功能:
- 应用创建
- 路由注册
- 中间件配置
"""

import os
from contextlib import asynccontextmanager
from typing import Optional

import aiosqlite
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.routers import chat, sessions, models, usage, settings, openai, model_registry
from backend.database import Database
from backend.mlx_instance import init_mlx_service
from backend.services.model_registry_service import ModelRegistryService
from backend.utils.model_detector import detect_local_models


# 数据库文件路径
DB_PATH = os.path.join(os.path.dirname(__file__), "mlx_chat.db")


async def get_database() -> Database:
    """获取数据库连接"""
    conn = await aiosqlite.connect(DB_PATH)
    conn.row_factory = aiosqlite.Row

    # 确保表存在
    await conn.executescript('''
        CREATE TABLE IF NOT EXISTS api_keys (
            id TEXT PRIMARY KEY,
            key_hash TEXT UNIQUE NOT NULL,
            key_prefix TEXT NOT NULL,
            name TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_used_at TIMESTAMP,
            is_active BOOLEAN DEFAULT 1
        );
        CREATE TABLE IF NOT EXISTS sessions (
            id TEXT PRIMARY KEY,
            api_key_id TEXT NOT NULL,
            name TEXT NOT NULL,
            model TEXT NOT NULL,
            temperature REAL DEFAULT 0.7,
            max_tokens INTEGER DEFAULT 4096,
            system_prompt TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS messages (
            id TEXT PRIMARY KEY,
            session_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS usage_logs (
            id TEXT PRIMARY KEY,
            api_key_id TEXT NOT NULL,
            session_id TEXT,
            model TEXT NOT NULL,
            input_tokens INTEGER DEFAULT 0,
            output_tokens INTEGER DEFAULT 0,
            time_ms INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS supported_models (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            model_id TEXT UNIQUE NOT NULL,
            description TEXT DEFAULT '',
            params_count TEXT DEFAULT '',
            quantization TEXT DEFAULT '',
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    ''')
    await conn.commit()

    return Database(conn)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时初始化
    init_mlx_service()

    # 连接数据库 (测试时可能已设置)
    if not hasattr(app.state, "db") or app.state.db is None:
        app.state.db = await get_database()

    # 初始化模型注册表并检测新模型
    registry = ModelRegistryService(app.state.db)
    await registry.initialize()
    app.state.model_registry = registry

    # 检测本地模型，自动注册未在数据库中的模型
    await _auto_register_local_models(registry)

    yield

    # 关闭时清理资源
    if hasattr(app.state, "db") and app.state.db is not None:
        await app.state.db.close()


async def _auto_register_local_models(registry: ModelRegistryService):
    """自动检测并注册本地模型"""
    try:
        local_models = detect_local_models()
        if not local_models:
            return

        registered_models = await registry.list_models(active_only=False)
        registered_ids = {m.model_id for m in registered_models}

        new_models = []
        for model in local_models:
            if model["model_id"] not in registered_ids:
                await registry.add_model(
                    name=model["name"],
                    model_id=model["model_id"],
                    description=model.get("description", ""),
                    params_count=model.get("params_count", ""),
                    quantization=model.get("quantization", "")
                )
                new_models.append(model)

        if new_models:
            print(f"\n[MLX Chat] 检测到 {len(new_models)} 个新本地模型，已自动注册:")
            for m in new_models:
                print(f"  - {m['name']} ({m['model_id']})")
            print()
    except Exception as e:
        # 不影响启动
        print(f"[MLX Chat] 模型检测失败: {e}")


def create_app(db: Optional[Database] = None) -> FastAPI:
    """
    创建 FastAPI 应用

    Args:
        db: 可选的数据库实例 (测试时使用)
             生产环境会自动连接 mlx_chat.db
    """
    app = FastAPI(
        title="MLX Chat API",
        description="Apple Silicon MLX 模型对话 API，支持 Web UI 和 Chrome 插件扩展",
        version="1.0.0",
        lifespan=lifespan,
    )

    # 设置数据库 (测试时传入)
    if db is not None:
        app.state.db = db

    # CORS 配置
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:3000",      # Vue 开发服务器
            "http://localhost:8000",      # 后端直接访问
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 注册路由
    app.include_router(chat.router, prefix="/api/v1/chat", tags=["Chat"])
    app.include_router(sessions.router, prefix="/api/v1/sessions", tags=["Sessions"])
    app.include_router(models.router, prefix="/api/v1/models", tags=["Models"])
    app.include_router(usage.router, prefix="/api/v1/usage", tags=["Usage"])
    app.include_router(settings.router, prefix="/api/v1/settings", tags=["Settings"])
    app.include_router(model_registry.router, prefix="/api/v1/model-registry", tags=["Model Registry"])
    app.include_router(openai.router, prefix="/v1", tags=["OpenAI"])  # OpenAI 兼容端点

    # 健康检查
    @app.get("/health")
    async def health_check():
        return {"status": "ok"}

    @app.get("/")
    async def root():
        return {
            "name": "MLX Chat API",
            "version": "1.0.0",
            "docs": "/docs"
        }

    return app


# 为了测试，创建一个简单的应用实例
app = create_app()
