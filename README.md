# MLX Chat API

Apple Silicon MLX 模型对话 API，支持 Web UI 和 Chrome 插件扩展。

## 功能特性

- **OpenAI 兼容接口** - `/v1/chat/completions` 端点，支持 Chrome 插件等第三方客户端
- **流式响应** - SSE (Server-Sent Events) 实时输出
- **多会话管理** - 会话 CRUD、消息历史
- **模型切换** - 动态加载/卸载 MLX 模型
- **API Key 认证** - 安全的访问控制
- **用量统计** - Token 使用记录

## 项目结构

```
mlx_chat/
├── backend/                  # FastAPI 后端
│   ├── main.py              # 应用入口
│   ├── database.py          # 数据库辅助类
│   ├── mlx_instance.py      # MLX 服务单例
│   ├── auth/
│   │   ├── api_key.py       # API Key 生成/验证
│   │   └── dependencies.py  # FastAPI 依赖注入
│   ├── routers/
│   │   ├── openai.py        # OpenAI 兼容接口
│   │   ├── chat.py          # 内部聊天接口
│   │   ├── sessions.py      # 会话管理
│   │   ├── models.py        # 模型管理
│   │   ├── settings.py      # 设置管理
│   │   └── usage.py         # 用量统计
│   ├── services/
│   │   ├── mlx_service.py   # MLX 模型服务
│   │   ├── session_service.py
│   │   ├── auth_service.py
│   │   └── usage_service.py
│   └── tests/
│       ├── conftest.py      # pytest fixtures
│       ├── unit/            # 单元测试
│       ├── api/             # API 测试
│       └── integration/     # 集成测试
├── frontend/                 # Vue 3 前端
│   ├── src/
│   │   ├── views/           # 页面视图
│   │   ├── components/     # Vue 组件
│   │   ├── stores/         # Pinia 状态管理
│   │   └── api/             # API 调用
│   ├── package.json
│   └── vite.config.ts
└── data/                    # 数据目录 (SQLite DB)
```

## 快速开始

### 1. 安装依赖

```bash
# 克隆项目
cd mlx_chat

# 创建虚拟环境 (推荐)
python -m venv mlx-env
source mlx-env/bin/activate  # Linux/Mac
# 或 mlx-env\Scripts\activate  # Windows

# 安装依赖
pip install fastapi uvicorn aiosqlite mlx-lm pytest pytest-asyncio httpx
```

### 2. 启动服务

```bash
cd backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

服务启动后访问:
- API 文档: http://localhost:8000/docs
- 健康检查: http://localhost:8000/health

### 3. 创建 API Key

服务启动时会自动检测本地 HuggingFace 缓存中的 MLX 模型，并自动注册。

```bash
cd backend
python init_db.py
```

运行后会:
1. 自动检测 `~/.cache/huggingface/hub/` 中的 MLX 模型
2. 将检测到的模型注册到数据库
3. 创建 API Key

**手动检测模型:**

```bash
python -c "from backend.utils.model_detector import print_local_models; print_local_models()"
```

### 4. 加载模型

服务启动后会自动初始化默认的 MLX 模型列表。

**查看可用模型:**

```bash
curl http://localhost:8000/api/v1/models \
  -H "Authorization: Bearer YOUR_API_KEY"
```

**加载模型:**

```bash
curl -X POST http://localhost:8000/api/v1/models/load \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model": "mlx-community/Qwen2.5-0.5B-Instruct-4bit"}'
```

**已注册模型列表:**

| 模型 | 参数量 | 说明 |
|------|--------|------|
| Qwen2.5-0.5B-Instruct | 0.5B | 轻量级对话模型，适合测试 |
| Qwen2.5-7B-Instruct | 7B | 平衡性能与质量 |
| Qwen3.5-9B-MLX | 9B | Qwen3.5 系列 |
| Qwen3.5-27B-Claude-Distilled | 27B | Claude 蒸馏版大模型 |

**查看已注册模型:**

```bash
curl http://localhost:8000/api/v1/models \
  -H "Authorization: Bearer YOUR_API_KEY"
```

响应示例:

```json
[
  {
    "name": "Qwen2.5-7B-Instruct",
    "model_id": "mlx-community/Qwen2.5-7B-Instruct-4bit",
    "params_count": "7B",
    "is_loaded": false
  }
]
```

**加载模型:**

```bash
curl -X POST http://localhost:8000/api/v1/models/load \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model": "Qwen2.5-7B-Instruct"}'
```

**添加新模型:**

```bash
# 添加自定义 MLX 模型 (model_id 需要符合 HuggingFace 格式)
curl -X POST http://localhost:8000/api/v1/model-registry \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Custom Model",
    "model_id": "mlx-community/my-model-4bit",
    "description": "自定义模型描述",
    "params_count": "7B",
    "quantization": "4bit"
  }'
```

## API 使用示例

### OpenAI 兼容接口

**非流式请求:**

```bash
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "mlx-community/Qwen2.5-0.5B-Instruct-4bit",
    "messages": [
      {"role": "user", "content": "你好，介绍一下你自己"}
    ],
    "temperature": 0.7,
    "max_tokens": 100,
    "stream": false
  }'
```

**响应示例:**

```json
{
  "id": "chatcmpl-abc123",
  "object": "chat.completion",
  "created": 1704067200,
  "model": "mlx-community/Qwen2.5-0.5B-Instruct-4bit",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "你好！我是一个AI助手..."
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 10,
    "completion_tokens": 50,
    "total_tokens": 60
  }
}
```

**流式请求:**

```bash
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "mlx-community/Qwen2.5-0.5B-Instruct-4bit",
    "messages": [
      {"role": "user", "content": "写一首关于春天的诗"}
    ],
    "temperature": 0.7,
    "max_tokens": 200,
    "stream": true
  }'
```

**流式响应格式 (SSE):**

```
data: {"id":"chatcmpl-...","object":"chat.completion.chunk","choices":[{"delta":{"role":"assistant"}}]}
data: {"id":"chatcmpl-...","object":"chat.completion.chunk","choices":[{"delta":{"content":"春"}}]}
data: {"id":"chatcmpl-...","object":"chat.completion.chunk","choices":[{"delta":{"content":"风"}}]}
...
data: [DONE]
```

### 会话管理

**创建会话:**

```bash
curl -X POST http://localhost:8000/api/v1/sessions \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "我的对话",
    "model": "mlx-community/Qwen2.5-0.5B-Instruct-4bit",
    "system_prompt": "你是一个友好的助手"
  }'
```

**获取会话列表:**

```bash
curl http://localhost:8000/api/v1/sessions \
  -H "Authorization: Bearer YOUR_API_KEY"
```

**获取会话详情 (含消息历史):**

```bash
curl http://localhost:8000/api/v1/sessions/SESSION_ID \
  -H "Authorization: Bearer YOUR_API_KEY"
```

### 用量统计

```bash
curl http://localhost:8000/api/v1/usage \
  -H "Authorization: Bearer YOUR_API_KEY"

# 指定月份查询
curl "http://localhost:8000/api/v1/usage?period=2026-04" \
  -H "Authorization: Bearer YOUR_API_KEY"
```

## Chrome 插件接入

Chrome 插件可以直接使用 OpenAI 兼容接口:

```javascript
// 在插件中配置
const API_BASE = "http://localhost:8000/v1";
const API_KEY = "YOUR_API_KEY";

// 发送请求
fetch(`${API_BASE}/chat/completions`, {
  method: "POST",
  headers: {
    "Authorization": `Bearer ${API_KEY}`,
    "Content-Type": "application/json"
  },
  body: JSON.stringify({
    model: "mlx-community/Qwen2.5-0.5B-Instruct-4bit",
    messages: [{ role: "user", content: "Hello" }],
    stream: false
  })
});
```

## 前端开发

前端使用 Vue 3 + Vite + Pinia + TypeScript。

### 安装依赖

```bash
cd frontend
npm install
```

### 启动开发服务器

```bash
# 先启动后端 (在另一个终端)
cd backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# 启动前端
cd frontend
npm run dev
```

访问 http://localhost:3000

### 构建生产版本

```bash
cd frontend
npm run build
```

### 功能特性

- **会话管理** - 创建、切换、删除对话会话
- **模型选择** - 下拉菜单选择已注册的 MLX 模型
- **流式输出** - SSE 实时显示 AI 响应
- **API Key 管理** - 首次使用时输入 API Key

## 运行测试

```bash
cd backend

# 单元测试
python -m pytest tests/unit/ -v

# API 测试
python -m pytest tests/api/ -v

# 所有测试
python -m pytest tests/ -v

# 集成测试 (需要加载真实模型)
python tests/integration/test_http_api.py
```

## API 端点总览

| 端点 | 方法 | 说明 |
|------|------|------|
| `/health` | GET | 健康检查 |
| `/v1/models` | GET | 列出模型 (OpenAI 兼容) |
| `/v1/chat/completions` | POST | 聊天补全 (OpenAI 兼容) |
| `/api/v1/models` | GET | 获取模型列表 |
| `/api/v1/models/load` | POST | 加载模型 |
| `/api/v1/models/current` | GET | 当前模型状态 |
| `/api/v1/sessions` | GET/POST | 会话列表/创建 |
| `/api/v1/sessions/{id}` | GET/PATCH/DELETE | 会话详情/更新/删除 |
| `/api/v1/chat` | POST | 内部聊天接口 |
| `/api/v1/settings` | GET/PATCH | 应用设置 |
| `/api/v1/settings/api-keys` | GET/POST/DELETE | API Key 管理 |
| `/api/v1/usage` | GET | 用量统计 |
| `/api/v1/model-registry` | GET | 获取模型列表 |
| `/api/v1/model-registry` | POST | 添加新模型 |
| `/api/v1/model-registry/{id}` | GET/PATCH/DELETE | 模型详情/更新/删除 |

## 常见问题

**Q: 模型加载失败?**

确保已安装 `mlx-lm` 并有足够的内存:
```bash
pip install mlx-lm
```

**Q: 请求返回 401?**

检查 Authorization header 格式:
```
Authorization: Bearer sk-xxxx...
```

**Q: 流式响应中断?**

确保客户端支持 SSE 并正确处理 `data:` 格式。

## 许可证

MIT License