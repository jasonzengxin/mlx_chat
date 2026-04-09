"""
API Key 管理测试

测试内容:
- Key 生成格式
- Hash 验证
- 格式验证
"""

import pytest

from backend.auth.api_key import APIKeyManager


class TestAPIKeyManager:
    """API Key 管理器单元测试"""

    def test_generate_key_returns_three_values(self):
        """测试生成 Key 返回三个值"""
        result = APIKeyManager.generate_key()

        assert len(result) == 3
        assert isinstance(result, tuple)

    def test_generate_key_format(self):
        """测试生成的 Key 格式正确"""
        api_key, key_hash, key_prefix = APIKeyManager.generate_key()

        # 验证格式
        assert api_key.startswith("sk-")
        assert len(api_key) == 67  # sk- + 64 hex
        assert len(key_hash) == 64  # SHA256 hex
        assert len(key_prefix) == 12  # sk- + 8 chars

    def test_generate_key_unique(self):
        """测试每次生成的 Key 都不同"""
        key1, _, _ = APIKeyManager.generate_key()
        key2, _, _ = APIKeyManager.generate_key()

        assert key1 != key2

    def test_hash_key_consistency(self):
        """测试同一 Key 产生相同 hash"""
        api_key, key_hash1, _ = APIKeyManager.generate_key()
        key_hash2 = APIKeyManager.hash_key(api_key)

        assert key_hash1 == key_hash2

    def test_hash_key_different_keys(self):
        """测试不同 Key 产生不同 hash"""
        api_key1, _, _ = APIKeyManager.generate_key()
        api_key2, _, _ = APIKeyManager.generate_key()

        hash1 = APIKeyManager.hash_key(api_key1)
        hash2 = APIKeyManager.hash_key(api_key2)

        assert hash1 != hash2

    def test_verify_key_correct(self):
        """测试正确 Key 验证通过"""
        api_key, key_hash, _ = APIKeyManager.generate_key()

        result = APIKeyManager.verify_key(api_key, key_hash)
        assert result is True

    def test_verify_key_incorrect(self):
        """测试错误 Key 验证失败"""
        _, key_hash, _ = APIKeyManager.generate_key()
        fake_key = "sk-" + "a" * 64

        result = APIKeyManager.verify_key(fake_key, key_hash)
        assert result is False

    def test_verify_key_tampered(self):
        """测试篡改的 Key 验证失败"""
        api_key, key_hash, _ = APIKeyManager.generate_key()
        # 篡改最后一个字符
        tampered_key = api_key[:-1] + ("f" if api_key[-1] != "f" else "e")

        result = APIKeyManager.verify_key(tampered_key, key_hash)
        assert result is False

    def test_is_valid_format_valid(self):
        """测试有效格式"""
        api_key, _, _ = APIKeyManager.generate_key()
        assert APIKeyManager.is_valid_format(api_key) is True

    def test_is_valid_format_none(self):
        """测试 None 输入"""
        assert APIKeyManager.is_valid_format(None) is False

    def test_is_valid_format_empty(self):
        """测试空字符串"""
        assert APIKeyManager.is_valid_format("") is False

    def test_is_valid_format_no_prefix(self):
        """测试无前缀"""
        assert APIKeyManager.is_valid_format("a" * 64) is False

    def test_is_valid_format_wrong_prefix(self):
        """测试错误前缀"""
        assert APIKeyManager.is_valid_format("pk-" + "a" * 64) is False

    def test_is_valid_format_too_short(self):
        """测试太短"""
        assert APIKeyManager.is_valid_format("sk-" + "a" * 32) is False

    def test_is_valid_format_too_long(self):
        """测试太长"""
        assert APIKeyManager.is_valid_format("sk-" + "a" * 100) is False

    def test_is_valid_format_non_hex(self):
        """测试非十六进制字符"""
        assert APIKeyManager.is_valid_format("sk-" + "g" * 64) is False

    def test_is_valid_format_with_special_chars(self):
        """测试包含特殊字符"""
        assert APIKeyManager.is_valid_format("sk-" + "!" * 64) is False


class TestAPIKeySecurity:
    """API Key 安全性测试"""

    def test_hash_not_reversible(self):
        """测试 hash 不可逆"""
        api_key, key_hash, _ = APIKeyManager.generate_key()

        # 确认 hash 不是明文
        assert key_hash != api_key
        assert key_hash != api_key[3:]  # 不是去掉前缀的 key

    def test_hash_deterministic(self):
        """测试 hash 是确定性的"""
        api_key, _, _ = APIKeyManager.generate_key()

        hash1 = APIKeyManager.hash_key(api_key)
        hash2 = APIKeyManager.hash_key(api_key)
        hash3 = APIKeyManager.hash_key(api_key)

        assert hash1 == hash2 == hash3

    def test_prefix_not_enough_to_find_key(self):
        """测试前缀不足以找到完整 key"""
        _, _, key_prefix = APIKeyManager.generate_key()

        # 前缀只有 12 个字符，不足以暴力破解
        assert len(key_prefix) == 12

        # 64 个十六进制字符的暴力空间是 16^64，几乎不可能
