# Flask Conventions

Use when the project is already Flask, or for simple sync services where async overhead isn't justified.

## Stack

| Concern | Tool |
|---|---|
| Framework | Flask + Gunicorn (WSGI) |
| Validation | marshmallow or Pydantic v2 (via flask-pydantic) |
| ORM | SQLAlchemy (sync) + Flask-SQLAlchemy |
| Environment | `python-dotenv` + `os.environ` via a `Config` class |

## Project Structure

```
src/
  app.py / __init__.py  ← app factory
  config.py             ← Config class (DevelopmentConfig, ProductionConfig)
  blueprints/           ← domain blueprints (auth, orders, etc.)
  models/               ← SQLAlchemy models
  services/             ← business logic
  schemas/              ← marshmallow / Pydantic schemas
tests/
  conftest.py
  unit/
  integration/
```

## Key conventions

- Use the **app factory pattern** (`create_app(config)`) — never module-level `app = Flask(__name__)` outside a factory.
- Register blueprints in the factory, never at import time.
- Use `flask db` (Flask-Migrate) for schema migrations.
- No `app.run()` in production — use Gunicorn: `gunicorn "src.app:create_app()"`.
