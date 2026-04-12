"""
导出模板服务

管理知识库导出的模板，支持预置模板和用户自定义模板
"""

import uuid
from datetime import datetime
from typing import Optional, List

from backend.database import Database


class ExportTemplateInfo:
    """导出模板信息"""
    def __init__(
        self,
        id: str,
        name: str,
        description: str = "",
        language: str = "both",
        template_content: str = "",
        system_prompt: str = "",
        is_builtin: bool = False,
        created_at: str = None,
        updated_at: str = None,
    ):
        self.id = id
        self.name = name
        self.description = description
        self.language = language
        self.template_content = template_content
        self.system_prompt = system_prompt
        self.is_builtin = is_builtin
        self.created_at = created_at
        self.updated_at = updated_at

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "language": self.language,
            "template_content": self.template_content,
            "system_prompt": self.system_prompt,
            "is_builtin": self.is_builtin,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


class ExportTemplateService:
    """导出模板服务"""

    # 4 个预置模板
    DEFAULT_TEMPLATES = [
        {
            "name": "学习笔记",
            "description": "将对话内容整理成学习笔记格式，适合学习新知识后整理总结",
            "language": "both",
            "template_content": """# {{session_name}} - 学习笔记

> 导出时间: {{export_date}}
> 对话轮数: {{message_count}}

## 概述

{{AI 生成的对话核心要点总结，3-5 句话}}

## 关键概念

{{AI 从对话中提取的关键概念列表，每个概念附简要说明}}

## 详细内容

{{AI 按主题整理的对话精华内容，以 Q&A 或知识点形式呈现}}

## 实践要点

{{AI 提取的可操作建议、步骤或注意事项}}

## 延伸阅读

{{AI 根据对话内容推荐的进一步学习方向}}""",
            "system_prompt": """你是一个知识整理助手。请根据提供的对话内容，整理成一份结构化的学习笔记。

要求：
1. 提取对话中的核心要点，简要总结（3-5句话）
2. 列出关键概念并给出简要说明
3. 按主题整理对话精华内容，以知识点形式呈现
4. 提取可操作的实践建议
5. 推荐进一步学习方向

请直接输出整理好的 Markdown 内容，不要有前言或后记。"""
        },
        {
            "name": "会议纪要",
            "description": "将对话整理成会议纪要格式，适合记录讨论过程和结论",
            "language": "both",
            "template_content": """# {{session_name}} - 会议纪要

> 日期: {{export_date}}
> 参与者: User & AI Assistant

## 讨论议题

{{AI 总结的讨论主题列表}}

## 核心决议

{{AI 提取的关键结论和决定}}

## 详细讨论

### 议题 1: {{topic}}
- **背景**: {{context}}
- **讨论要点**: {{points}}
- **结论**: {{conclusion}}

## 待办事项

- [ ] {{action_item_1}}
- [ ] {{action_item_2}}

## 后续跟进

{{AI 建议的后续步骤}}""",
            "system_prompt": """你是一个会议记录助手。请根据提供的对话内容，整理成一份标准的会议纪要。

要求：
1. 总结讨论的主要议题
2. 提取关键结论和决定
3. 详细整理每个议题的背景、讨论要点和结论
4. 提取待办事项（如果没有明确的待办，可以基于讨论内容推断合理的行动项）
5. 给出后续跟进建议

请直接输出整理好的 Markdown 内容，不要有前言或后记。"""
        },
        {
            "name": "技术文档",
            "description": "将对话整理成技术文档格式，适合记录技术问题和解决方案",
            "language": "both",
            "template_content": """# {{session_name}} - 技术文档

> 导出时间: {{export_date}}

## 问题背景

{{AI 总结的技术问题描述}}

## 解决方案

{{AI 整理的方案概述}}

## 实现细节

### 架构设计
{{AI 提取的架构相关信息}}

### 代码示例
{{对话中出现的代码片段，按语言/功能分类整理}}

### 配置说明
{{相关配置项和说明}}

## 注意事项

{{AI 提取的坑点、限制和最佳实践}}

## 参考资料

{{对话中提及的相关文档、链接、API 等}}""",
            "system_prompt": """你是一个技术文档助手。请根据提供的对话内容，整理成一份技术文档。

要求：
1. 清晰描述问题的背景
2. 整理解决方案的概述
3. 详细说明架构设计
4. 提取代码示例，按语言/功能分类
5. 列出相关配置项和说明
6. 提取注意事项、最佳实践和踩坑记录
7. 整理对话中提及的相关资料

请直接输出整理好的 Markdown 内容，不要有前言或后记。"""
        },
        {
            "name": "知识卡片",
            "description": "将对话整理成知识卡片格式，适合快速查阅和信息提取",
            "language": "both",
            "template_content": """# {{session_name}} - 知识卡片

> 导出时间: {{export_date}}

---

## 卡片 1: {{card_title}}

**Q**: {{question}}
**A**: {{answer}}
**Tags**: #{{tag1}} #{{tag2}}

---

## 卡片 2: {{card_title}}

**Q**: {{question}}
**A**: {{answer}}
**Tags**: #{{tag1}} #{{tag2}}

---

## 术语表

| 术语 | 定义 |
|------|------|
| {{term}} | {{definition}} |""",
            "system_prompt": """你是一个知识卡片助手。请根据提供的对话内容，整理成一系列知识卡片。

要求：
1. 将对话中的核心内容提取成 Q&A 格式的知识卡片
2. 每张卡片包含：问题、答案、相关标签
3. 卡片之间保持独立性和关联性
4. 整理术语表，包含对话中出现的专业术语及其定义
5. 标签应该简洁、有代表性

请直接输出整理好的 Markdown 内容，不要有前言或后记。"""
        },
    ]

    def __init__(self, db: Database):
        self.db = db

    async def initialize(self):
        """初始化预置模板"""
        # 检查是否已有模板
        count = await self.db.fetchval("SELECT COUNT(*) FROM export_templates WHERE is_builtin = 1")
        if count == 0:
            # 添加预置模板
            for template in self.DEFAULT_TEMPLATES:
                await self._create_template(
                    name=template["name"],
                    description=template.get("description", ""),
                    language=template.get("language", "both"),
                    template_content=template["template_content"],
                    system_prompt=template["system_prompt"],
                    is_builtin=True,
                )

    async def _create_template(
        self,
        name: str,
        template_content: str,
        system_prompt: str,
        description: str = "",
        language: str = "both",
        is_builtin: bool = False,
    ) -> ExportTemplateInfo:
        """内部方法：创建模板"""
        template_id = str(uuid.uuid4())
        now = datetime.now().isoformat()

        await self.db.execute(
            """
            INSERT INTO export_templates
            (id, name, description, language, template_content, system_prompt, is_builtin, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (template_id, name, description, language, template_content, system_prompt, is_builtin, now, now)
        )
        await self.db.commit()

        return ExportTemplateInfo(
            id=template_id,
            name=name,
            description=description,
            language=language,
            template_content=template_content,
            system_prompt=system_prompt,
            is_builtin=is_builtin,
            created_at=now,
            updated_at=now,
        )

    async def list_templates(self) -> List[ExportTemplateInfo]:
        """
        列出所有模板

        Returns:
            List[ExportTemplateInfo]: 模板列表
        """
        rows = await self.db.fetchall(
            """
            SELECT id, name, description, language, template_content, system_prompt,
                   is_builtin, created_at, updated_at
            FROM export_templates
            ORDER BY is_builtin DESC, created_at ASC
            """
        )

        return [self._row_to_template(row) for row in rows]

    @staticmethod
    def _row_to_template(row) -> ExportTemplateInfo:
        return ExportTemplateInfo(
            id=row["id"],
            name=row["name"],
            description=row["description"] or "",
            language=row["language"] or "both",
            template_content=row["template_content"],
            system_prompt=row["system_prompt"],
            is_builtin=bool(row["is_builtin"]),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    async def get_template(self, template_id: str) -> Optional[ExportTemplateInfo]:
        """
        获取单个模板

        Args:
            template_id: 模板 ID

        Returns:
            Optional[ExportTemplateInfo]: 模板信息
        """
        row = await self.db.fetchone(
            """
            SELECT id, name, description, language, template_content, system_prompt,
                   is_builtin, created_at, updated_at
            FROM export_templates
            WHERE id = ?
            """,
            (template_id,)
        )

        if row is None:
            return None
        return self._row_to_template(row)

    async def create_template(
        self,
        name: str,
        template_content: str,
        system_prompt: str,
        description: str = "",
        language: str = "both",
    ) -> ExportTemplateInfo:
        """
        创建自定义模板

        Args:
            name: 模板名称
            template_content: 模板内容
            system_prompt: 系统提示词
            description: 描述
            language: 支持语言

        Returns:
            ExportTemplateInfo: 创建的模板信息
        """
        return await self._create_template(
            name=name,
            template_content=template_content,
            system_prompt=system_prompt,
            description=description,
            language=language,
            is_builtin=False,
        )

    async def update_template(self, template_id: str, **kwargs) -> Optional[ExportTemplateInfo]:
        """
        更新模板

        Args:
            template_id: 模板 ID
            **kwargs: 要更新的字段

        Returns:
            Optional[ExportTemplateInfo]: 更新后的模板信息

        Raises:
            PermissionError: 如果尝试更新预置模板
        """
        # 检查是否是预置模板
        template = await self.get_template(template_id)
        if template is None:
            return None

        if template.is_builtin:
            raise PermissionError("Cannot update builtin template")

        allowed_fields = ["name", "description", "language", "template_content", "system_prompt"]
        updates = []
        values = []

        for field in allowed_fields:
            if field in kwargs and kwargs[field] is not None:
                updates.append(f"{field} = ?")
                values.append(kwargs[field])

        if not updates:
            return template

        # 添加 updated_at
        updates.append("updated_at = ?")
        values.append(datetime.now().isoformat())

        values.append(template_id)

        await self.db.execute(
            f"""
            UPDATE export_templates
            SET {', '.join(updates)}
            WHERE id = ?
            """,
            values
        )
        await self.db.commit()

        return await self.get_template(template_id)

    async def delete_template(self, template_id: str) -> bool:
        """
        删除模板

        Args:
            template_id: 模板 ID

        Returns:
            bool: 是否成功

        Raises:
            PermissionError: 如果尝试删除预置模板
        """
        # 检查是否是预置模板
        template = await self.get_template(template_id)
        if template is None:
            return False

        if template.is_builtin:
            raise PermissionError("Cannot delete builtin template")

        await self.db.execute(
            "DELETE FROM export_templates WHERE id = ?",
            (template_id,)
        )
        await self.db.commit()

        return True

    async def build_export_prompt(
        self,
        session_id: str,
        api_key_id: str,
        template: ExportTemplateInfo,
        language: str
    ) -> tuple[list, str]:
        """
        构建导出的 prompt

        Args:
            session_id: 会话 ID
            api_key_id: API Key ID
            template: 模板信息
            language: 输出语言 (zh/en)

        Returns:
            tuple[list, str]: (对话消息列表, system_prompt)
        """
        from backend.services.session_service import SessionService

        session_service = SessionService(self.db)

        # 获取会话消息
        messages = await session_service.get_messages(session_id, api_key_id)

        # 转换为对话格式
        chat_messages = []
        for msg in messages:
            role = msg.get("role", "user")
            if role in ("user", "assistant"):
                chat_messages.append({
                    "role": role,
                    "content": msg.get("content", "")
                })

        # 构建 system_prompt，添加语言指令（与模板语言一致，避免模型忽略）
        if language == "zh":
            language_instruction = (
                "【输出语言 — 必须遵守】全文使用简体中文撰写最终 Markdown。"
                "正文、小标题、列表说明均用中文；仅专有名词、代码块、URL、文件路径可保留英文原文。"
                "禁止用英文写整段说明或整节标题（除非原文引用）。"
            )
        else:
            language_instruction = (
                "[Output language — required] Write the entire Markdown result in English. "
                "Use English for all headings, list items, and prose. "
                "Keep non-English only inside quoted source text, code blocks, or proper nouns."
            )
        system_prompt = f"{template.system_prompt}\n\n{language_instruction}"

        return chat_messages, system_prompt

    async def estimate_export_tokens(
        self,
        session_id: str,
        api_key_id: str,
        template: ExportTemplateInfo
    ) -> int:
        """
        预估导出所需的 token 数

        基于对话总长度估算 (简化实现，实际应使用 tokenizer)

        Args:
            session_id: 会话 ID
            api_key_id: API Key ID
            template: 模板信息

        Returns:
            int: 预估 token 数
        """
        from backend.services.session_service import SessionService

        session_service = SessionService(self.db)
        messages = await session_service.get_messages(session_id, api_key_id)

        # 简单估算：总字符数 / 4 (中英文混合的平均 token 比率)
        total_chars = sum(len(msg.get("content", "")) for msg in messages)

        # 添加模板内容的估算
        template_chars = len(template.template_content) + len(template.system_prompt)

        # 总估算 token (中文约 2 字符/token，英文约 4 字符/token，取平均)
        estimated = int((total_chars + template_chars) / 3)

        return max(estimated, 100)  # 至少返回 100
