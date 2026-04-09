"""
认证服务

功能:
- API Key CRUD
- Key 验证与更新
"""

import uuid
from datetime import datetime
from typing import Optional

from backend.database import Database


class AuthService:
    """认证服务"""

    def __init__(self, db: Database):
        self.db = db

    async def create_key(self, name: str) -> tuple:
        """
        创建新 API Key

        Args:
            name: Key 用途名称

        Returns:
            tuple: (key_info对象, 明文key, key_hash, key_prefix)
        """
        from backend.auth.api_key import APIKeyManager
        from dataclasses import dataclass

        api_key, key_hash, key_prefix = APIKeyManager.generate_key()
        key_id = str(uuid.uuid4())

        await self.db.execute(
            """
            INSERT INTO api_keys (id, key_hash, key_prefix, name)
            VALUES (?, ?, ?, ?)
            """,
            (key_id, key_hash, key_prefix, name)
        )
        await self.db.commit()

        # 使用 dataclass 避免类作用域问题
        @dataclass
        class APIKeyInfo:
            id: str
            key: str
            key_hash: str
            key_prefix: str
            name: str
            created_at: datetime
            last_used_at: None
            is_active: bool = True

        return APIKeyInfo(
            id=key_id,
            key=api_key,
            key_hash=key_hash,
            key_prefix=key_prefix,
            name=name,
            created_at=datetime.now(),
            last_used_at=None,
        ), api_key, key_hash, key_prefix

    async def verify_and_update(self, provided_key: str) -> Optional[dict]:
        """
        验证 Key 并更新最后使用时间

        Args:
            provided_key: 用户提供的 Key

        Returns:
            Optional[dict]: Key 信息，无效返回 None
        """
        from backend.auth.api_key import APIKeyManager

        if not APIKeyManager.is_valid_format(provided_key):
            return None

        key_hash = APIKeyManager.hash_key(provided_key)

        # 查询数据库
        row = await self.db.fetchone(
            """
            SELECT id, key_prefix, name, is_active, last_used_at
            FROM api_keys
            WHERE key_hash = ? AND is_active = 1
            """,
            (key_hash,)
        )

        if row is None:
            return None

        # 更新最后使用时间
        await self.db.execute(
            """
            UPDATE api_keys SET last_used_at = ?
            WHERE id = ?
            """,
            (datetime.now(), row["id"])
        )
        await self.db.commit()

        return {
            "id": row["id"],
            "key_prefix": row["key_prefix"],
            "name": row["name"],
        }

    async def get_key(self, key_id: str) -> Optional[dict]:
        """获取 Key 信息"""
        row = await self.db.fetchone(
            """
            SELECT id, key_prefix, name, created_at, last_used_at, is_active
            FROM api_keys WHERE id = ?
            """,
            (key_id,)
        )

        if row is None:
            return None

        return dict(row)

    async def list_keys(self) -> list:
        """列出所有 Keys (不含 hash 和明文)"""
        rows = await self.db.fetchall(
            """
            SELECT id, key_prefix, name, created_at, last_used_at, is_active
            FROM api_keys ORDER BY created_at DESC
            """
        )

        return rows

    async def delete_key(self, key_id: str) -> bool:
        """删除 Key"""
        result = await self.db.execute(
            "DELETE FROM api_keys WHERE id = ?",
            (key_id,)
        )
        await self.db.commit()

        return result.rowcount > 0