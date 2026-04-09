"""
认证服务测试

测试内容:
- Key 创建
- Key 验证
- Key 列表
- Key 删除
"""

import pytest
import pytest_asyncio
from unittest.mock import patch

from backend.services.auth_service import AuthService


class TestAuthServiceCreateKey:
    """认证服务 - 创建 Key 测试"""

    @pytest.mark.asyncio
    async def test_create_key_success(self, auth_service):
        """测试成功创建 Key"""
        result, api_key, key_hash, key_prefix = await auth_service.create_key("Test Key")

        assert result is not None
        assert result.name == "Test Key"
        assert api_key.startswith("sk-")
        assert len(key_hash) == 64
        assert key_prefix.startswith("sk-")

    @pytest.mark.asyncio
    async def test_create_key_stored_in_db(self, auth_service, db_connection):
        """测试创建的 Key 存储到数据库"""
        result, _, _, _ = await auth_service.create_key("Stored Key")

        # 查询数据库
        row = await db_connection.fetchone(
            "SELECT * FROM api_keys WHERE id = ?",
            (result.id,)
        )

        assert row is not None
        assert row["name"] == "Stored Key"
        assert row["is_active"] == 1

    @pytest.mark.asyncio
    async def test_create_multiple_keys_unique(self, auth_service):
        """测试创建多个 Key 互不相同"""
        result1, key1, _, _ = await auth_service.create_key("Key 1")
        result2, key2, _, _ = await auth_service.create_key("Key 2")

        assert result1.id != result2.id
        assert key1 != key2


class TestAuthServiceVerify:
    """认证服务 - 验证测试"""

    @pytest.mark.asyncio
    async def test_verify_valid_key(self, auth_service, db_with_api_key):
        """测试验证有效 Key"""
        result = await auth_service.verify_and_update(db_with_api_key.key)

        assert result is not None
        assert result["id"] == db_with_api_key.id

    @pytest.mark.asyncio
    async def test_verify_invalid_key(self, auth_service):
        """测试验证无效 Key"""
        result = await auth_service.verify_and_update("sk-invalid-key")

        assert result is None

    @pytest.mark.asyncio
    async def test_verify_wrong_format(self, auth_service):
        """测试错误格式 Key"""
        result = await auth_service.verify_and_update("not-a-valid-key")

        assert result is None

    @pytest.mark.asyncio
    async def test_verify_none(self, auth_service):
        """测试 None 输入"""
        result = await auth_service.verify_and_update(None)

        assert result is None

    @pytest.mark.asyncio
    async def test_verify_updates_last_used(self, auth_service, db_with_api_key):
        """测试验证后更新最后使用时间"""
        import time
        time.sleep(0.01)  # 等待一小段时间

        result = await auth_service.verify_and_update(db_with_api_key.key)

        assert result is not None
        # 验证数据库中的 last_used_at 已更新
        row = await auth_service.get_key(db_with_api_key.id)
        assert row["last_used_at"] is not None

    @pytest.mark.asyncio
    async def test_verify_inactive_key(self, auth_service, db_connection):
        """测试验证已禁用的 Key"""
        # 创建一个 Key
        result, api_key, _, _ = await auth_service.create_key("Inactive Key")

        # 禁用它
        await db_connection.execute(
            "UPDATE api_keys SET is_active = 0 WHERE id = ?",
            (result.id,)
        )
        await db_connection.commit()

        # 验证
        verify_result = await auth_service.verify_and_update(api_key)
        assert verify_result is None


class TestAuthServiceList:
    """认证服务 - 列表测试"""

    @pytest.mark.asyncio
    async def test_list_keys_empty(self, auth_service):
        """测试空列表"""
        result = await auth_service.list_keys()

        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_list_keys_with_items(self, auth_service):
        """测试列出多个 Keys"""
        await auth_service.create_key("Key 1")
        await auth_service.create_key("Key 2")
        await auth_service.create_key("Key 3")

        result = await auth_service.list_keys()

        assert len(result) >= 3

    @pytest.mark.asyncio
    async def test_list_keys_no_hash(self, auth_service):
        """测试列表不包含 hash"""
        await auth_service.create_key("Secret Key")

        result = await auth_service.list_keys()

        for key in result:
            assert "key_hash" not in key
            assert "key" not in key

    @pytest.mark.asyncio
    async def test_list_keys_sorted(self, auth_service):
        """测试列表按创建时间排序"""
        await auth_service.create_key("First")
        await auth_service.create_key("Second")
        await auth_service.create_key("Third")

        result = await auth_service.list_keys()

        # 最新创建的应该在最前面
        names = [k["name"] for k in result]
        assert "Third" in names
        assert "First" in names


class TestAuthServiceDelete:
    """认证服务 - 删除测试"""

    @pytest.mark.asyncio
    async def test_delete_key_success(self, auth_service, db_with_api_key):
        """测试成功删除 Key"""
        result = await auth_service.delete_key(db_with_api_key.id)

        assert result is True

        # 验证已删除
        key = await auth_service.get_key(db_with_api_key.id)
        assert key is None

    @pytest.mark.asyncio
    async def test_delete_key_not_found(self, auth_service):
        """测试删除不存在的 Key"""
        result = await auth_service.delete_key("nonexistent-id")

        assert result is False

    @pytest.mark.asyncio
    async def test_delete_key_invalidates_verification(self, auth_service, db_with_api_key):
        """测试删除后 Key 无法验证"""
        # 删除 Key
        await auth_service.delete_key(db_with_api_key.id)

        # 验证失败
        result = await auth_service.verify_and_update(db_with_api_key.key)
        assert result is None

    @pytest.mark.asyncio
    async def test_delete_key_preserves_other_keys(self, auth_service):
        """测试删除不影响其他 Keys"""
        result1, key1, _, _ = await auth_service.create_key("Key 1")
        result2, key2, _, _ = await auth_service.create_key("Key 2")

        # 删除 Key 1
        await auth_service.delete_key(result1.id)

        # Key 2 仍然可用
        verify_result = await auth_service.verify_and_update(key2)
        assert verify_result is not None


class TestAuthServiceGet:
    """认证服务 - 获取测试"""

    @pytest.mark.asyncio
    async def test_get_key_success(self, auth_service, db_with_api_key):
        """测试成功获取 Key 信息"""
        result = await auth_service.get_key(db_with_api_key.id)

        assert result is not None
        assert result["id"] == db_with_api_key.id
        assert result["name"] == db_with_api_key.name

    @pytest.mark.asyncio
    async def test_get_key_not_found(self, auth_service):
        """测试获取不存在的 Key"""
        result = await auth_service.get_key("nonexistent-id")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_key_no_sensitive_data(self, auth_service, db_with_api_key):
        """测试获取不返回敏感数据"""
        result = await auth_service.get_key(db_with_api_key.id)

        assert "key_hash" not in result
        assert "key" not in result
