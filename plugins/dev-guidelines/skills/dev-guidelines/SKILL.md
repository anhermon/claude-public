---
name: dev-guidelines
description: General development guidelines entry point. Provides universal rules (script org, repo hygiene, pre-commit, .env handling, CLAUDE.md maintenance) and routes to framework sub-skills based on project stack. Load this first, then load the sub-skills that match your project.
license: MIT
compatibility: claude-code
metadata:
  audience: developers
  workflow: development-process
---

## What I do

I provide universal development guidelines and route you to the right sub-skills based on your project stack. I am framework-agnostic. Sub-skills handle the opinionated implementation choices.

## When to use me

Load me at the start of any development session. Then load the sub-skills that match your project's stack.

---

## Sub-skill routing

Read your project's `AGENTS.md` or `CLAUDE.md` for the declared stack, then load the matching sub-skills:

| What you're working on | Load |
|---|---|
| Python backend | `backend-python` — then see its decision tree (FastAPI / Flask / Django) |
| TypeScript backend | `backend-typescript` — then see its decision tree (Hono / Express / Fastify) |
| Frontend / React | `frontend` — then see its decision tree (Next.js / Vite / Remix) |
| CI/CD pipeline | `ci` — then see its decision tree (Azure DevOps / GitHub Actions / GitLab CI) |
| Infrastructure / deployment | `infra` — then see its decision tree (K8s+Helm / Docker Compose / Serverless) |
| Observability (logging, tracing, metrics) | `observability` |
| Testing (any stack) | `testing` — then load the stack-specific testing sub-skill |

Multiple sub-skills should be loaded together for full-stack projects — e.g. `backend-python` + `testing` + `python` + `ci` for a FastAPI service with CI.

**Project descriptor pattern**: If a project's `AGENTS.md` declares a stack descriptor like:
```
Skills: dev-guidelines (lang=python, ci=azdo, infra=k8s-helm)
```
Map each param to the sub-skill above and load them all.

---

## Universal Guidelines

These apply to every project regardless of language or stack.

### Script Organization

Organize scripts by placing reusable tools in `./scripts/` and temporary ones in `.tmp/`. Before writing a new script:

- **For testing or validation:** use the project's formal testing framework, not ad-hoc scripts.
- **For reusable tasks:** use `Taskfile.yaml`. If a task grows complex, extract logic into `./scripts/` and invoke it from the Taskfile.
- **Never use `Makefile` as the primary task runner** — `Taskfile` is the standard. `Makefile` may exist as a legacy shim but must not grow.
- **If a Taskfile task doesn't exist yet, add it** — don't work around it with raw shell commands.

### Repository Cleanliness

**Keep the project root clean.** The root is for project-defining files only.

| Allowed at root | Not allowed at root |
|---|---|
| `README.md`, `AGENTS.md`, `CLAUDE.md` | `NOTES.md`, `TODO.md`, `ANALYSIS.md` |
| `CHANGELOG.md`, `CONTRIBUTING.md`, `LICENSE.md` | `PLAN.md`, `scratch.md` |
| `Taskfile.yaml` | `test.sh`, `debug.*` |
| `package.json`, `pyproject.toml` | Any ad-hoc script at root |
| Config files (`.eslintrc`, `tsconfig.json`, `ruff.toml`, etc.) | |

**Session-specific and WIP files go in gitignored locations — never committed:**

```
.claude/          ← session notes, analysis drafts, task breakdowns
docs/scratch/     ← exploratory design docs
.tmp/             ← anything ephemeral
```

**`.gitignore` baseline:**

```gitignore
/.tmp/
/.claude/
/test.sh
/debug.*
/scratch.*
/temp_*
/*.local.*
/NOTES.md
/TODO.md
/PLAN.md
/ANALYSIS.md
/SCRATCH.md
```

### Pre-commit Hooks

**All projects use `pre-commit` as the standard hook framework** — language-agnostic, isolates hook environments, runs identically locally and in CI.

**Install:**
```bash
pip install pre-commit          # or: pipx install pre-commit
pre-commit install              # commit-stage hooks
pre-commit install --hook-type pre-push   # push-stage hooks
```

**Stage split:**
- **commit:** fast feedback — formatting, linting. Must complete in seconds.
- **push:** slow analysis — type checking, security scanning.

**`.pre-commit-config.yaml` reference — universal hygiene block (all projects):**

```yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.6.0
    hooks:
      - id: trailing-whitespace
        stages: [commit]
      - id: end-of-file-fixer
        stages: [commit]
      - id: check-merge-conflict
        stages: [commit]
      - id: check-added-large-files
        stages: [commit]
        args: [--maxkb=500]
      - id: mixed-line-ending
        stages: [commit]
        args: [--fix=lf]
```

Add language-specific blocks from the relevant sub-skill (`backend-python`, `backend-typescript`).

**Skipping hooks — use sparingly:**
```bash
SKIP=mypy git push          # skip a specific hook by name
git commit --no-verify      # WIP/fixup only — never on main or release branches
```

### Environment Variable Handling

**Never read `.env` files directly in code. Never hardcode secrets.**

| Context | Pattern |
|---|---|
| Local dev | `.env` encrypted via SOPS; decrypt to `.env.local` (gitignored) |
| Shell / curl | `set -a && source .env.local && set +a && your_command` |
| Docker | `--env-file .env.local` |
| Python | `pydantic-settings` `Settings` class — never `os.environ` directly |
| Bun / Node | Validated env module (e.g. `env.ts`) — never `process.env` directly |
| CI pipelines | Variable groups or secrets manager — never inline YAML values |

See the `org` skill for org-specific secrets workflow (SOPS+Age, Key Vault, AzDO variable groups).

### CLAUDE.md / AGENTS.md Maintenance

Every project and significant subdirectory should have an `AGENTS.md` (OpenCode native) or `CLAUDE.md` (compatibility fallback) as a **compact navigation index** — not a context dump.

**Where to place them:**
```
project-root/AGENTS.md         ← entry point, key commands, stack descriptor, gotchas
frontend/AGENTS.md             ← frontend-specific patterns and pitfalls
backend/AGENTS.md              ← backend-specific patterns and pitfalls
tests/AGENTS.md                ← test conventions, fixture usage, selector rules
```

**Template:**
```markdown
# <Project> — Quick Reference

## Stack
lang=python, ci=azdo, infra=k8s-helm, test=pytest+playwright

## Skills
Load: dev-guidelines (lang=python, ci=azdo, infra=k8s-helm), testing, python, org

## Key Commands
- `task test:backend` — run backend tests
- `task dev` — start all services

## Architecture (1-liner each)
- Auth: JWT via /api/auth, tokens in httpOnly cookie
- State: Zustand store in src/store/

## Known Pitfalls
- <thing that trips up every session>
```

**When to update:** if the same mistake could recur in a future session without this note, add it.

**What NOT to put here:** full code examples, decisions in flux, session notes, content that duplicates README.

### Context Management

- Check `AGENTS.md` / `CLAUDE.md` first when missing context — before reading the codebase.
- Ask targeted questions when requirements are unclear rather than guessing.
- Update after any session where you corrected course more than once on the same issue.

---

### Constants — No Magic Strings or Numbers

**Never scatter raw literals through code.** All meaningful strings and numbers must be named constants.

**What counts as magic:**

| Type | Magic (bad) | Named constant (good) |
|---|---|---|
| Storage key | `'app:sessions'` | `LS_SESSIONS_KEY` |
| API path | `'/api/run'` | `API_RUN` |
| Timeout ms | `setTimeout(fn, 3000)` | `setTimeout(fn, ERROR_DISPLAY_MS)` |
| Hard limit | `if (items.length > 60)` | `if (items.length > MAX_ITEMS_STORED)` |
| Pixel dimension | `canvas.width = 13` | `CANVAS.w` |
| Default value | `model \|\| 'gpt-4o'` | `model \|\| DEFAULT_MODEL` |
| Status string | `s.status === 'active'` | `s.status === STATUS.ACTIVE` |

**Rules:**

1. **Collect constants in a single dedicated file** — `constants.js`, `constants.ts`, `config.py`, etc. One per module/package, co-located with its consumers.
2. **Name by meaning, not by value** — `ERROR_DISPLAY_MS` not `THREE_SECONDS`.
3. **Group related constants** with a brief JSDoc or comment header — don't alphabetize unrelated things together.
4. **Enums over bare strings** — when a field takes one of N fixed values (status, role, event type), use an object/enum: `const STATUS = { ACTIVE: 'active', CLOSED: 'closed' }`.
5. **Don't over-extract** — inline literals are fine for one-off values with no reuse and obvious meaning (e.g. `Math.max(0, n)`, array index `[0]`). Apply judgement: would a future reader be confused by the raw value?
6. **Co-locate with consumers** — a `constants.js` at the module level is preferred over a single global constants file for a large codebase. For small projects with 5-10 files, one shared file is fine.
7. **Duplicate helpers are a smell** — if the same `fmt`, `esc`, or utility function appears in multiple files, move it to a shared module and import it. Don't copy-paste.

---

### YAML Conventions

Applies to any repo with YAML (K8s manifests, Helm charts, CI pipelines, Docker Compose).

- **Indentation:** 2 spaces — never tabs
- **Document separator:** `---` at top of every YAML file
- **New line at end of file:** Required (enforced by `end-of-file-fixer` pre-commit hook)
- **Trailing whitespace:** Forbidden
- **Anchors for DRY (within same file):**
  ```yaml
  _common: &common        # leading underscore + snake_case anchor name
    replicas: 1
    timeout: 30

  staging:
    <<: *common           # merge key
    replicas: 2
  ```
- **Boolean annotations:** Use quoted strings `"true"` / `"false"` for K8s annotation values, not YAML booleans

---

### GitOps Repository Structure

For repos managing Kubernetes deployments via Helm/Helmfile — git state IS cluster state.

**Standard directory layout:**
```
repo-root/
├── charts/<service>/          ← Helm chart source
│   ├── Chart.yaml
│   ├── values.yaml            ← base defaults ONLY (no env-specific values)
│   ├── values-dev.yaml        ← dev overrides
│   ├── values-prod.yaml       ← prod overrides
│   └── templates/
├── helmfile/                  ← multi-chart orchestration
│   ├── helmfile.yaml
│   └── environments/          ← Go template values (.gotmpl per env)
├── argo/applications/         ← ArgoCD Application definitions
└── Taskfile.yaml
```

**Values resolution order (last wins):** `values.yaml` → env file → region file → cluster file

**Rendered-manifest PR review pattern:**
- Pre-commit hook renders Helm templates → committed output directory (e.g., `helmfile/templated-manifests/`)
- Reviewers see actual K8s resources in the diff, not just template changes
- Catches deployment impact that template diffs hide (wrong replica counts, missing env vars, etc.)
- `SKIP=<hook-name>` to skip during fast local iteration, but always include in PR

**Auto-deploy guard:** ArgoCD apps with `syncPolicy.automated.prune: true` + `selfHeal: true` will revert any manual cluster changes. Never apply to cluster directly — commit to git.
