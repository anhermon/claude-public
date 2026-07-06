---
name: backend-python
description: Python backend conventions. Framework decision tree (FastAPI vs Flask vs Django vs Django REST) with trade-offs, then routes to implementation conventions for the chosen framework. Load after dev-guidelines when working on any Python backend service, API, worker, or CLI.
license: MIT
compatibility: claude-code
metadata:
  audience: developers
  workflow: backend-development
---

## What I do

Guide Python backend decisions and provide implementation conventions. Start with the framework choice, then load the relevant reference file.

## When to use me

Load when writing or modifying any Python backend service, API, worker, or CLI.

---

## Setup

```bash
# pip-managed project
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt

# uv-managed project (pyproject.toml + uv.lock — no requirements.txt)
uv sync --group dev && source .venv/bin/activate
```

> Do not mix `pip install` into a `uv`-managed project.

---

## Framework Decision Tree

```
Is this a new project or greenfield service?
├── Yes → Need async I/O (DB, HTTP calls, queues)?
│   ├── Yes → Need full admin panel + ORM-first?
│   │   ├── Yes → Django + DRF
│   │   └── No  → FastAPI  ← default for new async APIs
│   └── No  → Tiny script or simple sync CRUD?
│       ├── Yes → Flask
│       └── No  → FastAPI (async is cheap, start right)
└── No (existing project) → match whatever framework is already in use
```

| Framework | Best for | Watch out for |
|---|---|---|
| **FastAPI** | Async APIs, microservices, ML serving, high concurrency | More setup; requires Pydantic discipline |
| **Flask** | Simple sync APIs, prototypes, small teams | No async story; grows messy without structure |
| **Django + DRF** | Admin-heavy, ORM-first, large models | Sync by default; heavier than needed for pure APIs |

---

## Supporting files

Load the file that matches your framework — it has the full stack, project structure, conventions, and patterns:

| Framework | Reference |
|---|---|
| FastAPI | [fastapi.md](fastapi.md) |
| Flask | [flask.md](flask.md) |
| Django + DRF | [django.md](django.md) |
| Python coding patterns (EAFP, Protocols) | [patterns.md](patterns.md) |

---

## What not to do (all frameworks)

- Do not access `os.environ` directly — use a typed settings/config class.
- Do not put business logic in route handlers / views — delegate to services.
- Do not return raw ORM objects from API endpoints — always serialize.
- Do not use `Any` in Pydantic models or type annotations without justification.
- Do not use stdlib `logging` — use `loguru` (see `observability` skill).
- Do not hand-roll auth — use the framework's recommended auth library.
- Do not hardcode secrets — see `dev-guidelines` for `.env.local` / SOPS workflow.
- Do not use `sys.path.append()` with relative paths — use proper package structure or editable installs.
