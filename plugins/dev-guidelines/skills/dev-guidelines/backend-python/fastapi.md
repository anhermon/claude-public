# FastAPI Conventions

## Stack

| Concern | Tool |
|---|---|
| Framework | FastAPI + Uvicorn (ASGI) |
| Validation / Serialization | Pydantic v2 |
| ORM / Data | See ORM decision tree below |
| Environment Variables | `pydantic-settings` — typed `Settings` class, loaded once at startup |
| Auth | `fastapi-users` (do not hand-roll); or `fastapi-azure-auth` for AAD |
| Rate Limiting | `fastapi-limiter` |
| Linting | `ruff` (replaces flake8, black, isort) |
| Type Checking | `mypy` — strict mode, push-stage |
| Security Scan | `bandit` — medium severity+, push-stage |

## ORM Decision Tree

```
Need async DB access?
├── Yes → SQLModel (SQLAlchemy + Pydantic fused) — simple schemas
│       → raw SQLAlchemy async — complex queries / existing DB
│       → Tortoise ORM — if Django-like simplicity preferred
└── No  → SQLAlchemy sync — safest, most ecosystem support
          Peewee — simpler, smaller projects
```

| ORM | Best for | Watch out for |
|---|---|---|
| **SQLModel** | FastAPI projects where API shape ≈ DB shape | Dual-mode adds magic; complex queries need raw SQLAlchemy |
| **SQLAlchemy (async)** | Full control, complex queries, existing schemas | More boilerplate |
| **Tortoise ORM** | Teams coming from Django; async-native | Smaller ecosystem |
| **Peewee** | Simple sync scripts or small Flask apps | No async |

## Project Structure

```
src/
  main.py           ← app factory, lifespan, middleware registration
  api/              ← routers grouped by domain
  core/
    config.py       ← pydantic-settings Settings class
    deps.py         ← shared FastAPI dependencies (db session, current user)
  models/           ← ORM table definitions
  schemas/          ← Pydantic request/response schemas (when separate from models)
  services/         ← business logic; no direct DB access in routers
tests/
  conftest.py       ← fixtures, async test DB setup
  unit/             ← @pytest.mark.unit
  integration/      ← @pytest.mark.smoke / @pytest.mark.integration
```

## Conventions

**Async-first**
- All route handlers are `async def`. Never `def` for routes that touch I/O.
- All DB access uses the async engine (`asyncpg` dialect for PostgreSQL).
- Service functions are `async def` if they call any awaitable.

**Dependency injection**
- DB sessions, auth context, settings — all injected via `Depends()`. Never imported as globals.
- Define shared dependencies in `core/deps.py`.

**Settings**
```python
# core/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str
    secret_key: str
    debug: bool = False
    model_config = {"env_file": ".env.local"}

settings = Settings()
```
Import `settings` from `core/config.py` everywhere. Never access `os.environ` directly.

**Routing**
- Group routers by domain in `api/`. Register in `main.py` with prefix and tags.
- Never put business logic in route handlers — delegate to `services/`.
- Always serialize through a Pydantic schema before returning — never raw ORM objects.

**Error handling**
- Use `HTTPException` for expected errors.
- Define custom exception handlers in `main.py` for domain exceptions.
- Never leak internal error details (stack traces, DB errors) in response bodies.

## Async Safety: Wrapping Blocking Sync Calls

Sync SDKs (Azure, AWS, some DB drivers) block FastAPI's event loop — all concurrent requests stall for the duration of the call.

**Pattern:** wrap every blocking sync function with `loop.run_in_executor`:

```python
import asyncio

async def my_async_wrapper(arg1, arg2):
    """Async wrapper for blocking_sync_fn to prevent blocking the event loop."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, blocking_sync_fn, arg1, arg2)
```

**Rule:** if any sync function touches the network or disk and takes > ~10ms, wrap it.

## Webhook / Notification Pattern

Separate payload construction from I/O — builders are pure/testable, sender is async.

```python
# builders — pure functions, no I/O
def create_success_notification(user_email: str, detail: str) -> Dict:
    return {"blocks": [{"type": "header", "text": {"type": "plain_text", "text": f"✅ {detail}"}}]}

# sender — async, explicit timeout, returns bool, never re-raises
async def send_notification(webhook_url: str, payload: Dict, timeout: int = 10) -> bool:
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(webhook_url, json=payload,
                headers={"Content-Type": "application/json"},
                timeout=aiohttp.ClientTimeout(total=timeout)) as response:
                return response.status == 200
    except Exception as e:
        log.error(f"Notification error: {e}")
        return False
```

Rules: builders are `def` (sync, pure) — senders return `bool` — always set explicit `ClientTimeout`.

## Testing: Mock at the Route Import Path

Patch at **where the route imported it**, not the source module:

```python
# routes/cluster.py: from _cmd.cluster import deploy_job
with patch("routes.cluster.deploy_job", new_callable=AsyncMock) as mock_deploy:
    mock_deploy.return_value = {"status": "ok"}
    response = client.post("/api/v2/cluster", json=payload)
    mock_deploy.assert_called_once()
```

**Startup patching in `conftest.py`:** patch before importing the app to prevent lifespan from making real network calls:

```python
# conftest.py — patch BEFORE importing the app
_openid_patch = patch("utils.auth.azure_scheme.openid_config")
_mock_openid  = _openid_patch.start()
_mock_openid.load_config = AsyncMock()

from main import app  # noqa: E402
```

Use `dependency_overrides` to inject mock auth for the full test session:

```python
@pytest.fixture(scope="function")
def test_app(mock_user):
    from main import app
    from utils.auth import azure_scheme
    app.dependency_overrides[azure_scheme] = lambda: mock_user
    yield app
    app.dependency_overrides.clear()
```

## Pre-commit (Python block)

```yaml
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.5.0
    hooks:
      - id: ruff
        stages: [commit]
        args: [--fix]
      - id: ruff-format
        stages: [commit]

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.10.0
    hooks:
      - id: mypy
        stages: [push]
        additional_dependencies: [pydantic, sqlmodel]

  - repo: https://github.com/PyCQA/bandit
    rev: 1.7.9
    hooks:
      - id: bandit
        stages: [push]
        args: [--severity-level=medium, -r, src/]
```

## Tooling

```toml
# ruff.toml
line-length = 100
target-version = "py312"

[lint]
select = ["E", "F", "I", "UP", "B", "SIM"]
```
