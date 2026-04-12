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
        created_at: str = None,
        model_type: str = "local",
        endpoint: str = "",
        remote_provider: str = "",
        remote_base_url: str = "",
        remote_api_key: str = "",
    ):
        self.id = id
        self.name = name
        self.model_id = model_id
        self.description = description
        self.params_count = params_count
        self.quantization = quantization
        self.is_active = is_active
        self.created_at = created_at
        self.model_type = model_type
        self.endpoint = endpoint
        self.remote_provider = remote_provider
        self.remote_base_url = remote_base_url
        self.remote_api_key = remote_api_key

    def to_dict(self) -> dict:
        d = {
            "id": self.id,
            "name": self.name,
            "model_id": self.model_id,
            "description": self.description,
            "params_count": self.params_count,
            "quantization": self.quantization,
            "is_active": self.is_active,
            "created_at": self.created_at,
            "model_type": self.model_type,
            "endpoint": self.endpoint,
            "remote_provider": self.remote_provider,
        }
        if self.model_type == "remote":
            d["remote_base_url"] = self.remote_base_url
            d["has_remote_api_key"] = bool(self.remote_api_key)
        return d


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
            (id, name, model_id, description, params_count, quantization, is_active, created_at, model_type)
            VALUES (?, ?, ?, ?, ?, ?, 1, ?, 'local')
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
            created_at=now,
            model_type="local"
        )

    async def add_remote_model(
        self,
        name: str,
        model_id: str,
        description: str = "",
        endpoint: str = "/chat/completions",
        remote_provider: str = "",
        remote_base_url: str = "",
        remote_api_key: str = "",
    ) -> ModelInfo:
        model_uuid = str(uuid.uuid4())
        now = datetime.now().isoformat()

        await self.db.execute(
            """
            INSERT INTO supported_models
            (id, name, model_id, description, params_count, quantization, is_active,
             created_at, model_type, endpoint, remote_provider, remote_base_url, remote_api_key)
            VALUES (?, ?, ?, ?, '', '', 1, ?, 'remote', ?, ?, ?, ?)
            """,
            (model_uuid, name, model_id, description, now,
             endpoint, remote_provider, remote_base_url, remote_api_key),
        )
        await self.db.commit()

        return ModelInfo(
            id=model_uuid,
            name=name,
            model_id=model_id,
            description=description,
            is_active=True,
            created_at=now,
            model_type="remote",
            endpoint=endpoint,
            remote_provider=remote_provider,
            remote_base_url=remote_base_url,
            remote_api_key=remote_api_key,
        )

    async def list_models(self, active_only: bool = True) -> List[ModelInfo]:
        """
        列出所有支持的模型

        Args:
            active_only: 是否只返回激活的模型

        Returns:
            List[ModelInfo]: 模型列表
        """
        _select = """
            SELECT id, name, model_id, description, params_count, quantization,
                   is_active, created_at,
                   COALESCE(model_type, 'local') as model_type,
                   COALESCE(endpoint, '') as endpoint,
                   COALESCE(remote_provider, '') as remote_provider,
                   COALESCE(remote_base_url, '') as remote_base_url,
                   COALESCE(remote_api_key, '') as remote_api_key
            FROM supported_models
        """
        if active_only:
            rows = await self.db.fetchall(
                _select + " WHERE is_active = 1 ORDER BY model_type DESC, params_count, name"
            )
        else:
            rows = await self.db.fetchall(
                _select + " ORDER BY model_type DESC, params_count, name"
            )

        return [self._row_to_model(row) for row in rows]

    @staticmethod
    def _row_to_model(row) -> ModelInfo:
        return ModelInfo(
            id=row["id"],
            name=row["name"],
            model_id=row["model_id"],
            description=row["description"],
            params_count=row["params_count"],
            quantization=row["quantization"],
            is_active=row["is_active"],
            created_at=row["created_at"],
            model_type=row["model_type"],
            endpoint=row["endpoint"],
            remote_provider=row["remote_provider"],
            remote_base_url=row["remote_base_url"],
            remote_api_key=row["remote_api_key"],
        )

    async def get_model(self, model_id: str) -> Optional[ModelInfo]:
        row = await self.db.fetchone(
            """
            SELECT id, name, model_id, description, params_count, quantization,
                   is_active, created_at,
                   COALESCE(model_type, 'local') as model_type,
                   COALESCE(endpoint, '') as endpoint,
                   COALESCE(remote_provider, '') as remote_provider,
                   COALESCE(remote_base_url, '') as remote_base_url,
                   COALESCE(remote_api_key, '') as remote_api_key
            FROM supported_models
            WHERE id = ? OR model_id = ?
            """,
            (model_id, model_id),
        )
        if row is None:
            return None
        return self._row_to_model(row)

    async def update_model(self, model_id: str, **kwargs) -> Optional[ModelInfo]:
        """
        更新模型信息

        Args:
            model_id: 模型 ID
            **kwargs: 要更新的字段

        Returns:
            Optional[ModelInfo]: 更新后的模型信息
        """
        allowed_fields = [
            "name", "description", "params_count", "quantization", "is_active",
            "model_type", "endpoint", "remote_provider", "remote_base_url", "remote_api_key",
        ]
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