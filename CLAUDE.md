# CLAUDE.md - MLX Chat Project Guide

## Project Overview

Apple Silicon MLX model chat API with OpenAI-compatible interface, supporting Chrome plugin extensions.

## Tech Stack

- **Backend**: FastAPI + aiosqlite + mlx-lm
- **Frontend**: Vue 3 + Vite + Pinia + TypeScript
- **Testing**: pytest + pytest-asyncio + httpx (backend), Vitest (frontend)

## Key Patterns

### 1. Database Access

```python
# Always use Database wrapper class
from backend.database import Database

conn = await aiosqlite.connect('path/to.db')
conn.row_factory = aiosqlite.Row
db = Database(conn)

# Use helper methods (never return raw cursors)
row = await db.fetchone("SELECT * FROM table WHERE id = ?", (id,))
rows = await db.fetchall("SELECT * FROM table")
value = await db.fetchval("SELECT COUNT(*) FROM table")
```

### 2. MLX Service (Singleton Pattern)

```python
# Use mlx_instance module to avoid circular imports
from backend.mlx_instance import get_mlx_service, init_mlx_service

mlx_service = get_mlx_service()

# MLX calls are blocking, wrap in thread pool:
def generate_tokens():
    return mlx_lm.generate(model, tokenizer, prompt, ...)

loop = asyncio.get_event_loop()
tokens = await loop.run_in_executor(None, generate_tokens)
```

### 3. MLX Sampler Creation

```python
# Use make_sampler() instead of passing temperature directly
from mlx_lm.sample_utils import make_sampler

sampler = make_sampler(temp=temperature)
mlx_lm.generate(..., sampler=sampler)
```

### 4. Prompt Building with Chat Template

```python
# Use tokenizer's apply_chat_template for proper prompt format
if hasattr(tokenizer, 'apply_chat_template'):
    prompt = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True
    )
```

### 5. FastAPI Request Injection

```python
# Always type annotate Request parameter
from fastapi import Request

@router.post("")
async def endpoint(
    request: Request,  # <-- Must be typed
    body: BodyModel,
    api_key: dict = Depends(verify_api_key)
):
    db = request.app.state.db
```

### 6. App State & Lifespan

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    init_mlx_service()

    # Connect DB only if not already set (for tests)
    if not hasattr(app.state, "db") or app.state.db is None:
        app.state.db = await get_database()

    yield

    # Cleanup
    if hasattr(app.state, "db"):
        await app.state.db.close()
```

### 7. Testing with TestClient

```python
# Setup database with all required tables
conn = await aiosqlite.connect(":memory:")
conn.row_factory = aiosqlite.Row
await conn.executescript(CREATE_TABLES_SQL)

# Create app with test db
app = create_app(db)
app.state.model_registry = ModelRegistryService(db)
await app.state.model_registry.initialize()

# Use TestClient for sync-like API testing
with TestClient(app) as client:
    response = client.post("/api/v1/...", json={...})
```

### 8. Pydantic Models for Request Bodies

```python
# Always use Pydantic models, not query params
class CreateSessionRequest(BaseModel):
    name: Optional[str] = None
    model: Optional[str] = None
    temperature: Optional[float] = 0.7

@router.post("")
async def create_session(request: Request, request_body: CreateSessionRequest, ...):
    model = request_body.model or "default"
```

## Database Schema

```sql
-- API Keys (authentication)
api_keys: id, key_hash, key_prefix, name, created_at, last_used_at, is_active

-- Sessions
sessions: id, api_key_id, name, model, temperature, max_tokens, system_prompt, created_at, updated_at

-- Messages
messages: id, session_id, role, content, created_at

-- Usage Logs
usage_logs: id, api_key_id, session_id, model, input_tokens, output_tokens, time_ms, created_at

-- Supported Models (registry)
supported_models: id, name, model_id, description, params_count, quantization, is_active, created_at
```

## Running Commands

```bash
# Backend dependencies
pip install fastapi uvicorn aiosqlite mlx-lm pytest pytest-asyncio httpx

# Frontend dependencies
cd frontend && npm install

# Backend tests
python -m pytest backend/tests/ -v

# Frontend tests (Vitest)
cd frontend && npm run test

# Initialize database
python backend/init_db.py

# Start backend
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000

# Start frontend
cd frontend && npm run dev
```

## API Structure

| Prefix | Routes | Auth |
|--------|--------|------|
| `/api/v1/` | Chat, Sessions, Models, Usage, Settings | Required |
| `/v1/` | OpenAI-compatible (chat/completions, models) | Required |
| `/health` | Health check | None |

## Model Registry

- Models stored in `supported_models` table
- Local models initialized in `init_db.py`
- New models can be added via API or `init_db.py`
- Model ID format: `organization/model-name` (e.g., `mlx-community/Qwen2.5-7B-4bit`)

## Project Rules

### TDD Methodology (CRITICAL - ALWAYS FOLLOW)

This project uses **Test-Driven Development (TDD)**. The workflow is:

1. **Write tests FIRST** - Before implementing any feature, write failing tests
2. **Implement the feature** - Write the minimum code to make tests pass
3. **Refactor if needed** - Improve code while keeping tests green
4. **All tests must pass** - Feature is only complete when tests pass

**The standard for feature completion is: ALL TESTS PASS**

```bash
# ALWAYS write tests first, then implement:
# 1. Backend: Write failing test first
# 2. Backend: Run test, verify it fails
# 3. Backend: Implement feature
# 4. Backend: Run test, verify it passes

# TDD Workflow Example:
python -m pytest backend/tests/ -v  # Run tests first
# See tests fail
# Implement feature
# Run tests again
# All must pass before moving on
```

### Testing Requirement (IMPORTANT)

**Every code or database script change MUST pass all tests before completion.**

```bash
# Backend tests
python -m pytest backend/tests/ -v

# Frontend tests (Vitest)
cd frontend && npm run test

# Expected: ALL tests pass
# If any test fails: Feature is NOT complete
```

### Documentation Update Requirement (IMPORTANT)

After completing any feature (when all tests pass), update documentation:

1. **TDD_IMPLEMENT.md** - Update progress and mark feature as complete
2. **CLAUDE.md** - Add new patterns if needed
3. **README.md** - Add usage examples if needed

```bash
# Check what needs to be updated
git status
```

### Test Categories

- **Unit tests** (`backend/tests/unit/`): Service logic, data classes
- **API tests** (`backend/tests/api/`): HTTP endpoints, authentication
- **Integration tests** (`backend/tests/integration/`): Real MLX model testing
- **Frontend tests** (`frontend/src/**/*.test.ts`): Vue components, stores, API calls

## Avoid These Mistakes

1. **Don't use `request = None`** - FastAPI won't inject it. Use `request: Request`
2. **Don't pass `temperature` directly to `mlx_lm.generate`** - Use `sampler=make_sampler(temp=...)`
3. **Don't call blocking MLX functions directly** - Wrap in `run_in_executor`
4. **Don't forget `conn.row_factory = aiosqlite.Row`** - Required for dict-like access
5. **Don't create app state in multiple places** - Lifespan manages it
