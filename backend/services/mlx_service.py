"""
MLX 模型服务

功能:
- 模型加载与卸载
- 流式生成
- 模型生命周期管理
"""

import asyncio
import gc
import time
from typing import Optional, AsyncGenerator, Dict, List

import mlx_lm
from mlx_lm.sample_utils import make_sampler


class MLXService:
    """MLX 模型服务"""

    def __init__(self):
        self.current_model: Optional[object] = None
        self.current_model_name: Optional[str] = None
        self._tokenizer: Optional[object] = None
        self.model_lock: asyncio.Lock = asyncio.Lock()

    async def load_model(self, model_name: str) -> Dict:
        """
        加载指定模型

        Args:
            model_name: HuggingFace 模型 ID 或本地路径

        Returns:
            Dict: 加载结果
        """
        async with self.model_lock:
            # 卸载旧模型
            if self.current_model is not None:
                self._unload_model()
                await asyncio.sleep(0.5)  # 等待资源释放

            # 加载新模型
            start_time = time.time()

            try:
                # 在线程池中执行阻塞的加载操作
                loop = asyncio.get_event_loop()
                self.current_model, self._tokenizer = await loop.run_in_executor(
                    None, lambda: mlx_lm.load(model_name)
                )
                self.current_model_name = model_name
                load_time = time.time() - start_time

                return {
                    "status": "loaded",
                    "model": model_name,
                    "load_time_seconds": round(load_time, 2)
                }
            except Exception as e:
                return {
                    "status": "error",
                    "model": model_name,
                    "error": str(e)
                }

    async def generate_stream(
        self,
        messages: List[Dict],
        temperature: float,
        max_tokens: int,
        system_prompt: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        """
        流式生成响应

        Args:
            messages: 消息历史
            temperature: 温度参数
            max_tokens: 最大 token 数
            system_prompt: 系统提示词

        Yields:
            str: 生成的 token
        """
        if self.current_model is None:
            raise RuntimeError("No model loaded")

        # 构建 prompt
        prompt = self._build_prompt(messages, system_prompt)

        # 获取阻塞生成函数
        def generate_tokens():
            # 创建 sampler
            sampler = make_sampler(temp=temperature)
            return mlx_lm.generate(
                model=self.current_model,
                tokenizer=self._tokenizer,
                prompt=prompt,
                max_tokens=max_tokens,
                sampler=sampler,
            )

        # 在线程池中执行阻塞的生成操作
        loop = asyncio.get_event_loop()
        tokens = await loop.run_in_executor(None, generate_tokens)

        for token in tokens:
            yield token

    def _build_prompt(
        self,
        messages: List[Dict],
        system_prompt: Optional[str] = None
    ) -> str:
        """
        构建对话 prompt

        Args:
            messages: 消息列表 [{role, content}, ...]
            system_prompt: 系统提示词

        Returns:
            str: 构建的 prompt
        """
        # 尝试使用 tokenizer 的 apply_chat_template
        if self._tokenizer is not None:
            try:
                # 构建完整消息列表
                full_messages = []
                if system_prompt:
                    full_messages.append({"role": "system", "content": system_prompt})
                full_messages.extend(messages)

                # 使用 tokenizer 的 chat template
                if hasattr(self._tokenizer, 'apply_chat_template'):
                    prompt = self._tokenizer.apply_chat_template(
                        full_messages,
                        tokenize=False,
                        add_generation_prompt=True
                    )
                    return prompt
            except Exception:
                pass

        # 回退到手动构建 (通用格式)
        parts = []

        if system_prompt:
            parts.append(f"<|system|>\n{system_prompt}\n")

        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")

            if role == "system":
                parts.append(f"<|system|>\n{content}\n")
            elif role == "user":
                parts.append(f"<|user|>\n{content}\n")
            elif role == "assistant":
                parts.append(f"<|assistant|>\n{content}\n")

        parts.append("<|assistant|>\n")

        return "".join(parts)

    def _unload_model(self):
        """卸载模型，释放内存"""
        self.current_model = None
        self._tokenizer = None
        self.current_model_name = None
        gc.collect()

    def get_current_model(self) -> Optional[str]:
        """获取当前加载的模型名称"""
        return self.current_model_name

    def is_model_loaded(self) -> bool:
        """检查是否有模型加载"""
        return self.current_model is not None