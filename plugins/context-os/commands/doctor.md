---
name: doctor
description: Preflight diagnostic — verify cc-lens, ccusage, CLI, deps before running /audit or /improve
model: inherit
---

# /doctor — preflight diagnostic

Run this **after a fresh install** and **before** `/audit` or `/improve`. It catches the silent failures
(missing Node, cc-lens not running, ccusage cold cache, CLI not on PATH) that otherwise cause those
commands to "succeed" with empty or degraded output.

## Checks (sequential)

| # | Check | Pass condition |
|---|-------|----------------|
| 1 | Python | ≥ 3.10 |
| 2 | Node / npx | `npx --version` on PATH |
| 3 | ccusage | `npx --yes ccusage@latest --version` completes within 60s |
| 4 | cc-lens dashboard | GET `/api/stats` on `localhost:3001–3010` (or `CC_LENS_BASE_URL` / `CONTEXT_OS_CC_LENS_URL`) within 2s |
| 5 | `context-os` CLI | Found on PATH via `shutil.which` |
| 6 | Plugin root | `CONTEXT_OS_PLUGIN_ROOT` (if set) or derived path is a directory |

Each failing check prints a one-line **fix hint** (e.g. `Start it: npx cc-lens`,
`uv tool install .`, `npx --yes ccusage@latest daily`).

## How to run

```bash
context-os doctor                # human-readable
context-os doctor --format json  # machine-readable: {"checks":[...],"ok":bool}
# fallback if CLI not on PATH yet:
python3 -m context_os doctor
```

Exit code: `0` if everything is OK, `2` if any check failed.

## Agent contract

Before running `/audit` or `/improve` on a fresh install, agents should:

1. Invoke `context-os doctor --format json`.
2. If `ok == false`, surface each failing check's `fix` line to the user.
3. Ask whether to proceed with **degraded analysis** or **stop** and fix first.
