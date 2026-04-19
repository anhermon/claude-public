# context-os (unified plugin)

Single Claude Code plugin combining:

- **Knowledge graph** — quickstart, ingest, local graph engine (`knowledge_base/` + `[[wiki-links]]`)
- **Session analytics** — [cc-lens](https://github.com/Arindam200/cc-lens) (`npx cc-lens`) + [ccusage](https://github.com/ryoppippi/ccusage) (`npx ccusage`)
- **Token playbook** — `token-efficiency` skill (waste taxonomy + ROI playbook)
- **Context audit** — `context-os audit` merges graph health + optional cc-lens HTML + ccusage
- **Three-mode ingest** — hooks (AUTO), `ingest source` (SOURCE), `ingest session` (HISTORICAL)

## Prerequisites

- **Python 3.10+** (bundled CLI)
- **Node.js** — for `npx cc-lens` and `npx ccusage`

## Install

1. Add this plugin to Claude Code (plugin path or marketplace).

2. **Install the `context-os` CLI globally** (pick one):

   **Recommended — uv** ([astral.sh/uv](https://docs.astral.sh/uv/)):

   ```bash
   cd /path/to/claude-public/plugins/context-os
   uv tool install .
   # Re-install after pulling: uv tool install . --force
   ```

   **pip** (editable, same repo):

   ```bash
   cd /path/to/claude-public/plugins/context-os
   python3 -m pip install -e .
   ```

   **npx / bunx** (Node shim → runs `python3 -m context_os`; ships `context_os/` + `cli.mjs`):

   ```bash
   cd /path/to/claude-public/plugins/context-os
   npm link
   # or: bun link
   context-os --help
   ```

   **Symlink only** (no package manager):

   ```bash
   bash scripts/install.sh
   # or: export PATH="/path/to/context-os-plugin/bin:$PATH"
   ```

   **Module form** (no PATH change):

   ```bash
   python3 -m context_os
   ```

3. Optional: merge `hooks/settings-snippet.json` into your project hooks and set `CONTEXT_OS_PLUGIN_ROOT` to this plugin’s root when hooks need it.

Verify:

```bash
context-os --help
context-os graph health --graph knowledge_base
```

## Commands

Slash-command markdown lives in **`commands/`** at the plugin root (a symlink keeps `.claude/commands` compatible).

| Slash command | Purpose |
|---------------|---------|
| `/quickstart` | Guided setup |
| `/ingest` | Raw → knowledge nodes |
| `/audit` | Graph + token audit |
| `/ingest-history` | Sessions → graph |
| `/cc-lens` | cc-lens analysis → paste-ready remediation prompt or per-project fixes (with your approval) |

## Bundled CLI

| Command | Purpose |
|---------|---------|
| `context-os graph health\|query\|show` | Local markdown graph |
| `context-os sessions list\|replay` | `~/.claude/projects/*.jsonl` |
| `context-os heat` | Heuristic file heat from session logs |
| `context-os ingest session\|file\|source` | Populate `knowledge_base/` |
| `context-os audit` | Combined HTML report |
| `context-os cc-lens …` | Forensics spec + HTML (needs dashboard) |
| `context-os ccusage …` | Pass-through to `npx ccusage` |

### cc-lens port (blank page on :3002?)

Upstream **`npx cc-lens`** chooses a free port and only one Next.js dev server should run. If **:3001** is already in use by cc-lens, a **second** launch may bind to **:3002** and show an **empty** page (“Another next dev server is already running”).

- **Use the first instance:** open **`http://localhost:3001`** (or whatever port `cc-lens` printed when it started).
- **`context-os cc-lens up`** detects an existing server and **does not** start a duplicate.
- **`context-os cc-lens analyze`** auto-discovers a running API on **3001–3010**, or set **`CC_LENS_BASE_URL`** / **`CONTEXT_OS_CC_LENS_URL`** (e.g. `http://localhost:3001`).

## Agents

- `token-efficiency-analyzer` — deep dive + optional `interactive-review-server.py` on port **3118**

## Legacy

The previous **cc-lens**-only plugin and **token-efficiency**-only plugin are **merged here**. The **gtm-context-os-quickstart** repo points to this tree via `REDIRECT.md`.

## Author

Angel Hermon — see `.claude-plugin/plugin.json`.
