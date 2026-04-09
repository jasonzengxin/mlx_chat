"""
集成测试 - 直接测试 MLX 服务

直接调用 MLX 服务，不通过 HTTP
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

import asyncio
import time


async def main():
    print("=" * 60)
    print("MLX 直接服务测试")
    print("=" * 60)

    # 导入 MLX 服务
    from backend.mlx_instance import get_mlx_service

    mlx_service = get_mlx_service()
    model_name = "mlx-community/Qwen2.5-0.5B-Instruct-4bit"

    # 1. 加载模型
    print(f"\n[1] 加载模型: {model_name}")
    start = time.time()
    try:
        result = await mlx_service.load_model(model_name)
        elapsed = time.time() - start
        print(f"    结果: {result}")
        print(f"    耗时: {elapsed:.1f}s")
    except Exception as e:
        print(f"    加载失败: {type(e).__name__}: {e}")
        return

    # 2. 测试生成
    print("\n[2] 测试生成...")
    messages = [{"role": "user", "content": "1+1等于几？只回答数字。"}]

    try:
        response = ""
        start = time.time()
        async for token in mlx_service.generate_stream(
            messages=messages,
            temperature=0.1,
            max_tokens=50
        ):
            response += token
            print(f"    token: {token}", end="", flush=True)
        elapsed = time.time() - start
        print()
        print(f"    完整回答: {response}")
        print(f"    耗时: {elapsed:.1f}s")
    except Exception as e:
        print(f"    生成失败: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "=" * 60)
    print("测试完成!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
