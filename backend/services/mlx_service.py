"""
MLX 模型服务

功能:
- 模型加载与卸载
- 流式生成（真增量 delta）
- 模型生命周期管理
"""

import asyncio
import gc
import logging
import re
import time
from queue import Queue
from typing import Optional, AsyncGenerator, Dict, List

import mlx_lm
from mlx_lm.sample_utils import make_sampler

try:
    from mlx_lm.sample_utils import make_logits_processors as _make_lp
except ImportError:
    _make_lp = None

log = logging.getLogger(__name__)

_THINK_RE = re.compile(r"<think>.*?</think>\s*", re.DOTALL | re.IGNORECASE)


def _build_logits_processors():
    """Build repetition-penalty logits processors if the API is available."""
    if _make_lp is None:
        return None
    try:
        procs = _make_lp(repetition_penalty=1.1, repetition_context_size=256)
        return procs if procs else None
    except Exception:
        return None


class MLXService:
    """MLX 模型服务"""

    def __init__(self):
        self.current_model: Optional[object] = None
        self.current_model_name: Optional[str] = None
        self._tokenizer: Optional[object] = None
        self.model_lock: asyncio.Lock = asyncio.Lock()

    async def load_model(self, model_name: str) -> Dict:
        async with self.model_lock:
            if self.current_model is not None:
                self._unload_model()
                await asyncio.sleep(0.5)

            start_time = time.time()

            try:
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
        if self.current_model is None:
            raise RuntimeError("No model loaded")

        prompt = self._build_prompt(messages, system_prompt)
        sampler = make_sampler(temp=temperature)
        logits_processors = _build_logits_processors()

        stream_generate = getattr(mlx_lm, "stream_generate", None)

        if callable(stream_generate):
            queue: Queue[str | Exception | None] = Queue()

            def generate_tokens_sync():
                kwargs: dict = dict(
                    model=self.current_model,
                    tokenizer=self._tokenizer,
                    prompt=prompt,
                    max_tokens=max_tokens,
                    sampler=sampler,
                )
                if logits_processors is not None:
                    kwargs["logits_processors"] = logits_processors

                try:
                    self._run_stream(stream_generate, kwargs, queue)
                except TypeError as exc:
                    if "logits_processors" in str(exc) and logits_processors is not None:
                        log.warning("logits_processors not supported, retrying without")
                        kwargs.pop("logits_processors", None)
                        self._run_stream(stream_generate, kwargs, queue)
                    else:
                        queue.put(exc)
                except Exception as exc:
                    queue.put(exc)
                finally:
                    queue.put(None)

            producer = asyncio.create_task(asyncio.to_thread(generate_tokens_sync))

            try:
                while True:
                    item = await asyncio.to_thread(queue.get)
                    if item is None:
                        break
                    if isinstance(item, Exception):
                        raise item
                    yield item
            finally:
                await producer
            return

        # Fallback: non-streaming generate
        def generate_text():
            kwargs: dict = dict(
                model=self.current_model,
                tokenizer=self._tokenizer,
                prompt=prompt,
                max_tokens=max_tokens,
                sampler=sampler,
            )
            if logits_processors is not None:
                kwargs["logits_processors"] = logits_processors
            try:
                return mlx_lm.generate(**kwargs)
            except TypeError:
                kwargs.pop("logits_processors", None)
                return mlx_lm.generate(**kwargs)

        loop = asyncio.get_running_loop()
        text = await loop.run_in_executor(None, generate_text)
        if text:
            yield text

    @staticmethod
    def _run_stream(stream_fn, kwargs, queue):
        """Run stream_generate, putting each incremental text segment into queue.

        mlx_lm.stream_generate yields GenerationResponse where .text is the
        *incremental* segment (via detokenizer.last_segment), NOT cumulative.
        """
        for response in stream_fn(**kwargs):
            text = getattr(response, "text", None)
            if text:
                queue.put(text)

    def _build_prompt(
        self,
        messages: List[Dict],
        system_prompt: Optional[str] = None
    ) -> str:
        if self._tokenizer is not None:
            try:
                full_messages = []
                if system_prompt:
                    full_messages.append({"role": "system", "content": system_prompt})
                for msg in messages:
                    if msg.get("role") == "assistant":
                        cleaned = _THINK_RE.sub("", msg["content"]).strip()
                        full_messages.append({"role": "assistant", "content": cleaned or msg["content"]})
                    else:
                        full_messages.append(msg)

                if hasattr(self._tokenizer, 'apply_chat_template'):
                    try:
                        prompt = self._tokenizer.apply_chat_template(
                            full_messages,
                            tokenize=False,
                            add_generation_prompt=True,
                            enable_thinking=False,
                        )
                    except TypeError:
                        prompt = self._tokenizer.apply_chat_template(
                            full_messages,
                            tokenize=False,
                            add_generation_prompt=True,
                        )
                    return prompt
            except Exception as exc:
                log.warning("apply_chat_template failed: %s", exc)

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
        self.current_model = None
        self._tokenizer = None
        self.current_model_name = None
        gc.collect()

    def get_current_model(self) -> Optional[str]:
        return self.current_model_name

    def is_model_loaded(self) -> bool:
        return self.current_model is not None