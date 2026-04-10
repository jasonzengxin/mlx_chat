"""
MLX 服务测试

测试内容:
- 模型状态检查
- Prompt 构建
- 错误处理

注意: MLX 模型加载需要实际 MLX 环境，这里主要测试不需要实际模型的逻辑
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import asyncio

from backend.services.mlx_service import MLXService


class TestMLXServiceInit:
    """MLX 服务 - 初始化测试"""

    def test_init_no_model(self):
        """测试初始状态无模型"""
        service = MLXService()

        assert service.current_model is None
        assert service.current_model_name is None
        assert service._tokenizer is None

    def test_init_has_lock(self):
        """测试初始化有锁"""
        service = MLXService()

        assert service.model_lock is not None
        assert isinstance(service.model_lock, asyncio.Lock)


class TestMLXServiceState:
    """MLX 服务 - 状态测试"""

    def test_get_current_model_none(self):
        """测试无模型时返回 None"""
        service = MLXService()

        result = service.get_current_model()

        assert result is None

    def test_is_model_loaded_false(self):
        """测试无模型时 is_model_loaded 返回 False"""
        service = MLXService()

        assert service.is_model_loaded() is False


class TestMLXServicePromptBuilder:
    """MLX 服务 - Prompt 构建测试"""

    def test_build_prompt_empty(self):
        """测试空消息"""
        service = MLXService()

        result = service._build_prompt([])

        assert "<|assistant|>" in result

    def test_build_prompt_single_user(self):
        """测试单条用户消息"""
        service = MLXService()

        result = service._build_prompt([
            {"role": "user", "content": "Hello"}
        ])

        assert "<|user|>" in result
        assert "Hello" in result
        assert "<|assistant|>" in result

    def test_build_prompt_with_system(self):
        """测试系统消息"""
        service = MLXService()

        result = service._build_prompt([
            {"role": "system", "content": "You are helpful."},
            {"role": "user", "content": "Hi"}
        ])

        assert "<|system|>" in result
        assert "You are helpful." in result
        assert "<|user|>" in result
        assert "Hi" in result

    def test_build_prompt_conversation(self):
        """测试对话历史"""
        service = MLXService()

        result = service._build_prompt([
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
            {"role": "user", "content": "How are you?"}
        ])

        assert "<|user|>" in result
        assert "Hello" in result
        assert "<|assistant|>" in result
        assert "Hi there!" in result
        assert "How are you?" in result

    def test_build_prompt_with_system_param(self):
        """测试 system_prompt 参数"""
        service = MLXService()

        result = service._build_prompt(
            [{"role": "user", "content": "Hi"}],
            system_prompt="You are a poet."
        )

        assert "<|system|>" in result
        assert "You are a poet." in result

    def test_build_prompt_missing_role(self):
        """测试缺失 role 字段"""
        service = MLXService()

        result = service._build_prompt([
            {"content": "Hello"}  # 缺少 role
        ])

        # 应该默认为 user
        assert "<|user|>" in result

    def test_build_prompt_missing_content(self):
        """测试缺失 content 字段"""
        service = MLXService()

        result = service._build_prompt([
            {"role": "user"}  # 缺少 content
        ])

        # 应该使用空字符串
        assert result is not None


class TestMLXServiceUnload:
    """MLX 服务 - 卸载测试"""

    def test_unload_model(self):
        """测试卸载模型"""
        service = MLXService()

        # 模拟有模型
        service.current_model = MagicMock()
        service._tokenizer = MagicMock()
        service.current_model_name = "test-model"

        service._unload_model()

        assert service.current_model is None
        assert service._tokenizer is None
        assert service.current_model_name is None


class TestMLXServiceGenerate:
    """MLX 服务 - 生成测试"""

    @pytest.mark.asyncio
    async def test_generate_no_model(self):
        """测试无模型时生成抛出异常"""
        service = MLXService()

        with pytest.raises(RuntimeError, match="No model loaded"):
            async for _ in service.generate_stream(
                messages=[{"role": "user", "content": "test"}],
                temperature=0.7,
                max_tokens=100
            ):
                pass


class TestMLXServiceMocked:
    """MLX 服务 - Mock 测试"""

    @pytest.mark.asyncio
    async def test_generate_stream_uses_stream_generate_when_available(self):
        """测试优先使用 mlx_lm.stream_generate 做真实流式输出"""
        service = MLXService()

        # Mock 模型
        service.current_model = MagicMock()
        service._tokenizer = MagicMock()
        service.current_model_name = "mock-model"

        mock_chunk_1 = MagicMock()
        mock_chunk_1.text = "你"
        mock_chunk_2 = MagicMock()
        mock_chunk_2.text = "好！"

        with patch("backend.services.mlx_service.mlx_lm.stream_generate", create=True) as mock_stream_generate:
            mock_stream_generate.return_value = iter([mock_chunk_1, mock_chunk_2])

            tokens = []
            async for token in service.generate_stream(
                messages=[{"role": "user", "content": "你好"}],
                temperature=0.7,
                max_tokens=10
            ):
                tokens.append(token)

            assert tokens == ["你", "好！"]
            mock_stream_generate.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_stream_falls_back_to_generate(self):
        """测试旧版本 mlx_lm 无 stream_generate 时回退到 generate"""
        service = MLXService()

        service.current_model = MagicMock()
        service._tokenizer = MagicMock()
        service.current_model_name = "mock-model"

        with patch(
            "backend.services.mlx_service.mlx_lm.stream_generate",
            new=None,
            create=True,
        ):
            with patch("backend.services.mlx_service.mlx_lm.generate") as mock_generate:
                mock_generate.return_value = "OK"

                tokens = []
                async for token in service.generate_stream(
                    messages=[{"role": "user", "content": "test"}],
                    temperature=0.7,
                    max_tokens=10,
                ):
                    tokens.append(token)

                assert tokens == ["OK"]
                mock_generate.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_stream_with_system_prompt(self):
        """测试带系统提示词生成"""
        service = MLXService()

        service.current_model = MagicMock()
        service._tokenizer = MagicMock()
        service.current_model_name = "mock-model"

        mock_chunk = MagicMock()
        mock_chunk.text = "OK"

        with patch("backend.services.mlx_service.mlx_lm.stream_generate", create=True) as mock_stream_generate:
            mock_stream_generate.return_value = iter([mock_chunk])

            tokens = []
            async for token in service.generate_stream(
                messages=[{"role": "user", "content": "test"}],
                temperature=0.7,
                max_tokens=10,
                system_prompt="You are helpful."
            ):
                tokens.append(token)

            # 验证 build_prompt 被调用
            mock_stream_generate.assert_called_once()
            call_kwargs = mock_stream_generate.call_args
            assert "prompt" in call_kwargs.kwargs or len(call_kwargs.args) > 0
