"""
MLX 模型检测工具

自动扫描本地 HuggingFace 缓存中的 MLX 模型
"""

import os
from pathlib import Path
from typing import List, Dict

# HuggingFace 缓存目录
HF_CACHE_DIR = Path.home() / ".cache" / "huggingface" / "hub"


def detect_local_models() -> List[Dict[str, str]]:
    """
    检测本地已下载的 MLX 模型

    扫描 HuggingFace 缓存目录，查找 mlx-community 或其他 MLX 相关模型

    Returns:
        List[Dict]: 模型信息列表
    """
    models = []

    if not HF_CACHE_DIR.exists():
        return models

    # 扫描模型目录
    for model_dir in HF_CACHE_DIR.iterdir():
        if not model_dir.is_dir():
            continue

        # 解析目录名 (格式: models--org--name)
        if model_dir.name.startswith("models--"):
            parts = model_dir.name.split("--")
            if len(parts) >= 3:
                org = parts[1]
                name = "--".join(parts[2:])

                # 构建完整的 model_id
                model_id = f"{org}/{name}"

                # 检查是否是 MLX 模型
                if _is_mlx_model(model_id, model_dir):
                    # 估算模型大小
                    size = _estimate_model_size(model_dir)

                    models.append({
                        "name": _format_model_name(name),
                        "model_id": model_id,
                        "org": org,
                        "description": f"本地模型，{size}",
                        "params_count": _extract_params(name),
                        "quantization": _extract_quantization(name),
                        "cache_path": str(model_dir)
                    })

    return models


def _is_mlx_model(model_id: str, model_dir: Path) -> bool:
    """检查是否是 MLX 模型"""
    # MLX 社区模型
    if "mlx-community" in model_id.lower():
        return True

    # 检查目录中是否有 MLX 相关文件
    mlx_indicators = ["mlx_model.safetensors", "model.safetensors", "config.json"]
    for indicator in mlx_indicators:
        if (model_dir / indicator).exists():
            return True

    return False


def _format_model_name(name: str) -> str:
    """格式化模型显示名称"""
    # 替换特殊字符
    name = name.replace("-", " ").replace("_", " ")
    return name


def _extract_params(name: str) -> str:
    """从名称中提取参数量"""
    import re

    # 匹配如 7B, 0.5B, 13B 等
    match = re.search(r'(\d+\.?\d*)B', name, re.IGNORECASE)
    if match:
        return f"{match.group(1)}B"

    return ""


def _extract_quantization(name: str) -> str:
    """从名称中提取量化方式"""
    if "4bit" in name.lower():
        return "4bit"
    elif "8bit" in name.lower():
        return "8bit"
    elif "fp16" in name.lower():
        return "fp16"
    elif "fp32" in name.lower():
        return "fp32"
    return "unknown"


def _estimate_model_size(model_dir: Path) -> str:
    """估算模型大小"""
    total_size = 0

    try:
        for root, dirs, files in os.walk(model_dir):
            for file in files:
                file_path = Path(root) / file
                try:
                    total_size += file_path.stat().st_size
                except:
                    pass
    except:
        pass

    # 转换为人类可读格式
    if total_size > 1024 * 1024 * 1024:
        return f"{total_size / (1024 * 1024 * 1024):.1f}GB"
    elif total_size > 1024 * 1024:
        return f"{total_size / (1024 * 1024):.0f}MB"
    else:
        return f"{total_size / 1024:.0f}KB"


def print_local_models() -> List[Dict[str, str]]:
    """打印本地检测到的模型"""
    models = detect_local_models()

    if not models:
        print("未检测到本地 MLX 模型")
        return models

    print(f"\n检测到 {len(models)} 个本地 MLX 模型:")
    print("-" * 80)

    for i, m in enumerate(models, 1):
        print(f"{i}. {m['name']}")
        print(f"   ID: {m['model_id']}")
        print(f"   参数量: {m['params_count']}")
        print(f"   量化: {m['quantization']}")
        print(f"   大小: {m['description']}")
        print()

    return models


if __name__ == "__main__":
    print("=" * 60)
    print("MLX 本地模型检测")
    print("=" * 60)
    print(f"\n扫描目录: {HF_CACHE_DIR}")
    print()

    models = print_local_models()
