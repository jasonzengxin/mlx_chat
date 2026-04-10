"""
会话管理服务

功能:
- 会话 CRUD
- 消息管理
- API Key 关联
"""

import uuid
from datetime import datetime
from typing import Optional, List

from backend.database import Database


class SessionService:
    """会话管理服务"""

    def __init__(self, db: Database):
        self.db = db

    async def create_session(
        self,
        api_key_id: str,
        name: Optional[str] = None,
        model: str = "default",
        temperature: float = 0.7,
        max_tokens: int = 4096,
        system_prompt: str = ""
    ) -> dict:
        """
        创建新会话

        Args:
            api_key_id: 关联的 API Key ID
            name: 会话名称
            model: 使用的模型
            temperature: 温度参数
            max_tokens: 最大 token 数
            system_prompt: 系统提示词

        Returns:
            dict: 会话信息
        """
        session_id = str(uuid.uuid4())
        session_name = name or f"会话 {datetime.now().strftime('%Y-%m-%d %H:%M')}"

        await self.db.execute(
            """
            INSERT INTO sessions
            (id, api_key_id, name, model, temperature, max_tokens, system_prompt)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (session_id, api_key_id, session_name, model, temperature, max_tokens, system_prompt)
        )
        await self.db.commit()

        return await self.get_session(session_id, api_key_id)

    async def get_session(self, session_id: str, api_key_id: str) -> Optional[dict]:
        """
        获取会话详情 (验证所有权)

        Args:
            session_id: 会话 ID
            api_key_id: API Key ID (用于验证所有权)

        Returns:
            Optional[dict]: 会话信息，不存在或无权限返回 None
        """
        row = await self.db.fetchone(
            """
            SELECT id, api_key_id, name, model, temperature, max_tokens,
                   system_prompt, created_at, updated_at
            FROM sessions
            WHERE id = ? AND api_key_id = ?
            """,
            (session_id, api_key_id)
        )

        if row is None:
            return None

        return dict(row)

    async def list_sessions(self, api_key_id: str) -> List[dict]:
        """
        获取指定 API Key 的所有会话

        Args:
            api_key_id: API Key ID

        Returns:
            List[dict]: 会话列表
        """
        rows = await self.db.fetchall(
            """
            SELECT id, name, model, created_at, updated_at
            FROM sessions
            WHERE api_key_id = ?
            ORDER BY updated_at DESC
            """,
            (api_key_id,)
        )

        return rows

    async def delete_session(self, session_id: str, api_key_id: str) -> bool:
        """
        删除会话 (验证所有权)

        Args:
            session_id: 会话 ID
            api_key_id: API Key ID

        Returns:
            bool: 是否成功删除
        """
        # 先验证所有权
        session = await self.get_session(session_id, api_key_id)
        if session is None:
            return False

        result = await self.db.execute(
            "DELETE FROM sessions WHERE id = ?",
            (session_id,)
        )
        await self.db.commit()

        return result.rowcount > 0

    async def add_message(
        self,
        session_id: str,
        api_key_id: str,
        role: str,
        content: str,
        duration_ms: int | None = None
    ) -> dict:
        """
        添加消息到会话

        Args:
            session_id: 会话 ID
            api_key_id: API Key ID
            role: 角色 (user/assistant/system)
            content: 消息内容
            duration_ms: 生成耗时 (毫秒, 仅 assistant 消息)

        Returns:
            dict: 消息信息
        """
        # 验证会话所有权
        session = await self.get_session(session_id, api_key_id)
        if session is None:
            raise ValueError("Session not found or no permission")

        # 验证角色
        if role not in ("user", "assistant", "system"):
            raise ValueError(f"Invalid role: {role}")

        message_id = str(uuid.uuid4())

        await self.db.execute(
            """
            INSERT INTO messages (id, session_id, role, content, duration_ms)
            VALUES (?, ?, ?, ?, ?)
            """,
            (message_id, session_id, role, content, duration_ms)
        )

        # 更新会话的 updated_at
        await self.db.execute(
            """
            UPDATE sessions SET updated_at = ? WHERE id = ?
            """,
            (datetime.now(), session_id)
        )

        await self.db.commit()

        return {
            "id": message_id,
            "session_id": session_id,
            "role": role,
            "content": content,
            "duration_ms": duration_ms,
            "created_at": datetime.now(),
        }

    async def get_messages(self, session_id: str, api_key_id: str) -> List[dict]:
        """
        获取会话的所有消息

        Args:
            session_id: 会话 ID
            api_key_id: API Key ID

        Returns:
            List[dict]: 消息列表
        """
        # 验证所有权
        session = await self.get_session(session_id, api_key_id)
        if session is None:
            return []

        rows = await self.db.fetchall(
            """
            SELECT id, session_id, role, content, duration_ms, created_at
            FROM messages
            WHERE session_id = ?
            ORDER BY created_at ASC
            """,
            (session_id,)
        )

        return rows

    async def update_session(
        self,
        session_id: str,
        api_key_id: str,
        **kwargs
    ) -> Optional[dict]:
        """
        更新会话参数

        Args:
            session_id: 会话 ID
            api_key_id: API Key ID
            **kwargs: 要更新的字段

        Returns:
            Optional[dict]: 更新后的会话信息
        """
        # 验证所有权
        session = await self.get_session(session_id, api_key_id)
        if session is None:
            return None

        # 构建更新语句
        allowed_fields = ["name", "model", "temperature", "max_tokens", "system_prompt"]
        updates = []
        values = []

        for field in allowed_fields:
            if field in kwargs:
                updates.append(f"{field} = ?")
                values.append(kwargs[field])

        if not updates:
            return session

        values.append(datetime.now())  # updated_at
        values.append(session_id)

        await self.db.execute(
            f"""
            UPDATE sessions
            SET {', '.join(updates)}, updated_at = ?
            WHERE id = ?
            """,
            values
        )
        await self.db.commit()

        return await self.get_session(session_id, api_key_id)