# setup-telemetry plugin

Configure Claude Code to emit telemetry events from its lifecycle hooks.

## Skills

**setup-telemetry** — Set up observability for Claude Code sessions. Choose between a lightweight Langfuse cloud integration (quick start, free tier available) or a fully self-hosted stack with a FastAPI backend and Next.js dashboard (no cloud, all data local).

Trigger phrases: "set up telemetry", "configure observability", "track tool usage", "deploy the telemetry dashboard", "set up langfuse", "monitor claude sessions".

## Two Setup Paths

### Path A — Langfuse (Cloud, quick start)

Streams events to [Langfuse](https://langfuse.com). Free tier available, zero infra required.

### Path B — Custom Dashboard (Self-hosted)

Runs a local FastAPI backend on `:5001` and a Next.js dashboard on `:3001`. All data stays local in SQLite. Includes live feed, session timeline, tool inspector, and metrics panels.

**One-command setup:**
```bash
python3 ~/.claude/skills/setup-telemetry/scripts/setup_custom_dashboard.py
```

**After setup:**
- Dashboard: http://localhost:3001
- Backend health: http://localhost:5001/health

## Bundled Source

```
setup-telemetry/
  backend/           FastAPI backend (app.py, database.py, models.py, requirements.txt)
  dashboard/         Next.js frontend (app/, components/, lib/)
  scripts/
    setup_custom_dashboard.py   Deployment + startup script
  skills/
    setup-telemetry/SKILL.md
```

## Hook Events

| Hook | Event | What it sends |
|------|-------|---------------|
| `session_start_telemetry.py` | `SessionStart` | session ID, cwd, project name |
| `pre_tool_use_telemetry.py` | `PreToolUse` | tool name, tool input |
| `post_tool_use_telemetry.py` | `PostToolUse` | tool name, output, duration, errors |
| `session_end_telemetry.py` | `SessionEnd` | duration, session summary |

All hooks fail silently — a broken backend never blocks Claude Code tool execution.
