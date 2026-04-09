"""
MLX 服务实例管理

避免循环导入
"""

from backend.services.mlx_service import MLXService


# 全局 MLX 服务实例
_mlx_service: MLXService = None


def get_mlx_service() -> MLXService:
    """获取 MLX 服务实例"""
    global _mlx_service
    if _mlx_service is None:
        _mlx_service = MLXService()
    return _mlx_service


def init_mlx_service() -> MLXService:
    """初始化 MLX 服务（如果已存在则返回现有实例）"""
    global _mlx_service
    if _mlx_service is None:
        _mlx_service = MLXService()
    return _mlx_service