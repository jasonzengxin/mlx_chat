# TDD Implementation Progress

## Project Overview

Apple Silicon MLX model chat API with OpenAI-compatible interface.

- **Backend**: FastAPI + aiosqlite + mlx-lm
- **Frontend**: Vue 3 + Vite + Pinia + TypeScript
- **Testing**: pytest (251 backend), Vitest (79 frontend)

---

## Completed Features ✅

### 1. Core Infrastructure

| Feature | Status | Tests |
|---------|--------|-------|
| Database helper class | ✅ | - |
| API Key generation (SHA256) | ✅ | `test_api_key.py` (5) |
| API Key authentication | ✅ | `test_auth_service.py` (6) |
| Pydantic request models | ✅ | - |
| FastAPI lifespan management | ✅ | - |
| Database migration (auto-add columns) | ✅ | `test_database_migration.py` |

### 2. MLX Model Service

| Feature | Status | Tests |
|---------|--------|-------|
| Model loading/unloading | ✅ | `test_mlx_service.py` (8) |
| Stream generation | ✅ | `test_mlx_service.py` |
| Sampler creation | ✅ | - |
| Prompt building (chat template) | ✅ | - |
| Thread pool execution | ✅ | - |

### 3. Session Management

| Feature | Status | Tests |
|---------|--------|-------|
| Create session | ✅ | `test_session_service.py` (15) |
| List sessions | ✅ | |
| Get session detail | ✅ | |
| Update session | ✅ | |
| Delete session | ✅ | |
| Delete all sessions | ✅ | `test_sessions_api.py` (4) |
| Add message (with duration_ms) | ✅ | |
| Get messages | ✅ | |

### 4. Chat API

| Feature | Status | Tests |
|---------|--------|-------|
| POST /api/v1/chat | ✅ | `test_chat_api.py` (6) |
| SSE streaming response | ✅ | |
| Temperature parameter | ✅ | |
| Max tokens parameter | ✅ | |
| System prompt | ✅ | |
| Duration tracking (duration_ms) | ✅ | `test_chat_duration.py` |
| TTFT tracking (ttft_ms) | ✅ | |
| Generation speed (chars/s) | ✅ | |

### 5. OpenAI Compatible API

| Feature | Status | Tests |
|---------|--------|-------|
| GET /v1/models | ✅ | `test_openai_api.py` (12) |
| POST /v1/chat/completions | ✅ | |
| Non-streaming response | ✅ | |
| SSE streaming response | ✅ | |
| OpenAI response format | ✅ | |
| Token usage tracking | ✅ | |

### 6. Model Registry

| Feature | Status | Tests |
|---------|--------|-------|
| List registered models | ✅ | `test_model_registry_api.py` (16) |
| Add new model | ✅ | |
| Get model detail | ✅ | |
| Update model info | ✅ | |
| Soft delete model | ✅ | |
| Validate model ID format | ✅ | |
| Load model from registry | ✅ | |
| Auto-detect local MLX models | ✅ | |
| Remote model support | ✅ | `test_remote_model_e2e.py` (9) |
| Model type routing (local/remote) | ✅ | |

### 7. Remote API Support

| Feature | Status | Tests |
|---------|--------|-------|
| Remote API settings (base_url, api_key) | ✅ | `test_settings_api.py` (7) |
| Remote model chat (httpx streaming) | ✅ | `test_remote_model_e2e.py` |
| Remote API key validation | ✅ | |
| Remote provider management | ✅ | |
| Model type routing | ✅ | |
| API key security (not exposed in GET) | ✅ | |
| Base URL trailing slash handling | ✅ | |

### 8. Usage Tracking (Backend API)

| Feature | Status | Tests |
|---------|--------|-------|
| Record usage | ✅ | `test_usage_service.py` (14) |
| Get usage summary | ✅ | |
| Period filtering | ✅ | |
| API key isolation | ✅ | |
| Recent logs query | ✅ | |

### 9. Settings & API Key Management (Backend API)

| Feature | Status | Tests |
|---------|--------|-------|
| Get/Update settings | ✅ | `test_settings_api.py` (21) |
| List API keys | ✅ | |
| Create API key | ✅ | |
| Delete API key | ✅ | |
| Key prefix display | ✅ | |

### 10. Integration Tests

| Feature | Status | Tests |
|---------|--------|-------|
| Real MLX model loading | ✅ | `integration/` (3) |
| HTTP API chat test | ✅ | |
| Stream/non-stream response | ✅ | |

### 11. Frontend (Vue 3)

| Feature | Status | Tests |
|---------|--------|-------|
| Project setup (Vite + Vue 3 + TypeScript) | ✅ | ✅ `api.test.ts` |
| Chat UI component | ✅ | ✅ `chat.test.ts` |
| Session list sidebar (create/delete/rename) | ✅ | ✅ `session.ts` store |
| Model selector dropdown (local/remote) | ✅ | ✅ `models.test.ts` |
| SSE stream rendering | ✅ | ✅ `chat.test.ts` |
| Pinia store for state management | ✅ | ✅ 3 store tests |
| API Key input modal | ✅ | ✅ `api.test.ts` |
| Models API & Store | ✅ | ✅ `models.test.ts` |
| Settings page (API Key list) | ✅ | `ApiKeyList.vue` |
| Remote API configuration UI | ✅ | `SettingsView.vue` |
| Remote model add form | ✅ | `SettingsView.vue` |
| Provider preset (OpenAI/OpenRouter/SiliconFlow) | ✅ | `SettingsView.vue` |
| API Key validation button | ✅ | `SettingsView.vue` |
| Dark/Light theme toggle | ✅ | `settings.ts` |
| 会话历史消息加载 | ✅ | `session.ts` - `loadSessionMessages()` |
| 实时生成进度 (token 计数、速度) | ✅ | `ChatArea.vue`, `MessageBubble.vue` |
| 生成耗时显示 (duration, TTFT) | ✅ | `MessageBubble.vue` - duration badge |
| 消息 Markdown 渲染 | ✅ | `MessageBubble.vue` - marked.js |
| Thinking process 折叠显示 | ✅ | `MessageBubble.vue` - thought 解析 |
| 一键清理所有 Sessions | ✅ | `SessionList.vue` - clear all button |
| 参数调节面板 | ✅ | `ParameterPanel.vue` |
| 用量统计展示 UI | ✅ | `UsageStats.vue` - 4-stat grid + period filter |
| CORS 配置界面 | ✅ | `SettingsView.vue` CORS section |

---

## Pending Features 🚧

### Priority 1 - 知识库导出 🔴

> 需求文档: `REQUIREMENTS.md`

将 Session 对话历史总结为知识库文件，用户选择模板和语言后导出 `.md` 文件下载。

#### 1.1 后端 - 模板管理

| 项目 | 状态 | 说明 |
|------|------|------|
| 数据库迁移: `export_templates` 表 | ✅ | id, name, description, language, template_content, system_prompt, is_builtin, created_at, updated_at |
| 预置 4 个模板初始化 | ✅ | 学习笔记、会议纪要、技术文档、知识卡片 |
| ExportTemplateService | ✅ | 模板 CRUD service |
| GET /api/v1/export/templates | ✅ | 获取模板列表 (预置 + 用户自定义) |
| POST /api/v1/export/templates | ✅ | 创建自定义模板 |
| GET /api/v1/export/templates/{id} | ✅ | 获取模板详情 |
| PATCH /api/v1/export/templates/{id} | ✅ | 更新自定义模板 |
| DELETE /api/v1/export/templates/{id} | ✅ | 删除自定义模板 (预置不可删) |
| 后端测试: 模板 CRUD API | ✅ | `test_export_templates_api.py` (20 tests) |
| 后端测试: 预置模板初始化 | ✅ | 包含在 test_export_templates_api.py |

#### 1.2 后端 - 导出生成

| 项目 | 状态 | 说明 |
|------|------|------|
| POST /sessions/{id}/export/estimate | ✅ | 预估 token 数，远程模型提示 |
| POST /sessions/{id}/export | ✅ | SSE 流式生成 |
| Prompt 构建: 对话 + 模板 system_prompt + 语言指令 | ✅ | |
| 客户端断开连接时中断生成 | ✅ | GeneratorExit 处理 |
| 后端测试: 预估 API | ✅ | `test_export_api.py` |
| 后端测试: 导出 API (mock 模型) | ✅ | 11 tests |

#### 1.3 前端 - 导出 UI

| 项目 | 状态 | 说明 |
|------|------|------|
| Session 操作菜单添加 "导出知识库" 按钮 | ✅ | `SessionList.vue` |
| 导出 Modal: 模板选择 + 语言选择 | ✅ | `ExportModal.vue` |
| 预估 token 显示 + 远程模型费用提示 | ✅ | |
| 流式内容预览 + 取消按钮 | ✅ | |
| 生成完成后自动下载 .md 文件 | ✅ | `Blob` + `URL.createObjectURL` |
| 失败错误展示 + 重试按钮 | ✅ | |
| 前端 API: getExportTemplates, estimateExport, exportSession | ✅ | `api/export.ts` |

#### 1.4 前端 - 模板管理

| 项目 | 状态 | 说明 |
|------|------|------|
| Settings 页面添加 "导出模板" 区域 | ✅ | `SettingsView.vue` |
| 自定义模板创建/编辑/删除 UI | ✅ | 展开/折叠卡片 |
| 模板编辑器 (markdown 输入 + 占位符说明) | ✅ | `TemplateEditor.vue` |
| 提供模板示例帮助用户理解 | ✅ | Placeholder Reference 区域 |
| 前端 API: 模板 CRUD | ⬜ | `api/export.ts` |
| 前端测试: 模板管理组件 | ⬜ | |

### Priority 2 - 功能增强 🟡

| 项目 | 状态 | 说明 |
|------|------|------|
| API 版本重定向 `/api/` → `/api/v1/` | ✅ | `backend/main.py` |
| CORS 配置界面 | ✅ | `views/SettingsView.vue` CORS section |
| 用量统计展示 UI | ✅ | `components/UsageStats.vue` + `SettingsView.vue` |
| Chrome 插件接入文档 | ⬜ | `docs/chrome-extension.md` |

---

## Development Roadmap (TDD)

### Phase 1 - 知识库导出: 模板管理后端 🔴

**TDD 流程: 先写测试，再实现**

- [x] 测试: 创建 `test_export_templates_api.py`，编写模板 CRUD 测试 (20 tests)
- [x] 测试: 预置模板初始化测试
- [x] 实现: 数据库迁移 - `export_templates` 表
- [x] 实现: `ExportTemplateService` - CRUD + 初始化
- [x] 实现: `routers/export.py` - 模板 CRUD API
- [x] 实现: `main.py` - 路由注册 + 初始化
- [x] 验证: `python -m pytest backend/tests/api/test_export_templates_api.py -v`

### Phase 2 - 知识库导出: 导出生成后端 🔴

- [x] 测试: 创建 `test_export_api.py`，编写导出 API 测试 (mock 模型)
- [x] 测试: 预估 token API 测试
- [x] 测试: SSE 流式响应测试
- [x] 测试: 语言参数测试
- [x] 实现: `POST /sessions/{id}/export/estimate` - 预估
- [x] 实现: `POST /sessions/{id}/export` - SSE 流式生成
- [x] 实现: Prompt 构建 (对话 + 模板 + 语言)
- [x] 实现: 客户端断开中断处理
- [x] 验证: `python -m pytest backend/tests/api/test_export_api.py -v`

### Phase 3 - 知识库导出: 前端 UI 🟡

- [x] 实现: `api/export.ts` - 导出相关 API
- [x] 实现: `ExportModal.vue` - 模板选择 + 语言 + 预览
- [x] 实现: `SessionList.vue` - 添加导出按钮
- [x] 实现: 流式预览 + 取消 + 下载
- [x] 实现: 错误展示 + 重试
- [ ] 测试: `ExportModal.vue` 组件测试
- [x] 验证: `cd frontend && npm run test -- --run`
- [x] 验证: `cd frontend && npm run build`

### Phase 4 - 知识库导出: 模板管理前端 🟡

- [x] 实现: `TemplateEditor.vue` - 模板编辑器
- [x] 实现: `SettingsView.vue` - 模板管理区域
- [x] 实现: 模板示例展示 (Placeholder Reference)
- [ ] 测试: 模板管理组件测试
- [x] 验证: `cd frontend && npm run test -- --run`
- [x] 验证: `cd frontend && npm run build`

### Phase 5 - 功能增强 🟡

- [x] API 版本重定向 (`/api/` → `/api/v1/`)
- [x] CORS 配置界面 (SettingsView.vue CORS section with add/remove/save)
- [x] 用量统计 UI (UsageStats.vue component in SettingsView)
- [ ] Chrome 插件文档

---

## Key Files Reference

### Backend
```
backend/
├── main.py                    # FastAPI 入口, 路由注册, CORS, DB migration
├── database.py                # SQLite Database wrapper
├── mlx_instance.py            # MLX 单例管理
├── auth/
│   ├── api_key.py             # API Key 生成/验证 (SHA256)
│   └── dependencies.py        # FastAPI 认证依赖
├── routers/
│   ├── chat.py                # POST /api/v1/chat (SSE, TTFT, local/remote routing)
│   ├── sessions.py            # CRUD /api/v1/sessions + delete all
│   ├── models.py              # /api/v1/models (list/load/current)
│   ├── model_registry.py      # /api/v1/model-registry (local + remote)
│   ├── usage.py               # GET /api/v1/usage
│   ├── settings.py            # /api/v1/settings + /api-keys + /remote + /remote/providers
│   ├── openai.py              # /v1/chat/completions (OpenAI compat)
│   └── export.py              # /api/v1/export/templates + /sessions/{id}/export ⬜
├── services/
│   ├── mlx_service.py         # MLX model inference
│   ├── session_service.py     # Session CRUD + messages + duration + delete all
│   ├── usage_service.py       # Usage recording/query
│   ├── auth_service.py        # API Key management
│   ├── model_registry_service.py  # Model registry (local + remote + provider)
│   └── export_template_service.py # Export template CRUD ⬜
└── utils/
    └── model_detector.py      # Local model auto-detection
```

### Frontend
```
frontend/src/
├── api/
│   ├── auth.ts                # API Key localStorage 管理
│   ├── chat.ts                # streamingChat (SSE parse, TTFT, duration)
│   ├── sessions.ts            # Session CRUD + deleteAllSessions API
│   ├── models.ts              # Models API + addRemoteModel
│   ├── settings.ts            # Settings + API Keys + Usage + Remote + Validate API
│   └── export.ts              # Export templates + generate API ✅
├── stores/
│   ├── chat.ts                # Chat state (messages, isGenerating, tokenCount, duration)
│   ├── session.ts             # Session state + loadSessionMessages() + deleteAll
│   ├── models.ts              # Models state (models, loadedModelId, local/remote)
│   └── settings.ts            # Settings state (apiKeys, theme)
├── components/
│   ├── ChatArea.vue           # 消息列表 + 实时进度
│   ├── MessageBubble.vue      # 消息气泡 + duration badge + thought 解析 + Markdown
│   ├── InputArea.vue          # 输入框 + 发送按钮
│   ├── SessionList.vue        # 会话列表 + 新建/删除/重命名/清理全部/导出按钮
│   ├── ModelSelector.vue      # 模型下拉 (本地🖥️ + 远程☁️) + 加载状态
│   ├── ParameterPanel.vue     # 参数调节面板
│   ├── ApiKeyList.vue         # API Key 列表 + 创建/删除
│   ├── Modal.vue              # 通用模态框
│   ├── ExportModal.vue        # 导出知识库弹窗 (模板/语言选择) ✅
│   └── TemplateEditor.vue     # 自定义模板编辑器 ✅
└── views/
    ├── ChatView.vue           # 主界面 (sidebar + chat area)
    └── SettingsView.vue       # 设置页面 (API Key + Remote API + Templates + Theme)
```

---

## Test Structure

### Backend Tests (pytest)
```
backend/tests/
├── conftest.py              # Fixtures (db, API keys, services, remote_providers table)
├── unit/                    # Unit tests
│   ├── test_api_key.py
│   ├── test_auth_service.py
│   ├── test_mlx_service.py
│   ├── test_session_service.py
│   ├── test_database_migration.py
│   └── test_usage_service.py
├── api/                     # API tests
│   ├── test_chat_api.py
│   ├── test_chat_duration.py
│   ├── test_sessions_api.py         # 22 tests (含 delete all)
│   ├── test_models_api.py
│   ├── test_model_registry_api.py   # 16 tests (含 remote model)
│   ├── test_openai_api.py
│   ├── test_settings_api.py         # 21 tests (含 remote settings + validate)
│   ├── test_remote_model_e2e.py     # 9 tests (remote E2E)
│   ├── test_usage_api.py
│   ├── test_export_templates_api.py # ✅ 模板 CRUD 测试 (20 tests)
│   ├── test_export_api.py           # ✅ 导出生成测试 (11 tests)
│   └── test_e2e_api.py              # ✅ E2E API 测试 (16 tests)
└── integration/             # Integration tests (run separately)
    ├── test_http_api.py
    ├── test_mlx_direct.py
    └── test_mlx_chat.py
```

### Frontend Tests (Vitest)
```
frontend/src/
├── api/
│   ├── api.test.ts          # Sessions & Settings & Chat API (11 tests)
│   └── models.test.ts       # Models API (5 tests)
├── stores/
│   ├── chat.test.ts          # Chat store (9 tests)
│   ├── models.test.ts        # Models store (7 tests)
│   └── session.test.ts       # Session store (6 tests)
├── components/
│   ├── ParameterPanel.test.ts # ParameterPanel (15 tests)
│   └── e2e.test.ts            # ✅ ExportModal + TemplateEditor (26 tests)
```

---

## Running Tests

```bash
# Backend tests (must pass before any commit)
cd /path/to/mlx_chat
python -m pytest backend/tests/ --ignore=backend/tests/integration -v

# Frontend unit tests (must pass before any commit)
cd frontend
npm run test -- --run

# Frontend build
npm run build
```

---

## Local Models Registered

| Model | Params | Size |
|-------|--------|------|
| Qwen2.5-0.5B-Instruct | 0.5B | 289MB |
| Qwen2.5-7B-Instruct | 7B | 4GB |
| Qwen3.5-9B-MLX | 9B | 5.6GB |
| Qwen3.5-27B-Claude-Distilled | 27B | 14GB |

---

Last Updated: 2026-04-11 (Phase 5 功能增强: API 重定向、用量统计 UI、CORS 配置界面)
