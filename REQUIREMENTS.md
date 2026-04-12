# MLX Chat 需求文档

## 已实现功能

- [x] OpenAI 兼容接口 (`/v1/chat/completions`)
- [x] 流式响应 (SSE)
- [x] 多会话管理 (CRUD)
- [x] 模型切换与动态加载
- [x] API Key 认证
- [x] 用量统计
- [x] 模型注册表 (本地 + 远程)
- [x] 远程 API 模型支持 (OpenAI / OpenRouter / SiliconFlow 等)
- [x] Remote Provider 管理 (多 Provider, 各自 base_url + api_key)
- [x] 前端模型选择器 (本地/远程分类显示)
- [x] 远程 API Key 验证
- [x] 一键清理所有 Sessions

## 待实现功能

### 知识库导出 (Session Summary Export)

**描述**: 一键将一个 Session 的所有对话历史总结成一个知识库文件，用户可以选择模板导出为 `.md` 文件并下载。

**用户故事**:
1. 用户与 AI 进行了一轮深入对话，涵盖了某个主题的方方面面
2. 用户希望把对话中的精华内容整理成一份结构化的知识文档
3. 用户点击 "Export as Knowledge Base" 按钮
4. 系统展示多个模板供选择（包括预置模板和用户自定义模板）
5. 用户选择语言（中文/英文）和模板
6. 系统显示预估 token 数，如果使用远程模型则提示用户
7. 后端调用当前加载的模型对对话历史进行总结/提炼
8. 用户可在生成过程中取消
9. 生成完成后自动下载 `.md` 文件（不保存到后端）

**核心规则**:

| 问题 | 决定 |
|------|------|
| 生成模型 | 使用**当前加载的模型** |
| 自定义模板 | 支持，模板存储在**数据库**，用户可创建/编辑/删除 |
| 导出内容 | 仅 AI 生成的总结，**不包含原始对话** |
| 输出格式 | Markdown (`.md`) |
| 远程模型提示 | 需要，显示**预估 token 数**和**费用提示** |
| 多语言 | 用户可选择**中文**或**英文**导出 |
| 存储方式 | **纯前端下载**，后端不保存 |
| 批量导出 | **不支持** |
| 取消/重试 | 支持**取消**，失败**显示错误可重试** |

**预置模板**:

#### 模板 1: 学习笔记 (Study Notes / 学习笔记)

```markdown
# {{session_name}} - 学习笔记

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

{{AI 根据对话内容推荐的进一步学习方向}}
```

#### 模板 2: 会议纪要 (Meeting Minutes / 会议纪要)

```markdown
# {{session_name}} - 会议纪要

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

### 议题 2: {{topic}}
...

## 待办事项

- [ ] {{action_item_1}}
- [ ] {{action_item_2}}

## 后续跟进

{{AI 建议的后续步骤}}
```

#### 模板 3: 技术文档 (Technical Document / 技术文档)

```markdown
# {{session_name}} - 技术文档

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

{{对话中提及的相关文档、链接、API 等}}
```

#### 模板 4: 知识卡片 (Knowledge Cards / 知识卡片)

```markdown
# {{session_name}} - 知识卡片

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

...

---

## 术语表

| 术语 | 定义 |
|------|------|
| {{term}} | {{definition}} |
```

**自定义模板功能**:

用户可以创建自己的模板，存储在数据库中。

模板数据结构:
```python
class ExportTemplate:
    id: str                    # UUID
    name: str                  # 模板名称，如 "我的读书笔记"
    description: str           # 简短描述
    language: str              # "zh" 或 "en" 或 "both"
    template_content: str      # Markdown 模板内容，含占位符
    system_prompt: str         # 指导 AI 如何填充模板的提示词
    is_builtin: bool           # 是否为预置模板（预置模板不可删除）
    created_at: datetime
    updated_at: datetime
```

模板示例（用户创建时可参考）:
```markdown
# 自定义模板示例：读书笔记

## 书籍信息
- 书名：{{AI 提取的书籍名称}}
- 作者：{{AI 提取的作者}}

## 核心观点
{{AI 总结的 3-5 个核心观点}}

## 精彩摘录
{{AI 提取的对话中引用的重要段落}}

## 我的思考
{{AI 整理的用户（在对话中）表达的观点和反思}}

## 行动清单
- [ ] {{AI 建议的下一步行动}}
```

**技术方案**:

### 后端

#### 数据库迁移
新增 `export_templates` 表:
```sql
CREATE TABLE export_templates (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT DEFAULT '',
    language TEXT DEFAULT 'both',
    template_content TEXT NOT NULL,
    system_prompt TEXT NOT NULL,
    is_builtin BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### API 端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/v1/export/templates` | GET | 获取所有模板列表（预置 + 用户自定义） |
| `/api/v1/export/templates` | POST | 创建自定义模板 |
| `/api/v1/export/templates/{id}` | GET | 获取模板详情 |
| `/api/v1/export/templates/{id}` | PATCH | 更新自定义模板 |
| `/api/v1/export/templates/{id}` | DELETE | 删除自定义模板 |
| `/api/v1/sessions/{session_id}/export/estimate` | POST | 预估导出 token 数 |
| `/api/v1/sessions/{session_id}/export` | POST | 生成知识库文件（SSE 流式） |

#### 导出流程

1. **预估阶段** (`/export/estimate`):
   - 获取对话历史
   - 计算 input token 预估值
   - 如果是远程模型，返回费用提示信息
   - 返回: `{ "estimated_tokens": 5000, "is_remote": true, "warning": "此操作将使用远程 API，预计消耗约 5000 tokens" }`

2. **生成阶段** (`/export`):
   - 请求参数: `template_id`, `language` ("zh" | "en")
   - 构建 prompt: 对话历史 + 模板 system_prompt + 语言指令
   - SSE 流式返回生成内容，支持客户端中断
   - 完成后返回 `event: done` + 完整 markdown 内容

### 前端

#### UI 流程

1. **入口**: Session 列表中每个 session 的操作菜单添加 "导出知识库" 按钮
2. **第一步 - 选择模板**:
   - 显示模板列表，分为"预置模板"和"我的模板"
   - 每个模板显示名称、描述、适用语言
   - 点击可预览模板结构
3. **第二步 - 选择语言**: 中文 / 英文 单选
4. **第三步 - 确认导出**:
   - 显示预估 token 数
   - 如果是远程模型，显示警告提示
   - 用户确认后开始生成
5. **生成中**:
   - 流式显示生成内容预览
   - 提供"取消"按钮
6. **完成后**:
   - 自动触发 `.md` 文件下载
   - 显示"导出成功"提示
7. **失败处理**:
   - 显示错误信息
   - 提供"重试"按钮

#### 自定义模板管理

- 在 Settings 页面添加"导出模板管理"区域
- 支持创建、编辑、删除自定义模板
- 编辑器: 文本框输入 markdown 模板，侧边显示占位符说明
- 提供模板示例帮助用户理解如何编写

**验收标准**:

- [ ] 后端: 数据库迁移成功，`export_templates` 表创建
- [ ] 后端: 预置 4 个模板初始化
- [ ] 后端: 模板 CRUD API 可用
- [ ] 后端: 预估 token API 返回正确数据
- [ ] 后端: 导出 API 支持 SSE 流式响应
- [ ] 后端: 导出 API 支持语言选择
- [ ] 后端: 客户端断开连接时正确中断生成
- [ ] 前端: Session 操作菜单有导出入口
- [ ] 前端: 模板选择 UI（预览、分组显示）
- [ ] 前端: 语言选择
- [ ] 前端: 远程模型费用提示
- [ ] 前端: 流式内容预览
- [ ] 前端: 取消按钮可用
- [ ] 前端: 自动下载 .md 文件
- [ ] 前端: 失败显示错误，可重试
- [ ] 前端: Settings 页面模板管理功能
- [ ] 测试: 后端模板 API 测试
- [ ] 测试: 后端导出 API 测试（mock 模型）
- [ ] 测试: 前端组件测试
