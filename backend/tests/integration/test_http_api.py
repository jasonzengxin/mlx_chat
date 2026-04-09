"""
集成测试 - HTTP API 测试

使用 httpx 测试 /v1/chat/completions 端点
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

import asyncio
import aiosqlite
from backend.main import create_app
from backend.database import Database
from backend.services.auth_service import AuthService
from backend.services.model_registry_service import ModelRegistryService
from backend.mlx_instance import init_mlx_service, get_mlx_service
from starlette.testclient import TestClient


async def main():
    print("=" * 60)
    print("MLX Chat HTTP API 测试")
    print("=" * 60)

    # 1. 初始化 MLX 服务并加载模型
    print("\n[1] 初始化 MLX 服务...")
    init_mlx_service()
    mlx_service = get_mlx_service()

    model_name = "mlx-community/Qwen2.5-0.5B-Instruct-4bit"
    print(f"    加载模型: {model_name}")
    result = await mlx_service.load_model(model_name)
    print(f"    结果: {result}")

    if result.get("status") != "loaded":
        print("    模型加载失败，退出")
        return

    # 2. 创建数据库和 API Key
    print("\n[2] 创建数据库和 API Key...")
    conn = await aiosqlite.connect(":memory:")
    db = Database(conn)

    await conn.executescript('''
        CREATE TABLE api_keys (
            id TEXT PRIMARY KEY,
            key_hash TEXT UNIQUE NOT NULL,
            key_prefix TEXT NOT NULL,
            name TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_used_at TIMESTAMP,
            is_active BOOLEAN DEFAULT 1
        );
        CREATE TABLE usage_logs (
            id TEXT PRIMARY KEY,
            api_key_id TEXT NOT NULL,
            session_id TEXT,
            model TEXT NOT NULL,
            input_tokens INTEGER DEFAULT 0,
            output_tokens INTEGER DEFAULT 0,
            time_ms INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
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
    ''')

    auth = AuthService(db)
    info, api_key, _, _ = await auth.create_key('test-key')
    print(f"    API Key: {api_key[:20]}...")

    # 3. 创建应用并设置 model_registry
    print("\n[3] 创建应用...")
    app = create_app(db)
    app.state.model_registry = ModelRegistryService(db)
    await app.state.model_registry.initialize()

    # 4. 测试 chat/completions (非流式)
    print("\n[4] 测试 /v1/chat/completions (非流式)...")
    with TestClient(app) as client:
        response = client.post(
            "/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "model": model_name,
                "messages": [
                    {"role": "user", "content": "1+1等于几？只回答数字。"}
                ],
                "stream": False,
                "temperature": 0.1,
                "max_tokens": 20
            }
        )

        print(f"    状态码: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"    响应 ID: {data['id']}")
            print(f"    模型: {data['model']}")
            print(f"    回答: {data['choices'][0]['message']['content']}")
            print(f"    Token 用量: {data['usage']}")
        else:
            print(f"    错误: {response.text}")

        # 5. 测试 chat/completions (流式)
        print("\n[5] 测试 /v1/chat/completions (流式)...")
        response = client.post(
            "/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "model": model_name,
                "messages": [
                    {"role": "user", "content": "说一个字：好"}
                ],
                "stream": True,
                "temperature": 0.1,
                "max_tokens": 10
            }
        )

        print(f"    状态码: {response.status_code}")
        if response.status_code == 200:
            print("    流式响应: ", end="")
            for line in response.iter_lines():
                if line.startswith("data: ") and line != "data: [DONE]":
                    import json
                    try:
                        data = json.loads(line[6:])
                        if "choices" in data and data["choices"]:
                            delta = data["choices"][0].get("delta", {})
                            if "content" in delta:
                                print(delta["content"], end="", flush=True)
                    except:
                        pass
            print()
        else:
            print(f"    错误: {response.text}")

    await conn.close()

    print("\n" + "=" * 60)
    print("测试完成!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
