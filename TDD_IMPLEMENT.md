# TDD Implementation Progress

## Project Overview

Apple Silicon MLX model chat API with OpenAI-compatible interface.

- **Backend**: FastAPI + aiosqlite + mlx-lm
- **Frontend**: Vue 3 + Vite + Pinia + TypeScript
- **Testing**: pytest (177 backend), Vitest (32 frontend), Playwright (14 E2E)

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
| List registered models | ✅ | `test_model_registry_api.py` (11) |
| Add new model | ✅ | |
| Get model detail | ✅ | |
| Update model info | ✅ | |
| Soft delete model | ✅ | |
| Validate model ID format | ✅ | |
| Load model from registry | ✅ | |
| Auto-detect local MLX models | ✅ | |

### 7. Usage Tracking (Backend API)

| Feature | Status | Tests |
|---------|--------|-------|
| Record usage | ✅ | `test_usage_service.py` (14) |
| Get usage summary | ✅ | |
| Period filtering | ✅ | |
| API key isolation | ✅ | |
| Recent logs query | ✅ | |

### 8. Settings & API Key Management (Backend API)

| Feature | Status | Tests |
|---------|--------|-------|
| Get/Update settings | ✅ | `test_settings_api.py` (13) |
| List API keys | ✅ | |
| Create API key | ✅ | |
| Delete API key | ✅ | |
| Key prefix display | ✅ | |

### 9. Integration Tests

| Feature | Status | Tests |
|---------|--------|-------|
| Real MLX model loading | ✅ | `integration/` (3) |
| HTTP API chat test | ✅ | |
| Stream/non-stream response | ✅ | |

### 10. Frontend (Vue 3)

| Feature | Status | Tests |
|---------|--------|-------|
| Project setup (Vite + Vue 3 + TypeScript) | ✅ | ✅ `api.test.ts` |
| Chat UI component | ✅ | ✅ `chat.test.ts` |
| Session list sidebar (create/delete/rename) | ✅ | ✅ `session.ts` store |
| Model selector dropdown + loading state | ✅ | ✅ `models.test.ts` |
| SSE stream rendering | ✅ | ✅ `chat.test.ts` |
| Pinia store for state management | ✅ | ✅ 3 store tests |
| API Key input modal | ✅ | ✅ `api.test.ts` |
| Models API & Store | ✅ | ✅ `models.test.ts` |
| Settings page (API Key list) | ✅ | `ApiKeyList.vue` |
| Dark/Light theme toggle | ✅ | `settings.ts` |
| **会话历史消息加载** | ✅ | `session.ts` - `loadSessionMessages()` |
| **实时生成进度 (token 计数、速度)** | ✅ | `ChatArea.vue`, `MessageBubble.vue` |
| **生成耗时显示 (duration, TTFT)** | ✅ | `MessageBubble.vue` - duration badge |
| **消息 Markdown 渲染** | ✅ | `MessageBubble.vue` - marked.js |
| **Thinking process 折叠显示** | ✅ | `MessageBubble.vue` - thought 解析 |

### 11. E2E Tests (Playwright)

#### E2E 测试文件
```
tests/e2e/
├── api.spec.ts              # 后端 API E2E (7 tests)
├── chat.spec.ts             # 前端基础 UI E2E (7 tests)
├── chat-flow.spec.ts        # 对话流程 + 模型选择 E2E (5 tests)
├── prd-compliance.spec.ts   # PRD 合规测试 (16 tests, 9 skipped)
└── api-key.spec.ts          # API Key 流程 E2E (9 tests)

frontend/tests/e2e/
└── api-key.spec.ts          # API Key 流程 (16 tests, 与上方部分重复)
```

#### E2E 覆盖率分析 (PRD 逐条对照)

| PRD 章节 | 功能点 | 后端路由 | E2E 状态 | 说明 |
|----------|--------|----------|----------|------|
| 2.1.1 | 模型对话/流式输出 | POST /api/v1/chat | ✅ | chat-flow.spec.ts |
| 2.1.1 | 实时 token 计数 | - | ✅ | chat-flow.spec.ts (streaming) |
| 2.1.2 | 创建会话 | POST /sessions | ✅ | api.spec.ts, chat-flow.spec.ts |
| 2.1.2 | 切换会话 | - | ✅ | prd-compliance.spec.ts |
| 2.1.2 | 删除会话 | DELETE /sessions/{id} | ✅ | prd-compliance.spec.ts |
| 2.1.2 | 会话历史保存 | GET /sessions/{id} | ✅ | prd-compliance.spec.ts |
| 2.1.3 | 模型列表展示 | GET /api/v1/models | ✅ | api.spec.ts |
| 2.1.3 | 切换模型 | POST /api/v1/models/load | ❌ | 缺失 E2E |
| 2.1.3 | 加载状态显示 | - | ✅ | prd-compliance.spec.ts |
| 2.1.4 | Temperature 调节 | PATCH /sessions/{id} | ❌ | 待实现 |
| 2.1.4 | Max Tokens 调节 | PATCH /sessions/{id} | ❌ | 待实现 |
| 2.1.4 | System Prompt | PATCH /sessions/{id} | ❌ | 待实现 |
| 2.1.4 | 参数随会话保存 | - | ❌ | 待实现 |
| 2.2.1 | API Key 生成 | POST /settings/api-keys | ❌ | 缺失 E2E |
| 2.2.1 | API Key 删除 | DELETE /settings/api-keys/{id} | ❌ | 缺失 E2E |
| 2.2.1 | API Key 列表 | GET /settings/api-keys | ❌ | 缺失 E2E |
| 2.2.2 | /api/v1/ 前缀 | - | ✅ | prd-compliance.spec.ts |
| 2.2.2 | /api/ → /api/v1/ 重定向 | - | ✅ | prd-compliance.spec.ts |
| 2.2.4 | 用量统计 API | GET /usage | ✅ | prd-compliance.spec.ts |
| 2.2.4 | 按时段查询 | GET /usage?period= | ✅ | prd-compliance.spec.ts |
| 2.3.1 | OpenAI 兼容格式 | POST /v1/chat/completions | ✅ | api.spec.ts |
| 2.3.1 | OpenAI 非流式 | POST /v1/chat/completions (stream=false) | ❌ | 缺失 E2E |
| 2.3.1 | OpenAI 流式 | POST /v1/chat/completions (stream=true) | ❌ | 缺失 E2E |
| 2.4.1 | 侧边栏会话列表 | - | ✅ | chat.spec.ts |
| 2.4.1 | 聊天消息区域 | - | ✅ | chat.spec.ts |
| 2.4.1 | 输入区域 | - | ✅ | chat.spec.ts |
| 2.4.1 | 模型选择器 | - | ✅ | chat-flow.spec.ts |
| 2.4.2 | Settings 页面加载 | - | ❌ | 缺失 E2E |
| 2.4.2 | API Key 管理 UI | - | ❌ | 缺失 E2E |
| 2.4.2 | 用量统计展示 UI | - | ❌ | 待实现 |
| 2.4.2 | CORS 配置 UI | - | ❌ | 待实现 |
| 2.4.3 | 深色主题 | - | ✅ | settings.ts store |
| 2.4.3 | 浅色主题 | - | ✅ | settings.ts store |
| - | Health 检查 | GET /health | ✅ | api.spec.ts |
| - | 未授权访问拦截 | - | ✅ | api.spec.ts |
| - | 会话重命名 | PATCH /sessions/{id} | ❌ | 缺失 E2E |
| - | 历史消息加载 (UI) | GET /sessions/{id} | ✅ | session store |
| - | duration_ms 显示 | - | ✅ | MessageBubble.vue |
| - | TTFT 显示 | - | ✅ | MessageBubble.vue |

#### 缺失 E2E 测试汇总

**后端 API E2E 缺失 (需要真实 MLX 模型或 mock)**:
| 缺失测试 | 优先级 | 原因 |
|----------|--------|------|
| POST /api/v1/models/load | 🟡 | 需要 MLX mock 或真实模型 |
| GET /api/v1/models/current | 🟡 | 同上 |
| GET /api/v1/settings | 🟡 | 简单 API，可直接测 |
| PATCH /api/v1/settings | 🟡 | 同上 |
| POST /api/v1/settings/api-keys | 🟡 | 创建 key 流程 |
| DELETE /api/v1/settings/api-keys/{id} | 🟡 | 删除 key 流程 |
| GET /api/v1/settings/api-keys | 🟡 | 列出 keys |
| PATCH /sessions/{id} (rename) | 🟡 | 更新会话 |
| POST /v1/chat/completions non-stream | 🟡 | 需要 MLX mock |
| POST /v1/chat/completions stream | 🟡 | 需要 MLX mock |

**前端 UI E2E 缺失**:
| 缺失测试 | 优先级 | 原因 |
|----------|--------|------|
| Settings 页面 /settings 加载 | 🟡 | Vue router |
| Settings API Key 列表展示 | 🟡 | ApiKeyList 组件 |
| Settings 创建 API Key | 🟡 | ApiKeyList 组件 |
| Settings 删除 API Key | 🟡 | ApiKeyList 组件 |
| 会话重命名 (UI) | 🟡 | SessionList rename |
| 会话详情 + 历史消息加载 | 🟡 | 已有后端测试，前端需 E2E |
| 参数调节面板 | 🔴 | 待实现 ParameterPanel |
| 参数持久化到会话 | 🔴 | 待实现 |
| 用量统计展示 | 🟡 | 待实现 UsageStats |

> 当前 E2E 总计约 **50+ tests** (含重复)，实际独立场景约 **35 个**，PRD 共 **37 个功能点**，覆盖率约 **~65%**。

---

## Pending Features 🚧 (from PRD Analysis 2026-04-10)

> 以下基于 PRD (`MLX_Chat_Web_UI_PRD.md`) 与当前代码的全面对比得出。

### Priority 1 - 关键功能缺失 🔴

#### 1.1 参数调节面板

| 项目 | 说明 |
|------|------|
| 状态 | ❌ 未实现 |
| 期望 | PRD 2.1.4 要求: Temperature 滑块 (0.0-2.0), Max Tokens 输入框 (1-8192), System Prompt 文本框 |
| 后端 | ✅ `PATCH /api/v1/sessions/{id}` 已支持 |
| 前端 | ❌ 缺少 `components/ParameterPanel.vue` |
| 优先级 | **高** |

#### 1.2 参数随会话保存

| 项目 | 说明 |
|------|------|
| 状态 | ❌ 未实现 |
| 期望 | 调节参数后保存到 session 的 temperature/max_tokens/system_prompt 字段，切换会话自动恢复 |
| 涉及文件 | `stores/session.ts`, `api/sessions.ts`, `ParameterPanel.vue` |
| 优先级 | **高** |

#### 1.3 用量统计展示

| 项目 | 说明 |
|------|------|
| 状态 | ❌ 前端未实现 |
| 后端 | ✅ `/api/v1/usage` 完整 |
| 期望 | Settings 页面展示: 请求次数、输入 Token 数、输出 Token 数、总耗时 |
| 涉及文件 | `views/SettingsView.vue`, 新增 `components/UsageStats.vue` |
| 优先级 | **中** |

### Priority 2 - 功能增强 🟡

#### 2.1 API 版本重定向

| 项目 | 说明 |
|------|------|
| 状态 | ❌ 未实现 |
| 期望 | PRD 2.2.2 要求 `/api/` 重定向到 `/api/v1/`，保留旧版本兼容性 |
| 涉及文件 | `backend/main.py` |
| 优先级 | **中** |

#### 2.2 CORS 配置界面

| 项目 | 说明 |
|------|------|
| 状态 | ❌ 前端未实现 |
| 后端 | ✅ `PATCH /api/v1/settings` 已支持 |
| 期望 | Settings 页面增加 CORS 白名单编辑组件 |
| 涉及文件 | `views/SettingsView.vue`, 新增 `components/CorsConfig.vue` |
| 优先级 | **中** |

#### 2.3 Chrome 插件接入文档

| 项目 | 说明 |
|------|------|
| 状态 | ❌ 未编写 |
| 期望 | PRD 第 9 章预留的插件接入指南: PluginConfig 接口、API 兼容性说明 |
| 涉及文件 | `README.md` 或新增 `docs/chrome-extension.md` |
| 优先级 | **低** |

---

## Development Roadmap (开发路线)

按优先级排序的 TODO 列表，供后续 TDD 开发使用:

### TODO 1 - 参数调节面板 🔴
- [ ] 前端: 新增 `components/ParameterPanel.vue`
- [ ] 前端: Temperature 滑块 (0.0-2.0, step 0.1, default 0.7)
- [ ] 前端: Max Tokens 输入框 (1-8192, default 4096)
- [ ] 前端: System Prompt 文本框 (多行)
- [ ] 前端: `views/ChatView.vue` - 集成折叠面板
- [ ] 前端: 编写 ParameterPanel 组件测试
- [ ] E2E: 参数调节并发送消息验证参数生效

### TODO 2 - 参数会话持久化 🔴
- [ ] 前端: ParameterPanel 监听 session 切换，加载对应参数值
- [ ] 前端: 发送消息时从当前 session 读取参数传给 chat API
- [ ] 前端: 参数变更自动保存 (debounce 500ms)
- [ ] 前端: 编写参数持久化测试
- [ ] E2E: 验证切换会话后参数恢复

### TODO 3 - 用量统计展示 🟡
- [ ] 前端: 新增 `components/UsageStats.vue`
- [ ] 前端: 调用 `api/settings.ts` 的 `getUsage()`
- [ ] 前端: `views/SettingsView.vue` 集成 UsageStats 组件
- [ ] 前端: 显示请求次数、input/output tokens、总耗时
- [ ] 前端: 编写 UsageStats 组件测试

### TODO 4 - API 版本重定向 🟡
- [ ] 后端: `main.py` - 添加 `/api/` -> `/api/v1/` 重定向
- [ ] 后端: 编写重定向测试

### TODO 5 - CORS 配置界面 🟡
- [ ] 前端: 新增 `components/CorsConfig.vue`
- [ ] 前端: `views/SettingsView.vue` 集成 CORS 配置
- [ ] 前端: 编写 CorsConfig 组件测试

### TODO 6 - Chrome 插件文档 🟢
- [ ] 编写插件接入指南文档
- [ ] 包含 PluginConfig 接口定义
- [ ] 包含 API 兼容性说明

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
│   ├── chat.py                # POST /api/v1/chat (SSE, TTFT, duration)
│   ├── sessions.py            # CRUD /api/v1/sessions
│   ├── models.py              # /api/v1/models (list/load/current)
│   ├── model_registry.py      # /api/v1/model-registry
│   ├── usage.py               # GET /api/v1/usage
│   ├── settings.py            # /api/v1/settings + /api-keys
│   └── openai.py              # /v1/chat/completions (OpenAI compat)
├── services/
│   ├── mlx_service.py         # MLX model inference
│   ├── session_service.py     # Session CRUD + messages + duration
│   ├── usage_service.py       # Usage recording/query
│   ├── auth_service.py        # API Key management
│   └── model_registry_service.py
└── utils/
    └── model_detector.py      # Local model auto-detection
```

### Frontend
```
frontend/src/
├── api/
│   ├── auth.ts                # API Key localStorage 管理
│   ├── chat.ts                # streamingChat (SSE parse, TTFT, duration)
│   ├── sessions.ts            # Session CRUD API
│   ├── models.ts              # Models API
│   └── settings.ts            # Settings + API Keys + Usage API
├── stores/
│   ├── chat.ts                # Chat state (messages, isGenerating, tokenCount, duration)
│   ├── session.ts             # Session state + loadSessionMessages()
│   ├── models.ts              # Models state (models, loadedModelId)
│   └── settings.ts            # Settings state (apiKeys, theme)
├── components/
│   ├── ChatArea.vue           # 消息列表 + 实时进度
│   ├── MessageBubble.vue      # 消息气泡 + duration badge + thought 解析 + Markdown
│   ├── InputArea.vue          # 输入框 + 发送按钮
│   ├── SessionList.vue        # 会话列表 + 新建/删除/重命名
│   ├── ModelSelector.vue      # 模型下拉 + 加载状态
│   ├── ApiKeyList.vue         # API Key 列表 + 创建/删除
│   └── Modal.vue              # 通用模态框
└── views/
    ├── ChatView.vue           # 主界面 (sidebar + chat area)
    └── SettingsView.vue       # 设置页面 (API Key + Theme)
```

---

## Test Structure

### Backend Tests (pytest)
```
backend/tests/
├── conftest.py              # Fixtures (db, API keys, services)
├── unit/                    # Unit tests
│   ├── test_api_key.py
│   ├── test_auth_service.py
│   ├── test_mlx_service.py
│   ├── test_session_service.py
│   ├── test_database_migration.py
│   └── test_usage_service.py
├── api/                     # API tests
│   ├── test_chat_api.py
│   ├── test_chat_duration.py    # Duration + TTFT tests
│   ├── test_sessions_api.py
│   ├── test_models_api.py
│   ├── test_model_registry_api.py
│   ├── test_openai_api.py
│   ├── test_settings_api.py
│   └── test_usage_api.py
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
└── stores/
    ├── chat.test.ts          # Chat store (9 tests)
    └── models.test.ts        # Models store (7 tests)
```

### E2E Tests (Playwright)
```
tests/e2e/
├── api.spec.ts              # Backend API E2E (7 tests)
├── chat.spec.ts             # Frontend page load E2E (7 tests)
├── chat-flow.spec.ts        # Chat flow + model selector (5 tests)
├── prd-compliance.spec.ts   # PRD compliance (16 tests, 9 skipped)
└── api-key.spec.ts          # API Key flow (9 tests)

frontend/tests/e2e/
└── api-key.spec.ts          # API Key flow (16 tests, duplicate)
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

# E2E tests (requires backend and frontend running)
# Terminal 1: Start backend
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000

# Terminal 2: Start frontend
cd frontend && npm run dev

# Terminal 3: Run E2E tests
npm run test:e2e
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

Last Updated: 2026-04-10 (E2E coverage analysis added)
