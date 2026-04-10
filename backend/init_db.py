#!/usr/bin/env python3
"""
初始化脚本 - 创建数据库和 API Key
"""

import asyncio
import aiosqlite
import sys
import os

# 添加项目路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from backend.database import Database
from backend.services.auth_service import AuthService
from backend.services.model_registry_service import ModelRegistryService
from backend.utils.model_detector import detect_local_models


async def main():
    print("=" * 50)
    print("MLX Chat 初始化")
    print("=" * 50)

    # 创建数据库连接 (保存在 backend 目录)
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mlx_chat.db")
    print(f"\n[1] 创建数据库: {db_path}")

    conn = await aiosqlite.connect(db_path)
    db = Database(conn)

    # 创建表
    print("[2] 创建数据表...")
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
            duration_ms INTEGER,
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
    print("    数据表创建成功!")

    # 检测并注册本地模型
    print("\n[3] 检测本地 MLX 模型...")
    local_models = detect_local_models()

    registry = ModelRegistryService(db)
    registered_count = 0
    skipped_count = 0

    for model in local_models:
        # 检查是否已存在
        existing = await registry.get_model(model["model_id"])
        if not existing:
            await registry.add_model(
                name=model["name"],
                model_id=model["model_id"],
                description=model.get("description", ""),
                params_count=model.get("params_count", ""),
                quantization=model.get("quantization", "")
            )
            registered_count += 1
        else:
            skipped_count += 1

    print(f"    检测到 {len(local_models)} 个本地模型")
    print(f"    新增注册: {registered_count} 个")
    print(f"    已存在: {skipped_count} 个")

    if local_models:
        print("\n    本地模型列表:")
        for m in local_models:
            status = "已存在" if any(x["model_id"] == m["model_id"] for x in []) else "新增"
            print(f"    - {m['name']} ({m['params_count']}, {m['quantization']})")

    # 创建 API Key
    print("\n[4] 创建 API Key...")
    auth = AuthService(db)
    info, api_key, _, _ = await auth.create_key('default-key')

    print("\n" + "=" * 50)
    print("初始化完成!")
    print("=" * 50)
    print(f"\n您的 API Key:\n\n    {api_key}\n")
    print("请保存此 Key，后续请求需要使用。")
    print("\n示例:")
    print(f'  curl -H "Authorization: Bearer {api_key}" http://localhost:8000/health')
    print("\n" + "=" * 50)

    await conn.close()


if __name__ == "__main__":
    asyncio.run(main())