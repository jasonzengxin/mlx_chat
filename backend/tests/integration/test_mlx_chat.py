"""
集成测试 - 实际测试 MLX 模型对话

测试流程:
1. 加载模型
2. 测试 chat/completions 端点
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

import asyncio
import aiosqlite
from backend.main import create_app
from backend.database import Database
from backend.services.auth_service import AuthService
from backend.mlx_instance import get_mlx_service
import uvicorn
import threading
import time
import httpx


async def setup_db():
    """创建数据库和 API Key"""
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
    ''')
    await conn.commit()

    auth = AuthService(db)
    info, api_key, _, _ = await auth.create_key('test-key')

    return db, api_key


def run_server(app, port=8000):
    """在后台运行服务器"""
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="error")


async def main():
    print("=" * 60)
    print("MLX Chat 集成测试")
    print("=" * 60)

    # 1. 设置数据库
    print("\n[1] 设置数据库...")
    db, api_key = await setup_db()
    print(f"    API Key: {api_key[:20]}...")

    # 2. 创建应用
    print("\n[2] 创建应用...")
    app = create_app(db)

    # 3. 启动服务器
    print("\n[3] 启动服务器 (端口 8000)...")
    server_thread = threading.Thread(target=run_server, args=(app,), daemon=True)
    server_thread.start()
    time.sleep(2)  # 等待服务器启动

    # 4. 加载模型
    print("\n[4] 加载模型...")
    model_name = "mlx-community/Qwen2.5-0.5B-Instruct-4bit"

    async with httpx.AsyncClient() as client:
        # 加载模型
        print(f"    加载 {model_name}...")
        try:
            response = await client.post(
                "http://127.0.0.1:8000/api/v1/models/load",
                headers={"Authorization": f"Bearer {api_key}"},
                json={"model": model_name},
                timeout=180.0
            )

            print(f"    响应状态: {response.status_code}")
            print(f"    响应内容: {response.text}")

            if response.status_code != 200:
                print(f"    加载失败!")
                return

            result = response.json()
            print(f"    加载成功! 耗时: {result.get('load_time_seconds', 'N/A')}s")
        except Exception as e:
            print(f"    加载异常: {e}")
            return

        # 5. 测试 chat/completions (非流式)
        print("\n[5] 测试 chat/completions (非流式)...")
        response = await client.post(
            "http://127.0.0.1:8000/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "model": model_name,
                "messages": [
                    {"role": "user", "content": "1+1等于几？只回答数字。"}
                ],
                "stream": False,
                "temperature": 0.1,
                "max_tokens": 50
            },
            timeout=60.0
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

        # 6. 测试 chat/completions (流式)
        print("\n[6] 测试 chat/completions (流式)...")
        async with client.stream(
            "POST",
            "http://127.0.0.1:8000/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "model": model_name,
                "messages": [
                    {"role": "user", "content": "说一个字：好"}
                ],
                "stream": True,
                "temperature": 0.1,
                "max_tokens": 10
            },
            timeout=60.0
        ) as response:
            print(f"    状态码: {response.status_code}")
            if response.status_code == 200:
                print("    流式响应: ", end="", flush=True)
                async for line in response.aiter_lines():
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
                print(f"    错误: {await response.aread()}")

    print("\n" + "=" * 60)
    print("测试完成!")
    print("=" * 60)

    await db.close()


if __name__ == "__main__":
    asyncio.run(main())
