# TDD Implementation Progress

## Project Overview

Apple Silicon MLX model chat API with OpenAI-compatible interface.

- **Backend**: FastAPI + aiosqlite + mlx-lm
- **Frontend**: Vue 3 + Vite + Pinia + TypeScript
- **Testing**: pytest (171 backend), Vitest (31 frontend), Playwright (14 E2E)

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
| Add message | ✅ | |
| Get messages | ✅ | |

### 4. Chat API

| Feature | Status | Tests |
|---------|--------|-------|
| POST /api/v1/chat | ✅ | `test_chat_api.py` (6) |
| SSE streaming response | ✅ | |
| Temperature parameter | ✅ | |
| Max tokens parameter | ✅ | |
| System prompt | ✅ | |

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

### 11. E2E Tests (Playwright)

| Feature | Status | Tests |
|---------|--------|-------|
| Health check | ✅ | ✅ `api.spec.ts` |
| Models API | ✅ | ✅ `api.spec.ts` |
| Sessions API | ✅ | ✅ `api.spec.ts` |
| OpenAI compatibility | ✅ | ✅ `api.spec.ts` |
| Auth validation | ✅ | ✅ `api.spec.ts` |
| Frontend page load | ✅ | ✅ `chat.spec.ts` |
| UI components | ✅ | ✅ `chat.spec.ts` |

> E2E tests: 7 API tests + 7 Frontend tests = 14 total

---

## Pending Features 🚧 (from PRD Analysis 2026-04-10)

> 以下基于 PRD (`MLX_Chat_Web_UI_PRD.md`) 与当前代码的全面对比得出。

### Priority 1 - 关键功能缺失 🔴

这些功能在 PRD 中明确要求，当前前后端均未完整实现。

#### 1.1 会话历史消息加载

| 项目 | 说明 |
|------|------|
| 问题 | 前端切换会话时只调用 `clearMessages()`，没有从 API 加载历史消息 |
| 期望 | 切换会话后调用 `GET /api/v1/sessions/{id}` 获取并渲染历史 messages |
| 涉及文件 | `stores/session.ts` (selectSession), `api/sessions.ts` (已有 getSession) |
| 优先级 | **高** |

#### 1.2 参数调节面板

| 项目 | 说明 |
|------|------|
| 问题 | 前端完全没有参数调节 UI |
| 期望 | PRD 2.1.4 要求: Temperature 滑块 (0.0-2.0), Max Tokens 输入框 (1-8192), System Prompt 文本框 |
| 涉及文件 | 新增 `components/ParameterPanel.vue`, `ChatView.vue` (折叠面板), 后端 `sessions.py` PATCH 接口已有支持 |
| 优先级 | **高** |

#### 1.3 参数随会话保存

| 项目 | 说明 |
|------|------|
| 问题 | 参数调节后没有持久化到 session |
| 期望 | 调节参数后保存到 session 的 temperature/max_tokens/system_prompt 字段，切换会话自动恢复 |
| 涉及文件 | `stores/session.ts`, `api/sessions.ts`, `ParameterPanel.vue` |
| 优先级 | **高** |

#### 1.4 用量统计展示

| 项目 | 说明 |
|------|------|
| 问题 | 后端 API 完整 (`/api/v1/usage`)，但前端 Settings 页面没有用量展示 |
| 期望 | 在 Settings 页面展示: 请求次数、输入 Token 数、输出 Token 数、总耗时 |
| 涉及文件 | `views/SettingsView.vue`, `components/UsageStats.vue`(新增), `api/settings.ts` (已有 getUsage) |
| 优先级 | **中** |

### Priority 2 - 功能增强 🟡

#### 2.1 实时生成进度 (Token 计数)

| 项目 | 说明 |
|------|------|
| 问题 | `stores/chat.ts` 中 `tokenCount` 已计数但未在 UI 展示 |
| 期望 | PRD 2.1.1 要求实时显示已生成 token 数 |
| 涉及文件 | `components/ChatArea.vue` 或 `components/MessageBubble.vue` |
| 优先级 | **中** |

#### 2.2 API 版本重定向

| 项目 | 说明 |
|------|------|
| 问题 | PRD 2.2.2 要求 `/api/` 重定向到 `/api/v1/`，当前未实现 |
| 期望 | 在 `main.py` 中添加重定向路由 |
| 涉及文件 | `backend/main.py` |
| 优先级 | **中** |

#### 2.3 CORS 配置界面

| 项目 | 说明 |
|------|------|
| 问题 | PRD 2.4.2 要求在设置页面配置 CORS 允许域名，前端缺少 UI |
| 期望 | Settings 页面增加 CORS 白名单编辑组件，调用 `PATCH /api/v1/settings` |
| 涉及文件 | `views/SettingsView.vue`, 新增 `components/CorsConfig.vue` |
| 优先级 | **中** |

#### 2.4 Chrome 插件接入文档

| 项目 | 说明 |
|------|------|
| 问题 | PRD 第 9 章预留的插件文档未编写 |
| 期望 | 提供插件接入指南: PluginConfig 接口、API 兼容性说明 |
| 涉及文件 | `README.md` 或新增 `docs/chrome-extension.md` |
| 优先级 | **低** |

---

## Development Roadmap (开发路线)

按优先级排序的 TODO 列表，供后续 TDD 开发使用:

### TODO 1 - 会话历史加载 🔴
- [ ] 后端: 编写 session 带 messages 返回的测试
- [ ] 前端: 编写 selectSession 加载历史消息的 store 测试
- [ ] 前端: `stores/session.ts` - selectSession 调用 `getSession()` 并恢复 messages
- [ ] 前端: `stores/chat.ts` - 新增 `loadMessages()` action
- [ ] 前端: `components/SessionList.vue` - 确认选择后触发加载
- [ ] E2E: 编写切换会话后历史消息可见的测试

### TODO 2 - 参数调节面板 🔴
- [ ] 后端: 确认 `PATCH /api/v1/sessions/{id}` 参数保存测试覆盖
- [ ] 前端: 新增 `components/ParameterPanel.vue`
- [ ] 前端: Temperature 滑块 (0.0-2.0, step 0.1, default 0.7)
- [ ] 前端: Max Tokens 输入框 (1-8192, default 4096)
- [ ] 前端: System Prompt 文本框
- [ ] 前端: `views/ChatView.vue` - 集成折叠面板
- [ ] 前端: 参数变更后调用 `PATCH /api/v1/sessions/{id}` 保存
- [ ] E2E: 参数调节并发送消息验证参数生效

### TODO 3 - 参数会话持久化 🔴
- [ ] 前端: ParameterPanel 监听 session 切换，加载对应参数值
- [ ] 前端: 发送消息时从当前 session 读取参数传给 chat API
- [ ] 前端: 参数变更自动保存 (debounce)
- [ ] E2E: 验证切换会话后参数恢复

### TODO 4 - 用量统计展示 🟡
- [ ] 前端: 新增 `components/UsageStats.vue`
- [ ] 前端: 调用 `api/settings.ts` 的 `getUsage()`
- [ ] 前端: `views/SettingsView.vue` 集成 UsageStats 组件
- [ ] 前端: 显示请求次数、input/output tokens、总耗时

### TODO 5 - 实时 Token 计数 🟡
- [ ] 前端: `components/ChatArea.vue` - 在生成中显示 token 计数
- [ ] 前端: `components/MessageBubble.vue` - 可选显示 token 数

### TODO 6 - API 版本重定向 🟡
- [ ] 后端: `main.py` - 添加 `/api/` -> `/api/v1/` 重定向
- [ ] 后端: 编写重定向测试

### TODO 7 - CORS 配置界面 🟡
- [ ] 前端: 新增 `components/CorsConfig.vue`
- [ ] 前端: `views/SettingsView.vue` 集成 CORS 配置

### TODO 8 - Chrome 插件文档 🟢
- [ ] 编写插件接入指南文档

---

## Key Files Reference

### Backend
```
backend/
├── main.py                    # FastAPI 入口, 路由注册, CORS
├── database.py                # SQLite Database wrapper
├── mlx_instance.py            # MLX 单例管理
├── auth/
│   ├── api_key.py             # API Key 生成/验证 (SHA256)
│   └── dependencies.py        # FastAPI 认证依赖
├── routers/
│   ├── chat.py                # POST /api/v1/chat (SSE streaming)
│   ├── sessions.py            # CRUD /api/v1/sessions
│   ├── models.py              # /api/v1/models (list/load/current)
│   ├── model_registry.py      # /api/v1/model-registry
│   ├── usage.py               # GET /api/v1/usage
│   ├── settings.py            # /api/v1/settings + /api-keys
│   └── openai.py              # /v1/chat/completions (OpenAI compat)
├── services/
│   ├── mlx_service.py         # MLX model inference
│   ├── session_service.py     # Session CRUD + messages
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
│   ├── chat.ts                # streamingChat + streamingChatCompletions
│   ├── sessions.ts            # Session CRUD API
│   ├── models.ts              # Models API
│   └── settings.ts            # Settings + API Keys + Usage API
├── stores/
│   ├── chat.ts                # Chat state (messages, isGenerating, tokenCount)
│   ├── session.ts             # Session state (sessions, currentSessionId)
│   ├── models.ts              # Models state (models, loadedModelId)
│   └── settings.ts            # Settings state (apiKeys, theme)
├── components/
│   ├── ChatArea.vue           # 消息列表 + 空状态
│   ├── MessageBubble.vue      # 消息气泡 + thought 解析
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
├── unit/                    # Unit tests (91 tests)
│   ├── test_api_key.py
│   ├── test_auth_service.py
│   ├── test_mlx_service.py
│   ├── test_session_service.py
│   └── test_usage_service.py
├── api/                     # API tests (80 tests)
│   ├── test_chat_api.py
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
│   ├── api.test.ts          # Sessions & Settings API (10 tests)
│   └── models.test.ts       # Models API (5 tests)
└── stores/
    ├── chat.test.ts          # Chat store (9 tests)
    ├── models.test.ts        # Models store (7 tests)
    └── chat.test.ts
```

### E2E Tests (Playwright)
```
frontend/tests/e2e/
├── chat.spec.ts             # UI E2E tests (8 tests)
└── api.spec.ts              # Backend API E2E (7 tests)
```

---

## Running Tests

```bash
# Backend tests (must pass before any commit)
cd /path/to/mlx_chat
python -m pytest backend/tests/ -v

# Frontend unit tests (must pass before any commit)
cd frontend
npm run test

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

Last Updated: 2026-04-10
