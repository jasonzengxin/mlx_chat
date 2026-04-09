"""
API Key 生成与管理

功能:
- 生成安全 API Key (OpenAI 风格)
- SHA256 Hash 存储
- Key 验证
"""

import hashlib
import secrets
from typing import Tuple


class APIKeyManager:
    """API Key 管理器"""

    KEY_LENGTH = 32  # 32 bytes = 64 hex characters
    KEY_PREFIX = "sk-"  # OpenAI 风格前缀

    @classmethod
    def generate_key(cls) -> Tuple[str, str, str]:
        """
        生成新的 API Key

        Returns:
            Tuple[str, str, str]: (明文密钥, hash存储值, key_prefix显示值)
        """
        # 生成随机字节
        raw_key = secrets.token_hex(cls.KEY_LENGTH)

        # 添加前缀
        api_key = f"{cls.KEY_PREFIX}{raw_key}"

        # 计算 SHA256 hash (用于存储)
        key_hash = cls.hash_key(api_key)

        # 显示前缀 (sk-xxxx...)
        key_prefix = api_key[:12]

        return api_key, key_hash, key_prefix

    @staticmethod
    def hash_key(key: str) -> str:
        """
        对 API Key 进行 SHA256 hash

        Args:
            key: 明文 API Key

        Returns:
            str: SHA256 hash 值
        """
        return hashlib.sha256(key.encode()).hexdigest()

    @classmethod
    def verify_key(cls, provided_key: str, stored_hash: str) -> bool:
        """
        验证 API Key

        Args:
            provided_key: 用户提供的 Key
            stored_hash: 数据库存储的 hash

        Returns:
            bool: 验证结果
        """
        return cls.hash_key(provided_key) == stored_hash

    @staticmethod
    def is_valid_format(key: str) -> bool:
        """
        检查 Key 格式是否有效

        Args:
            key: API Key 字符串

        Returns:
            bool: 格式是否正确
        """
        if not key:
            return False

        if not key.startswith("sk-"):
            return False

        # sk- 后面应该是 64 个十六进制字符
        hex_part = key[3:]
        if len(hex_part) != 64:
            return False

        # 检查是否全是十六进制字符
        try:
            int(hex_part, 16)
            return True
        except ValueError:
            return False