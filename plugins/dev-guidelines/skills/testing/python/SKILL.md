---
name: python
description: Python testing conventions using pytest, pytest-asyncio, and httpx. Implements the tier model and layered switching pattern from testing/ using pytest markers and fixtures. Use when writing or modifying tests in any Python project.
license: MIT
compatibility: opencode
metadata:
  audience: developers
  workflow: testing
---

## What I do

I provide Python-specific testing conventions. Always load `testing/` first for philosophy and tier model — this skill covers the pytest implementation of those principles.

## Test Runner Decision Tree

```
Which test runner?
├── New project or greenfield → pytest  ← standard; richer fixtures, markers, plugins
├── Stdlib-only constraint (no pip install allowed) → unittest
│   └── Trade-off: no fixtures, no markers, verbose setup/teardown, no parameterize
├── Already on unittest → consider migrating; pytest runs unittest tests natively
└── Both? → pytest discovers and runs unittest.TestCase subclasses without changes
```

**Trade-offs:**

| Runner | Best for | Watch out for |
|---|---|---|
| **pytest** | All production projects; async tests; parametrize; fixtures; markers; plugins | Requires install; fixture magic can be confusing to newcomers |
| **unittest** | Zero-dependency environments; stdlib constraint | Verbose; no fixtures; no markers; no async support without extra setup |

This skill covers pytest. For unittest, apply the same tier model using `setUp`/`tearDown` and `TestSuite` grouping, but expect more boilerplate.

---

## Stack

| Concern | Tool |
|---|---|
| Test runner | pytest |
| Async tests | pytest-asyncio |
| HTTP test client | httpx `AsyncClient` (never `TestClient`) |
| Coverage | pytest-cov — enforced at 80% |
| Data setup | pytest fixtures (simple) or factory-boy (relational/complex) — confirm per project |

---

## Marker conventions

Markers implement the tier model. Every test must have exactly one tier marker.

```ini
# pytest.ini or pyproject.toml [tool.pytest.ini_options]
markers =
    unit: Single function or class, all external deps mocked
    smoke: Fast integration subset covering critical paths
    integration: Full integration, real dependencies, no mocks
    e2e: Reserved for Playwright — do not apply to pytest tests
```

```python
@pytest.mark.unit
async def test_calculate_discount():
    ...

@pytest.mark.smoke
async def test_create_order_happy_path():
    ...

@pytest.mark.integration
async def test_order_payment_flow():
    ...
```

**Taskfile mapping:**
```yaml
tasks:
  test:unit:
    cmd: pytest -m unit --cov=src --cov-fail-under=80

  test:smoke:
    cmd: pytest -m smoke

  test:integration:
    cmd: pytest -m integration

  test:all:
    cmd: pytest --cov=src --cov-fail-under=80
```

---

## Project structure

```
tests/
  conftest.py           ← session/module-scoped fixtures, DB setup, client factory
  unit/
    test_services.py    ← @pytest.mark.unit
    test_models.py
  integration/
    test_api.py         ← @pytest.mark.smoke and @pytest.mark.integration
    test_flows.py
  conftest.py
```

---

## Async setup

```python
# pyproject.toml
[tool.pytest.ini_options]
asyncio_mode = "auto"   # all async tests run without @pytest.mark.asyncio decorator
```

All test functions that touch I/O are `async def`. Never mix sync and async in the same test.

---

## Fixtures

### DB session fixture (async, transaction-scoped)

Wrap each test in a transaction and roll back — no teardown rebuild.

```python
# conftest.py
import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlmodel import SQLModel

TEST_DATABASE_URL = "postgresql+asyncpg://test:test@localhost/testdb"

@pytest.fixture(scope="session")
async def engine():
    engine = create_async_engine(TEST_DATABASE_URL)
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)
    await engine.dispose()

@pytest.fixture
async def db(engine):
    async with AsyncSession(engine) as session:
        async with session.begin():
            yield session
            await session.rollback()   # clean state between tests, no teardown
```

### HTTP client fixture

```python
# conftest.py
import pytest
from httpx import AsyncClient, ASGITransport
from src.main import app

@pytest.fixture
async def client(db):          # inject db to ensure same session scope
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        yield ac
```

---

## Data setup — two approaches

**Approach A: Plain fixtures** — good for simple, low-relational data.

```python
@pytest.fixture
async def existing_user(db):
    user = User(email="test@example.com", hashed_password="...")
    db.add(user)
    await db.flush()
    return user
```

**Approach B: factory-boy** — good for complex relational data with many variants.

```python
# tests/factories.py
import factory
from factory.alchemy import SQLAlchemyModelFactory
from src.models import User

class UserFactory(SQLAlchemyModelFactory):
    class Meta:
        model = User
        sqlalchemy_session_persistence = "flush"

    email = factory.Sequence(lambda n: f"user{n}@example.com")
    hashed_password = factory.LazyFunction(lambda: hash_password("test"))

# In a test
async def test_something(db):
    UserFactory._meta.sqlalchemy_session = db
    user = UserFactory()
```

**Decision rule:** start with plain fixtures. Introduce factory-boy only when fixture setup becomes repetitive across many tests or when you need many variants of the same object.

---

## BDD scenario naming

```python
# Unit — describes function contract
@pytest.mark.unit
async def test_given_zero_items__when_discount_calculated__then_returns_zero():
    assert calculate_discount(items=[]) == 0

# Integration — describes service behavior
@pytest.mark.smoke
async def test_given_valid_user__when_login_requested__then_token_returned(client):
    response = await client.post("/auth/login", json={
        "email": "test@example.com",
        "password": "correct"
    })
    assert response.status_code == 200
    assert "access_token" in response.json()

# Integration (full) — describes flow
@pytest.mark.integration
async def test_given_authenticated_user__when_order_placed__then_confirmation_sent(
    client, existing_user, mock_email_service
):
    ...
```

---

## Mocking

Mock at the service boundary — never mock internal implementation details.

```python
# Mock an external service dependency, not a private method
@pytest.fixture
def mock_payment_gateway(monkeypatch):
    async def fake_charge(amount, card_token):
        return {"status": "success", "charge_id": "ch_test_123"}
    monkeypatch.setattr("src.services.payment.charge", fake_charge)

# Smoke tests use the mock — fast, no external calls
@pytest.mark.smoke
async def test_given_valid_card__when_payment_submitted__then_order_confirmed(
    client, mock_payment_gateway
):
    ...

# Integration tests use the real gateway — no mock fixture injected
@pytest.mark.integration
async def test_given_valid_card__when_payment_submitted__then_order_confirmed(
    client   # no mock_payment_gateway
):
    ...
```

The same scenario exists at two tiers. The smoke version runs on every commit. The integration version runs on PR.

---

## Coverage

```toml
# pyproject.toml
[tool.coverage.run]
source = ["src"]
omit = ["src/main.py", "tests/*", "*/__init__.py"]

[tool.coverage.report]
fail_under = 80
show_missing = true
```

Coverage is enforced on `task test:unit` and `task test:all`. Not enforced on `test:smoke` or `test:integration` runs.

---

## What not to do

- Do not use `TestClient` — use `httpx.AsyncClient`.
- Do not use `time.sleep()` — use `await asyncio.sleep()` only when genuinely needed, prefer async waiters.
- Do not rebuild the DB for every test — use transaction rollback.
- Do not test ORM queries directly — test the service methods that use them.
- Do not assert on response structure that comes from the framework (FastAPI auto-generates 422 for validation errors — don't test that, test your validation logic).
- Do not share mutable state between tests via module-level variables.
- Do not omit tier markers — every test must be tagged.
