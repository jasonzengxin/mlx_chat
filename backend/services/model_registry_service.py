"""
模型注册服务

管理支持的 MLX 模型列表
"""

import uuid
from datetime import datetime
from typing import Optional, List, Dict

from backend.database import Database


class ModelInfo:
    """模型信息"""
    def __init__(
        self,
        id: str,
        name: str,
        model_id: str,
        description: str = "",
        params_count: str = "",
        quantization: str = "",
        is_active: bool = True,
        created_at: str = None
    ):
        self.id = id
        self.name = name
        self.model_id = model_id  # HuggingFace model ID
        self.description = description
        self.params_count = params_count  # 如 "7B", "0.5B"
        self.quantization = quantization  # 如 "4bit", "8bit"
        self.is_active = is_active
        self.created_at = created_at

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "model_id": self.model_id,
            "description": self.description,
            "params_count": self.params_count,
            "quantization": self.quantization,
            "is_active": self.is_active,
            "created_at": self.created_at
        }


class ModelRegistryService:
    """模型注册服务"""

    # 预置的推荐模型
    DEFAULT_MODELS = [
        {
            "name": "Qwen2.5-0.5B-Instruct",
            "model_id": "mlx-community/Qwen2.5-0.5B-Instruct-4bit",
            "description": "轻量级对话模型，适合测试",
            "params_count": "0.5B",
            "quantization": "4bit"
        },
        {
            "name": "Qwen2.5-3B-Instruct",
            "model_id": "mlx-community/Qwen2.5-3B-Instruct-4bit",
            "description": "平衡性能与质量",
            "params_count": "3B",
            "quantization": "4bit"
        },
        {
            "name": "Qwen2.5-7B-Instruct",
            "model_id": "mlx-community/Qwen2.5-7B-Instruct-4bit",
            "description": "高质量对话模型",
            "params_count": "7B",
            "quantization": "4bit"
        },
        {
            "name": "Qwen3-8B",
            "model_id": "mlx-community/Qwen3-8B-4bit",
            "description": "最新 Qwen3 模型",
            "params_count": "8B",
            "quantization": "4bit"
        },
        {
            "name": "Llama-3.2-1B-Instruct",
            "model_id": "mlx-community/Llama-3.2-1B-Instruct-4bit",
            "description": "Meta Llama 3.2 轻量版",
            "params_count": "1B",
            "quantization": "4bit"
        },
        {
            "name": "Llama-3.2-3B-Instruct",
            "model_id": "mlx-community/Llama-3.2-3B-Instruct-4bit",
            "description": "Meta Llama 3.2 标准版",
            "params_count": "3B",
            "quantization": "4bit"
        },
    ]

    def __init__(self, db: Database):
        self.db = db

    async def initialize(self):
        """初始化模型表，添加默认模型"""
        # 检查是否已有模型
        count = await self.db.fetchval("SELECT COUNT(*) FROM supported_models")
        if count == 0:
            # 添加默认模型
            for model in self.DEFAULT_MODELS:
                await self.add_model(
                    name=model["name"],
                    model_id=model["model_id"],
                    description=model.get("description", ""),
                    params_count=model.get("params_count", ""),
                    quantization=model.get("quantization", "")
                )

    async def add_model(
        self,
        name: str,
        model_id: str,
        description: str = "",
        params_count: str = "",
        quantization: str = ""
    ) -> ModelInfo:
        """
        添加新模型

        Args:
            name: 显示名称
            model_id: HuggingFace 模型 ID (如 mlx-community/Qwen2.5-7B-4bit)
            description: 描述
            params_count: 参数量
            quantization: 量化方式

        Returns:
            ModelInfo: 创建的模型信息
        """
        model_uuid = str(uuid.uuid4())
        now = datetime.now().isoformat()

        await self.db.execute(
            """
            INSERT INTO supported_models
            (id, name, model_id, description, params_count, quantization, is_active, created_at)
            VALUES (?, ?, ?, ?, ?, ?, 1, ?)
            """,
            (model_uuid, name, model_id, description, params_count, quantization, now)
        )
        await self.db.commit()

        return ModelInfo(
            id=model_uuid,
            name=name,
            model_id=model_id,
            description=description,
            params_count=params_count,
            quantization=quantization,
            is_active=True,
            created_at=now
        )

    async def list_models(self, active_only: bool = True) -> List[ModelInfo]:
        """
        列出所有支持的模型

        Args:
            active_only: 是否只返回激活的模型

        Returns:
            List[ModelInfo]: 模型列表
        """
        if active_only:
            rows = await self.db.fetchall(
                """
                SELECT id, name, model_id, description, params_count, quantization, is_active, created_at
                FROM supported_models
                WHERE is_active = 1
                ORDER BY params_count, name
                """
            )
        else:
            rows = await self.db.fetchall(
                """
                SELECT id, name, model_id, description, params_count, quantization, is_active, created_at
                FROM supported_models
                ORDER BY params_count, name
                """
            )

        return [
            ModelInfo(
                id=row["id"],
                name=row["name"],
                model_id=row["model_id"],
                description=row["description"],
                params_count=row["params_count"],
                quantization=row["quantization"],
                is_active=row["is_active"],
                created_at=row["created_at"]
            )
            for row in rows
        ]

    async def get_model(self, model_id: str) -> Optional[ModelInfo]:
        """
        获取模型信息

        Args:
            model_id: 模型 ID 或 HuggingFace ID

        Returns:
            Optional[ModelInfo]: 模型信息
        """
        # 先按 UUID 查找
        row = await self.db.fetchone(
            """
            SELECT id, name, model_id, description, params_count, quantization, is_active, created_at
            FROM supported_models
            WHERE id = ? OR model_id = ?
            """,
            (model_id, model_id)
        )

        if row is None:
            return None

        return ModelInfo(
            id=row["id"],
            name=row["name"],
            model_id=row["model_id"],
            description=row["description"],
            params_count=row["params_count"],
            quantization=row["quantization"],
            is_active=row["is_active"],
            created_at=row["created_at"]
        )

    async def update_model(self, model_id: str, **kwargs) -> Optional[ModelInfo]:
        """
        更新模型信息

        Args:
            model_id: 模型 ID
            **kwargs: 要更新的字段

        Returns:
            Optional[ModelInfo]: 更新后的模型信息
        """
        allowed_fields = ["name", "description", "params_count", "quantization", "is_active"]
        updates = []
        values = []

        for field in allowed_fields:
            if field in kwargs:
                updates.append(f"{field} = ?")
                values.append(kwargs[field])

        if not updates:
            return await self.get_model(model_id)

        values.append(model_id)

        await self.db.execute(
            f"""
            UPDATE supported_models
            SET {', '.join(updates)}
            WHERE id = ? OR model_id = ?
            """,
            values + [model_id]
        )
        await self.db.commit()

        return await self.get_model(model_id)

    async def delete_model(self, model_id: str) -> bool:
        """
        删除模型 (软删除，设置为不活跃)

        Args:
            model_id: 模型 ID

        Returns:
            bool: 是否成功
        """
        result = await self.db.execute(
            "UPDATE supported_models SET is_active = 0 WHERE id = ? OR model_id = ?",
            (model_id, model_id)
        )
        await self.db.commit()

        return result.rowcount > 0

    async def validate_model_id(self, model_id: str) -> bool:
        """
        验证模型 ID 是否有效

        检查格式: 应为 mlx-community/xxx 或符合 HuggingFace ID 格式

        Args:
            model_id: HuggingFace 模型 ID

        Returns:
            bool: 是否有效
        """
        if not model_id:
            return False

        # 检查基本格式 (org/model-name)
        parts = model_id.split("/")
        if len(parts) != 2:
            return False

        # 检查是否是 MLX 社区模型或用户自定义
        org, name = parts
        if not org or not name:
            return False

        return True