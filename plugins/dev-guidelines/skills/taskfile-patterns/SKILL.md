---
name: taskfile-patterns
description: Taskfile (go-task) best practices, anti-patterns, and pitfalls — dev lifecycle, process management, readiness checks, cache hygiene, K8s conventions.
license: MIT
compatibility: claude-code
metadata:
  audience: developers
  workflow: project-setup, dev-tooling
---

# Skill: taskfile-patterns

## What I do

Correct patterns and explicit anti-patterns for writing Taskfiles (go-task v3). Covers dev lifecycle ordering, readiness checking, process management, log hygiene, K8s/infra conventions, and structure rules. Use the template at `templates/Taskfile.template.yaml` as a starting point.

## When to use me

- Starting a new project — scaffold the dev lifecycle correctly from the start
- `task dev` is flaky — zombie ports, stale caches, wrong startup order
- Reviewing or auditing an existing Taskfile
- Writing K8s/staging ops tasks

---

## Core Patterns

### 1. Dev Lifecycle Order

Every `task dev` must follow this sequence:

```
env:check → stop → start backend → (readiness) → start frontend → (readiness) → tail logs
```

```yaml
dev:
  desc: Start full dev environment
  cmds:
    - task: env:check           # fail fast if .env missing
    - task: stop                # kill processes + clear build caches
    - mkdir -p logs
    - task: dev:backend:start   # background + readiness poll
    - task: dev:frontend:start  # background + readiness poll
    - task: dev:tail-logs       # only reached when both are healthy
```

Backend before frontend: frontend API calls fail silently during compilation if the backend isn't up yet.

### 2. `stop` Must Clear Build Caches

Killing processes without clearing caches means every restart inherits stale state. This is the most common source of "works after fresh checkout, breaks after restart."

```yaml
# ❌ WRONG
stop:
  cmds:
    - task: kill:frontend
    - task: kill:backend

# ✅ CORRECT
stop:
  cmds:
    - task: kill:frontend
    - task: kill:backend
    - rm -rf frontend/.next          # Next.js
    - rm -rf frontend/dist           # Vite
    - find . -type d -name __pycache__ | xargs rm -rf 2>/dev/null || true
    - find . -name '*.pyc' -delete 2>/dev/null || true
```

### 3. Readiness Check Ownership

The task that **starts** a service owns its readiness check. The orchestrating `dev` task trusts that `dev:backend:start` returned cleanly.

Never add a second readiness check in the outer task — when the inner check fails, the outer one hangs for its full timeout on a condition that will never arrive.

```yaml
# ❌ WRONG — dual poll; outer hangs if inner already failed
dev:
  cmds:
    - task: dev:frontend:start
    - sh -c 'until [ -f .next/static/chunks/main-app.js ]; do sleep 1; done'  # remove this
    - task: dev:tail-logs

# ✅ CORRECT — poll lives inside the start task
dev:frontend:start:
  internal: true
  cmds:
    - sh -c 'npm run dev > ../../logs/frontend.log 2>&1 & disown'
    - sh -c 'i=0; until curl -sf http://localhost:{{.FRONTEND_PORT}} > /dev/null 2>&1; do
        sleep 1; i=$((i+1));
        [ $i -ge 60 ] && echo "Frontend failed to start — check logs/frontend.log" && exit 1;
      done; echo "Frontend ready."'
```

### 4. Backend Readiness: Never Fire-and-Forget

```yaml
# ❌ WRONG — no readiness check; frontend proceeds even if backend crashed
dev:backend:start:
  cmd: nohup uv run uvicorn src.main:app > logs/backend.log 2>&1 &

# ✅ CORRECT
dev:backend:start:
  internal: true
  cmds:
    - nohup uv run uvicorn src.main:app --reload --host 0.0.0.0 --port {{.BACKEND_PORT}} > logs/backend.log 2>&1 &
    - sh -c 'i=0; until curl -sf http://localhost:{{.BACKEND_PORT}}/health > /dev/null 2>&1; do
        sleep 1; i=$((i+1));
        [ $i -ge 30 ] && echo "Backend failed to start — check logs/backend.log" && exit 1;
      done; echo "Backend ready."'
```

Add a `/health` endpoint to every backend from day one. Without it there is no reliable signal.

### 5. `clean` Must Stop First

```yaml
# ❌ WRONG — deletes dirs the running process may be writing to
clean:
  cmds:
    - rm -rf .next

# ✅ CORRECT
clean:
  cmds:
    - task: stop    # kill + clear caches first
    - rm -rf node_modules/.cache
```

### 6. Targeted Restart Tasks

Provide `dev:restart:frontend` and `dev:restart:backend`. Developers bounce the frontend far more than the full stack — without these they restart everything.

```yaml
dev:restart:backend:
  desc: Restart only the backend
  cmds:
    - task: kill:backend
    - task: dev:backend:start
    - task: dev:tail-logs

dev:restart:frontend:
  desc: Restart only the frontend
  cmds:
    - task: kill:frontend
    - task: dev:frontend:start
    - task: dev:tail-logs
```

### 7. Process Kill: `sleep 1` + Document Broad Matches

`pkill -f` matches on the full `argv` of every process on the machine. Without `sleep 1`, the next task may read the port and still see the dying process.

```yaml
kill:frontend:
  cmd: |
    # NOTE: pkill -f "vite" matches ANY process with "vite" in its argv —
    # including other projects. Acceptable on single-project machines.
    pkill -9 -f "vite" 2>/dev/null || true
    lsof -ti:{{.FRONTEND_PORT}} | xargs kill -9 2>/dev/null || true
    sleep 1    # let the kernel reap the socket before the next task reads the port
  silent: true
```

### 8. Log Hygiene

Use `>` (truncate), never `>>` (append). Old errors must not bleed into new sessions.

```yaml
# ❌  >> lets old errors persist
- nohup uvicorn src.main:app >> logs/backend.log 2>&1 &

# ✅  > starts fresh every time
- nohup uvicorn src.main:app > logs/backend.log 2>&1 &
```

- Keep all service logs in a single root `logs/` directory so `tail -f logs/*.log` works.
- Add framework-generated log dirs to `.gitignore` **and** to `clean`.

### 9. `dir:` vs `sources:` Paths

`dir:` changes the working directory for `cmds`. `sources:` and `generates:` are **always relative to the Taskfile's location** (repo root), regardless of `dir:`.

```yaml
build:frontend:
  dir: frontend
  # NOTE: sources/generates are always repo-root-relative even though
  # dir: changes the working directory for cmds.
  sources:
    - frontend/**/*.{ts,tsx}
  generates:
    - frontend/.next/**/*
  cmd: bun run build
```

### 10. Taskfile Is the Contract

If a command isn't in the Taskfile, it doesn't exist. Developers who run `cd frontend && npm run dev` directly bypass env checks, kill steps, and readiness checks. The Taskfile rots into a lie.

Use `internal: true` to hide implementation steps from `task --list` while keeping them composable.

```yaml
dev:backend:start:
  internal: true   # step, not a user command
```

### 11. Namespace Convention: Colons, Not Hyphens

```yaml
# ❌ WRONG
kill-frontend:
dev-restart-frontend:

# ✅ CORRECT
kill:frontend:
dev:restart:frontend:
```

Colons create a clear hierarchy, make `task --list` readable, and work cleanly with `includes:` (e.g., `task frontend:dev` vs ambiguous `task frontend-dev`).

### 12. kubectl: Never `config use-context`

`kubectl config use-context` globally mutates `~/.kube/config`. If a task fails mid-way, the developer is left pointing at the wrong cluster.

```yaml
# ❌ WRONG
deploy:staging:
  cmds:
    - kubectl config use-context my-cluster
    - helm upgrade ...

# ✅ CORRECT — explicit --context per command, no global side effects
deploy:staging:
  cmds:
    - helm upgrade --install my-app ./helm/my-app \
        --kube-context={{.KUBE_CONTEXT}} \
        -f values-staging.yaml \
        -n {{.STAGE_NAMESPACE}}
```

Declare `KUBE_CONTEXT` in the root `vars:` block. Sub-Taskfiles inherit it via includes.

### 13. Port-Forward Readiness: Poll, Don't Sleep

```yaml
# ❌ WRONG — race condition; port-forward may not be bound yet
- kubectl port-forward svc/my-svc 3001:80 &
- sleep 3

# ✅ CORRECT — poll with explicit timeout and cleanup trap
- |
  kubectl --context={{.KUBE_CONTEXT}} port-forward \
    -n {{.STAGE_NAMESPACE}} svc/{{.STAGE_SVC_NAME}} \
    {{.STAGE_LOCAL_PORT}}:{{.STAGE_SVC_PORT}} &
  PFPID=$!
  trap "kill $PFPID 2>/dev/null" EXIT INT TERM
  i=0; until curl -sf http://localhost:{{.STAGE_LOCAL_PORT}} > /dev/null 2>&1; do
    sleep 1; i=$((i+1))
    [ $i -ge 15 ] && echo "Port-forward not ready after 15s" && exit 1
  done
  echo "Port-forward ready."
  # ... run tests ...
  kill $PFPID
```

### 14. Multi-Service dev: No Raw `& + wait`

`wait` blocks until all background processes exit — it gives no signal about which ones started correctly.

```yaml
# ❌ WRONG
dev:
  cmds:
    - |
      uvicorn main:app &
      npm run dev &
      wait

# ✅ CORRECT — sequential with readiness gates
dev:
  cmds:
    - task: dev:backend:start
    - task: dev:frontend:start
    - task: dev:tail-logs
```

### 15. Env Gate Before dev

```yaml
env:check:
  internal: true
  cmds:
    - |
      if [ ! -f .env ] && [ ! -f .env.local ]; then
        echo "ERROR: No .env or .env.local found. Run: task secrets:decrypt"
        exit 1
      fi

dev:
  cmds:
    - task: env:check   # first, before any process starts
    - task: stop
    - ...
```

### 16. `docker buildx create --use` Is Not Idempotent

```yaml
# ❌ WRONG — fails if a builder already exists
- docker buildx create --use

# ✅ CORRECT
- docker buildx create --use || true
```

---

## Checklist: New Project Taskfile

**Dev lifecycle**
- [ ] `stop` kills processes AND clears build caches
- [ ] `clean` runs `task: stop` as its first command
- [ ] `dev` starts with `task: env:check`, then `task: stop`
- [ ] Every background service has exactly one readiness poll, owned by its start task
- [ ] `dev:restart:frontend` and `dev:restart:backend` exist

**Process management**
- [ ] Every `kill:*` task ends with `sleep 1`
- [ ] All `pkill -f` patterns have a scope comment
- [ ] No `kubectl config use-context` — use `--context=` per command

**Logging**
- [ ] Service logs use `>` (truncate), not `>>`
- [ ] All service logs go to root `logs/` directory
- [ ] Framework log dirs are gitignored and in `clean`
- [ ] Backend exposes `/health`

**Structure**
- [ ] Task names use colons for namespacing, not hyphens
- [ ] All implementation steps have `internal: true`
- [ ] All user-facing tasks have `desc:`
- [ ] No `cd dir && cmd` — use `dir:` field
- [ ] `default` task runs `task --list`

**Infra**
- [ ] `docker buildx create --use || true`
- [ ] Port-forward tasks poll `curl -sf`, not `sleep N`
- [ ] `KUBE_CONTEXT` var in root `vars:` block
- [ ] `install` tasks have `status: [test -d node_modules]` guard

---

## Anti-Pattern Quick Reference

| Anti-pattern | Symptom | Fix |
|---|---|---|
| `stop` doesn't clear cache | Works after fresh checkout, breaks after restart | Add `rm -rf` of build dirs to `stop` |
| Dual readiness polls | Outer hangs when inner fails | Remove outer poll; start task owns it |
| Fire-and-forget backend | Frontend fails silently at startup | Poll `/health` after `nohup` |
| `clean` without `stop` | Running server crashes when its dirs vanish | `task: stop` as first cmd in `clean` |
| No restart tasks | Developer restarts entire stack for one service | Add `dev:restart:frontend/backend` |
| `pkill -f` without comment | Kills unrelated projects on same machine | Add scope comment |
| `kill` without `sleep 1` | Port still in use on next start | Add `sleep 1` after every kill |
| Framework log dirs not gitignored | Stale files accumulate in `git status` | Add to `.gitignore` and `clean` |
| No `/health` endpoint | No reliable readiness signal | Add health endpoint on day one |
| Hyphens as namespace separator | `task frontend-dev` looks like a root task | Use colons: `task frontend:dev` |
| `kubectl config use-context` | Dev left on wrong cluster after partial failure | `--context={{.KUBE_CONTEXT}}` per command |
| `sleep N` for port-forward | Race condition — not ready yet | Poll with `curl -sf` loop |
| Raw `& + wait` multi-service | No readiness ordering between services | Sequential start with readiness tasks |
| No `env:check` before `dev` | Cryptic crash from missing secrets | First cmd in `dev` is `task: env:check` |
| `buildx create --use` without `\|\| true` | Fails if builder already exists | Add `\|\| true` |
| `cd dir && cmd` | Fragile, breaks on spaces | Use `dir:` field |
| `install` without `status:` guard | npm/bun install runs every invocation | Add `status: [test -d node_modules]` |

---

## Key Debugging Commands

```bash
# Is the port free?
lsof -ti:3000

# What's on the port?
lsof -i:3000

# Kill everything on a port
lsof -ti:3000 | xargs kill -9 2>/dev/null || true

# Is the backend up?
curl -sf http://localhost:8000/health && echo "up" || echo "down"

# Watch both service logs
tail -f logs/backend.log logs/frontend.log

# Parse check before running
task --list
task --taskfile path/to/Taskfile.yaml --list

# Check kubectl context without mutating it
kubectl --context=my-cluster get nodes
kubectl config get-contexts
```
