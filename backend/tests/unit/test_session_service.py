"""
会话服务测试

测试内容:
- 会话 CRUD
- 消息管理
- API Key 关联
"""

import pytest
from unittest.mock import patch

from backend.services.session_service import SessionService


class TestSessionServiceCreate:
    """会话服务 - 创建测试"""

    @pytest.mark.asyncio
    async def test_create_session_success(self, session_service, db_with_api_key):
        """测试成功创建会话"""
        result = await session_service.create_session(
            api_key_id=db_with_api_key.id,
            name="Test Session"
        )

        assert result is not None
        assert result["name"] == "Test Session"
        assert result["api_key_id"] == db_with_api_key.id
        assert result["model"] == "default"

    @pytest.mark.asyncio
    async def test_create_session_with_params(self, session_service, db_with_api_key):
        """测试带参数创建会话"""
        result = await session_service.create_session(
            api_key_id=db_with_api_key.id,
            name="Custom Session",
            model="qwen3.5",
            temperature=1.0,
            max_tokens=8192,
            system_prompt="You are a helpful assistant."
        )

        assert result["model"] == "qwen3.5"
        assert result["temperature"] == 1.0
        assert result["max_tokens"] == 8192
        assert result["system_prompt"] == "You are a helpful assistant."

    @pytest.mark.asyncio
    async def test_create_session_default_values(self, session_service, db_with_api_key):
        """测试默认值"""
        result = await session_service.create_session(
            api_key_id=db_with_api_key.id
        )

        assert result["temperature"] == 0.7
        assert result["max_tokens"] == 4096
        assert result["system_prompt"] == ""

    @pytest.mark.asyncio
    async def test_create_session_auto_name(self, session_service, db_with_api_key):
        """测试自动生成名称"""
        result = await session_service.create_session(
            api_key_id=db_with_api_key.id
        )

        assert result["name"] is not None
        assert "会话" in result["name"]


class TestSessionServiceGet:
    """会话服务 - 获取测试"""

    @pytest.mark.asyncio
    async def test_get_session_success(self, session_service, db_with_api_key):
        """测试成功获取会话"""
        created = await session_service.create_session(
            api_key_id=db_with_api_key.id,
            name="Get Test"
        )

        result = await session_service.get_session(
            created["id"],
            db_with_api_key.id
        )

        assert result is not None
        assert result["id"] == created["id"]

    @pytest.mark.asyncio
    async def test_get_session_not_found(self, session_service, db_with_api_key):
        """测试获取不存在的会话"""
        result = await session_service.get_session(
            "nonexistent-id",
            db_with_api_key.id
        )

        assert result is None

    @pytest.mark.asyncio
    async def test_get_session_wrong_api_key(self, session_service, db_with_two_api_keys):
        """测试使用错误的 API Key 获取会话"""
        # 用 Key 1 创建会话
        created = await session_service.create_session(
            api_key_id=db_with_two_api_keys[0].id,
            name="Private Session"
        )

        # 用 Key 2 获取 (应该失败)
        result = await session_service.get_session(
            created["id"],
            db_with_two_api_keys[1].id
        )

        assert result is None


class TestSessionServiceList:
    """会话服务 - 列表测试"""

    @pytest.mark.asyncio
    async def test_list_sessions_empty(self, session_service, db_with_api_key):
        """测试空列表"""
        result = await session_service.list_sessions(db_with_api_key.id)

        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_list_sessions_multiple(self, session_service, db_with_api_key):
        """测试列出多个会话"""
        await session_service.create_session(api_key_id=db_with_api_key.id, name="S1")
        await session_service.create_session(api_key_id=db_with_api_key.id, name="S2")
        await session_service.create_session(api_key_id=db_with_api_key.id, name="S3")

        result = await session_service.list_sessions(db_with_api_key.id)

        assert len(result) >= 3

    @pytest.mark.asyncio
    async def test_list_sessions_only_own(self, session_service, db_with_two_api_keys):
        """测试只列出自己的会话"""
        # Key 1 创建 2 个
        await session_service.create_session(api_key_id=db_with_two_api_keys[0].id, name="A1")
        await session_service.create_session(api_key_id=db_with_two_api_keys[0].id, name="A2")

        # Key 2 创建 1 个
        await session_service.create_session(api_key_id=db_with_two_api_keys[1].id, name="B1")

        sessions_a = await session_service.list_sessions(db_with_two_api_keys[0].id)
        sessions_b = await session_service.list_sessions(db_with_two_api_keys[1].id)

        assert len(sessions_a) == 2
        assert len(sessions_b) == 1


class TestSessionServiceDelete:
    """会话服务 - 删除测试"""

    @pytest.mark.asyncio
    async def test_delete_session_success(self, session_service, db_with_api_key):
        """测试成功删除会话"""
        created = await session_service.create_session(
            api_key_id=db_with_api_key.id,
            name="To Delete"
        )

        result = await session_service.delete_session(
            created["id"],
            db_with_api_key.id
        )

        assert result is True

        # 验证已删除
        check = await session_service.get_session(created["id"], db_with_api_key.id)
        assert check is None

    @pytest.mark.asyncio
    async def test_delete_session_not_found(self, session_service, db_with_api_key):
        """测试删除不存在的会话"""
        result = await session_service.delete_session(
            "nonexistent-id",
            db_with_api_key.id
        )

        assert result is False

    @pytest.mark.asyncio
    async def test_delete_session_wrong_api_key(self, session_service, db_with_two_api_keys):
        """测试错误的 API Key 无法删除"""
        created = await session_service.create_session(
            api_key_id=db_with_two_api_keys[0].id,
            name="Protected"
        )

        # 用 Key 2 删除 (应该失败)
        result = await session_service.delete_session(
            created["id"],
            db_with_two_api_keys[1].id
        )

        assert result is False

        # 会话仍然存在
        check = await session_service.get_session(created["id"], db_with_two_api_keys[0].id)
        assert check is not None


class TestSessionServiceMessages:
    """会话服务 - 消息测试"""

    @pytest.mark.asyncio
    async def test_add_message_user(self, session_service, db_with_session):
        """测试添加用户消息"""
        result = await session_service.add_message(
            session_id=db_with_session.id,
            api_key_id=db_with_session.api_key_id,
            role="user",
            content="Hello"
        )

        assert result["role"] == "user"
        assert result["content"] == "Hello"

    @pytest.mark.asyncio
    async def test_add_message_assistant(self, session_service, db_with_session):
        """测试添加助手消息"""
        result = await session_service.add_message(
            session_id=db_with_session.id,
            api_key_id=db_with_session.api_key_id,
            role="assistant",
            content="Hi there!"
        )

        assert result["role"] == "assistant"
        assert result["content"] == "Hi there!"

    @pytest.mark.asyncio
    async def test_add_message_invalid_role(self, session_service, db_with_session):
        """测试无效角色"""
        with pytest.raises(ValueError, match="Invalid role"):
            await session_service.add_message(
                session_id=db_with_session.id,
                api_key_id=db_with_session.api_key_id,
                role="invalid",
                content="test"
            )

    @pytest.mark.asyncio
    async def test_add_message_session_not_found(self, session_service, db_with_api_key):
        """测试会话不存在"""
        with pytest.raises(ValueError, match="Session not found"):
            await session_service.add_message(
                session_id="nonexistent",
                api_key_id=db_with_api_key.id,
                role="user",
                content="test"
            )

    @pytest.mark.asyncio
    async def test_get_messages_empty(self, session_service, db_with_session):
        """测试获取空消息列表"""
        result = await session_service.get_messages(
            db_with_session.id,
            db_with_session.api_key_id
        )

        assert result == []

    @pytest.mark.asyncio
    async def test_get_messages_ordered(self, session_service, db_with_session):
        """测试消息按时间顺序"""
        await session_service.add_message(
            db_with_session.id,
            db_with_session.api_key_id,
            "user",
            "First"
        )
        await session_service.add_message(
            db_with_session.id,
            db_with_session.api_key_id,
            "assistant",
            "Second"
        )
        await session_service.add_message(
            db_with_session.id,
            db_with_session.api_key_id,
            "user",
            "Third"
        )

        messages = await session_service.get_messages(
            db_with_session.id,
            db_with_session.api_key_id
        )

        assert len(messages) == 3
        assert messages[0]["content"] == "First"
        assert messages[1]["content"] == "Second"
        assert messages[2]["content"] == "Third"


class TestSessionServiceUpdate:
    """会话服务 - 更新测试"""

    @pytest.mark.asyncio
    async def test_update_session_name(self, session_service, db_with_session):
        """测试更新会话名称"""
        result = await session_service.update_session(
            db_with_session.id,
            db_with_session.api_key_id,
            name="New Name"
        )

        assert result["name"] == "New Name"

    @pytest.mark.asyncio
    async def test_update_session_model(self, session_service, db_with_session):
        """测试更新会话模型"""
        result = await session_service.update_session(
            db_with_session.id,
            db_with_session.api_key_id,
            model="new-model"
        )

        assert result["model"] == "new-model"

    @pytest.mark.asyncio
    async def test_update_session_multiple(self, session_service, db_with_session):
        """测试批量更新"""
        result = await session_service.update_session(
            db_with_session.id,
            db_with_session.api_key_id,
            temperature=1.0,
            max_tokens=8192,
            system_prompt="New prompt"
        )

        assert result["temperature"] == 1.0
        assert result["max_tokens"] == 8192
        assert result["system_prompt"] == "New prompt"

    @pytest.mark.asyncio
    async def test_update_session_not_found(self, session_service, db_with_api_key):
        """测试更新不存在的会话"""
        result = await session_service.update_session(
            "nonexistent",
            db_with_api_key.id,
            name="New Name"
        )

        assert result is None
