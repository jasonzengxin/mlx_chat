"""
pytest 配置和 fixtures

提供测试所需的所有 fixtures:
- 数据库连接
- API Key
- 服务实例
- Mock 对象
"""

import asyncio
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

# ============================================================
# 事件循环
# ============================================================

@pytest.fixture(scope="session")
def event_loop():
    """创建会话级别的事件循环"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# ============================================================
# 数据库 Fixtures
# ============================================================

@pytest_asyncio.fixture
async def db_connection():
    """
    内存数据库连接
    每个测试函数独立的数据库实例
    """
    import aiosqlite
    from backend.database import Database

    conn = await aiosqlite.connect(":memory:")
    conn.row_factory = aiosqlite.Row

    # 创建表结构
    await conn.executescript("""
        -- API Keys 表
        CREATE TABLE api_keys (
            id TEXT PRIMARY KEY,
            key_hash TEXT UNIQUE NOT NULL,
            key_prefix TEXT NOT NULL,
            name TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_used_at TIMESTAMP,
            is_active BOOLEAN DEFAULT 1
        );

        -- 会话表
        CREATE TABLE sessions (
            id TEXT PRIMARY KEY,
            api_key_id TEXT NOT NULL,
            name TEXT NOT NULL,
            model TEXT NOT NULL,
            temperature REAL DEFAULT 0.7,
            max_tokens INTEGER DEFAULT 4096,
            system_prompt TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (api_key_id) REFERENCES api_keys(id)
        );

        -- 消息表
        CREATE TABLE messages (
            id TEXT PRIMARY KEY,
            session_id TEXT NOT NULL,
            role TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
        );

        -- 用量日志表
        CREATE TABLE usage_logs (
            id TEXT PRIMARY KEY,
            api_key_id TEXT NOT NULL,
            session_id TEXT,
            model TEXT NOT NULL,
            input_tokens INTEGER DEFAULT 0,
            output_tokens INTEGER DEFAULT 0,
            time_ms INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (api_key_id) REFERENCES api_keys(id)
        );

        -- 支持的模型表
        CREATE TABLE supported_models (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            model_id TEXT UNIQUE NOT NULL,
            description TEXT DEFAULT '',
            params_count TEXT DEFAULT '',
            quantization TEXT DEFAULT '',
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- 索引
        CREATE INDEX idx_sessions_api_key ON sessions(api_key_id);
        CREATE INDEX idx_messages_session_id ON messages(session_id);
        CREATE INDEX idx_usage_api_key ON usage_logs(api_key_id);
        CREATE INDEX idx_usage_created_at ON usage_logs(created_at);
    """)

    await conn.commit()

    # 使用 Database 辅助类包装
    db = Database(conn)

    yield db

    await db.close()


# ============================================================
# API Key Fixtures
# ============================================================

@pytest_asyncio.fixture
async def db_with_api_key(db_connection):
    """带单个 API Key 的数据库"""
    from backend.auth.api_key import APIKeyManager
    from dataclasses import dataclass

    api_key, key_hash, key_prefix = APIKeyManager.generate_key()
    key_id = f"key-{api_key[:8]}"

    await db_connection.execute(
        """
        INSERT INTO api_keys (id, key_hash, key_prefix, name)
        VALUES (?, ?, ?, ?)
        """,
        (key_id, key_hash, key_prefix, "Test Key")
    )
    await db_connection.commit()

    # 使用 dataclass 避免类作用域问题
    @dataclass
    class APIKeyInfo:
        id: str
        key: str
        key_hash: str
        key_prefix: str
        name: str

    return APIKeyInfo(
        id=key_id,
        key=api_key,
        key_hash=key_hash,
        key_prefix=key_prefix,
        name="Test Key"
    )


@pytest_asyncio.fixture
async def db_with_two_api_keys(db_connection):
    """带两个 API Keys 的数据库"""
    from backend.auth.api_key import APIKeyManager
    from dataclasses import dataclass

    @dataclass
    class APIKeyInfo:
        id: str
        key: str
        key_hash: str
        key_prefix: str
        name: str

    keys = []
    for i in range(2):
        api_key, key_hash, key_prefix = APIKeyManager.generate_key()
        key_id = f"key-{api_key[:8]}"

        await db_connection.execute(
            """
            INSERT INTO api_keys (id, key_hash, key_prefix, name)
            VALUES (?, ?, ?, ?)
            """,
            (key_id, key_hash, key_prefix, f"Test Key {i+1}")
        )

        keys.append(APIKeyInfo(
            id=key_id,
            key=api_key,
            key_hash=key_hash,
            key_prefix=key_prefix,
            name=f"Test Key {i+1}"
        ))

    await db_connection.commit()
    return keys


# ============================================================
# Session Fixtures
# ============================================================

@pytest_asyncio.fixture
async def db_with_session(db_connection, db_with_api_key):
    """带会话的数据库"""
    import uuid
    from dataclasses import dataclass

    session_id = str(uuid.uuid4())

    await db_connection.execute(
        """
        INSERT INTO sessions (id, api_key_id, name, model)
        VALUES (?, ?, ?, ?)
        """,
        (session_id, db_with_api_key.id, "Test Session", "test-model")
    )
    await db_connection.commit()

    @dataclass
    class SessionInfo:
        id: str
        api_key_id: str
        name: str
        model: str

    return SessionInfo(
        id=session_id,
        api_key_id=db_with_api_key.id,
        name="Test Session",
        model="test-model"
    )


@pytest_asyncio.fixture
async def db_with_sessions(db_connection, db_with_api_key):
    """带多个会话的数据库"""
    import uuid

    sessions = []
    for i in range(3):
        session_id = str(uuid.uuid4())
        await db_connection.execute(
            """
            INSERT INTO sessions (id, api_key_id, name, model)
            VALUES (?, ?, ?, ?)
            """,
            (session_id, db_with_api_key.id, f"Session {i+1}", "test-model")
        )

        class SessionInfo:
            id = session_id
            name = f"Session {i+1}"

        sessions.append(SessionInfo())

    await db_connection.commit()
    return sessions


@pytest_asyncio.fixture
async def db_with_messages(db_connection, db_with_session):
    """带消息的会话"""
    import uuid

    for i in range(5):
        await db_connection.execute(
            """
            INSERT INTO messages (id, session_id, role, content)
            VALUES (?, ?, ?, ?)
            """,
            (
                str(uuid.uuid4()),
                db_with_session.id,
                "user" if i % 2 == 0 else "assistant",
                f"Message {i+1}"
            )
        )

    await db_connection.commit()
    return db_with_session


# ============================================================
# Service Fixtures
# ============================================================

@pytest.fixture
def auth_service(db_connection):
    """认证服务实例"""
    from backend.services.auth_service import AuthService
    return AuthService(db_connection)


@pytest.fixture
def session_service(db_connection):
    """会话服务实例"""
    from backend.services.session_service import SessionService
    return SessionService(db_connection)


@pytest.fixture
def usage_service(db_connection):
    """用量统计服务实例"""
    from backend.services.usage_service import UsageService
    return UsageService(db_connection)


@pytest.fixture
def mlx_service():
    """MLX 服务实例 (Mock)"""
    from backend.services.mlx_service import MLXService
    service = MLXService()
    return service


# ============================================================
# Mock Fixtures
# ============================================================

@pytest.fixture
def mock_mlx_model():
    """Mock MLX 模型"""
    model = MagicMock()

    # Mock generate 方法返回 token 流
    def mock_generate(*args, **kwargs):
        for token in ["你", "好", "！", "有", "什", "么", "可", "以", "帮", "助", "你", "的", "？"]:
            yield token

    model.generate = MagicMock(side_effect=mock_generate)
    return model


@pytest.fixture
def mock_mlx_generate(mock_mlx_model):
    """Mock mlx_lm.generate 函数"""
    with patch("backend.services.mlx_service.mlx_lm.generate") as mock:
        mock.return_value = iter(["你", "好", "！"])
        yield mock


@pytest.fixture
def mock_huggingface_cache(tmp_path):
    """Mock HuggingFace 缓存目录"""
    cache = tmp_path / ".cache" / "huggingface" / "hub"
    cache.mkdir(parents=True)

    # 创建模拟模型目录
    for model_name in ["model-a", "model-b", "model-c"]:
        model_dir = cache / f"models--{model_name}"
        model_dir.mkdir()
        snapshots = model_dir / "snapshots"
        snapshots.mkdir()
        (snapshots / "commit123").mkdir()

    return cache


# ============================================================
# API Client Fixtures
# ============================================================

@pytest_asyncio.fixture
async def app(db_connection):
    """FastAPI 应用实例"""
    from backend.main import create_app
    from backend.database import Database
    from backend.services.model_registry_service import ModelRegistryService

    # 创建 Database 包装
    db = Database(db_connection)

    # 创建应用
    app = create_app(db)

    # 设置并初始化 model_registry
    registry = ModelRegistryService(db)
    await registry.initialize()
    app.state.model_registry = registry

    return app


@pytest_asyncio.fixture
async def api_client(app):
    """HTTP 测试客户端 (无认证)"""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as client:
        yield client


@pytest_asyncio.fixture
async def api_client_with_auth(app, db_with_api_key):
    """带认证的 HTTP 测试客户端"""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        headers={"Authorization": f"Bearer {db_with_api_key.key}"}
    ) as client:
        yield client


# ============================================================
# 工具函数
# ============================================================

def create_test_api_key():
    """创建测试用 API Key"""
    from backend.auth.api_key import APIKeyManager
    return APIKeyManager.generate_key()


def create_test_session_id():
    """创建测试用会话 ID"""
    import uuid
    return str(uuid.uuid4())