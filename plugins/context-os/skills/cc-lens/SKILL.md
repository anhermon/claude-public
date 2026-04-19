---
name: cc-lens
description: >
  Token usage intelligence for Claude Code via the cc-lens dashboard (http://localhost:3001).
  Four operations: SETUP (install & start), ANALYZE (full top-N workflow with forensics report),
  PROJECT (deep dive into one project), FORENSICS (single-session replay analysis).
  Generates self-contained HTML reports with Chart.js visualizations, waste classification,
  and actionable optimization recommendations. Loads /token-efficiency for industry-standard
  waste taxonomy, scoring thresholds, and optimization playbook.

  Trigger on: "analyze token usage", "token report", "what's burning tokens", "cc-lens",
  "session forensics", "why is [project] so expensive", "optimize token usage",
  "setup cc-lens", "start the dashboard", "top projects by cost", "session outliers".
license: private
compatibility: claude-sonnet-4-5+
metadata:
  dashboard_url: http://localhost:3001
  script: context-os cc-lens (bundled; runs context_os/analyze.py + generate_dashboard.py)
  operations: [setup, analyze, project, forensics]
---

# cc-lens

Token usage intelligence for Claude Code. Reads from `~/.claude/` via the cc-lens dashboard API
(`http://localhost:3001`) and generates forensics reports with waste classification and
actionable optimization recommendations.

---

## Dashboard URL

`npx cc-lens` may bind to **any free port** (often **3001**). The bundled analyzer auto-discovers `http://localhost:3001`–`3010` for `/api/stats`, or use **`CC_LENS_BASE_URL`**. If you see a **blank page on :3002**, a server is usually already running on **:3001** — use that URL; do not start a second cc-lens.

---

## Operation: SETUP

**Triggered by:** "setup cc-lens", "install cc-lens", "start the dashboard", "launch cc-lens"

### Steps

1. **Check if already running:**
   ```bash
   curl -s http://localhost:3001/api/stats > /dev/null 2>&1 && echo "running" || echo "not running"
   ```

2. **If not running — start it** (either works):
   ```bash
   context-os cc-lens up
   # or: npx --yes cc-lens@latest &
   sleep 3
   curl -s http://localhost:3001/api/stats > /dev/null 2>&1 && echo "Dashboard live at http://localhost:3001" || echo "Still starting..."
   ```

3. **Verify and report:**
   ```bash
   curl -s http://localhost:3001/api/stats | python3 -c "
   import json, sys
   d = json.load(sys.stdin)
   print(f'Sessions indexed: {d.get(\"total_sessions\", d.get(\"session_count\", \"?\"))}')
   print(f'Total cost tracked: \${d.get(\"total_cost\", 0):.2f}')
   "
   ```

4. Tell the user the dashboard is live and offer to run ANALYZE.

---

## Operation: ANALYZE

**Triggered by:** "analyze token usage", "token report", "cc-lens", "top projects by cost", "what's burning my tokens"

**Default:** top 5 projects by `estimated_cost`, then top 3 outlier sessions per project.

**Parameters (from user prompt):**
- `top_n` — number of projects (default: 5)
- `sort_by` — "cost" (default) or "tokens"
- `sessions_per_project` — outlier sessions to drill into (default: 3)

### Steps

1. **Run the bundled pipeline** (writes `/tmp/cc-lens-spec.json` + `/tmp/cc-lens-report.html`):
   ```bash
   context-os cc-lens analyze \
     --top-n 5 \
     --sort-by cost \
     --sessions-per-project 3
   open /tmp/cc-lens-report.html
   ```
   Adjust `--top-n`, `--sort-by`, `--sessions-per-project` from user request.

2. **Summarize key findings** from stdout:
   - Top 3 waste categories found across all analyzed projects
   - Single most actionable recommendation
   - Total potential cost savings if recommendations are applied

---

## Operation: PROJECT

**Triggered by:** "analyze [project name]", "deep dive [project]", "why is [project] expensive"

### Steps

1. **Find the project slug:**
   ```bash
   curl -s http://localhost:3001/api/projects | python3 -c "
   import json, sys
   projects = json.load(sys.stdin).get('projects', [])
   for p in sorted(projects, key=lambda x: x['estimated_cost'], reverse=True):
       print(f'{p[\"estimated_cost\"]:.2f}  {p[\"slug\"]}  ({p[\"display_name\"]})')
   " | head -20
   ```

2. **Run analysis for that project:**
   ```bash
   context-os cc-lens project --project SLUG --sessions-per-project 10
   open /tmp/cc-lens-project-SLUG.html
   ```

3. **Open and summarize.**

---

## Operation: FORENSICS

**Triggered by:** "session forensics SESSION_ID", "analyze session X", "what happened in session X"

### Steps

1. **Fetch replay data:**
   ```bash
   curl -s http://localhost:3001/api/sessions/SESSION_ID/replay | python3 -c "
   import json, sys
   d = json.load(sys.stdin)
   turns = d['turns']
   print(f'Turns: {len(turns)}  Total cost: \${d[\"total_cost\"]:.4f}')
   assistant_turns = [t for t in turns if t['type'] == 'assistant']
   for t in assistant_turns[:5]:
       u = t.get('usage', {})
       print(f'  [{t[\"timestamp\"][:19]}] in={u.get(\"input_tokens\",0)} out={u.get(\"output_tokens\",0)} cache_r={u.get(\"cache_read_input_tokens\",0)} cost=\${t.get(\"estimated_cost\",0):.4f} tools={len(t.get(\"tool_calls\",[]))}')
   "
   ```

2. **Run deep forensics:**
   ```bash
   context-os cc-lens forensics --session SESSION_ID
   open /tmp/cc-lens-session-SESSION_ID.html
   ```

3. **Open and summarize** the turn-by-turn waste findings.

---

## Waste Classification System

The analyzer scores sessions and projects across these categories:

### Category 1: Context Bloat
**Signal:** `cache_creation_input_tokens` >> `input_tokens`; long sessions without `has_compaction`.
**Threshold:** cache_creation > 5× input_tokens, or session > 60 min without compaction.
**Fix:** Add `/compact` triggers, break long sessions, prune CLAUDE.md and memory files.

### Category 2: Cache Inefficiency
**Signal:** Low cache hit rate = `cache_read / (cache_creation + cache_read + input)`.
**Threshold:** Cache hit rate < 40% on sessions > 10 turns.
**Fix:** Keep system prompts stable, don't randomize tool descriptions, use `ephemeral: true` for stable context blocks.

### Category 3: Tool Pollution
**Signal:** High ratio of tool calls to useful output tokens; MCP tools dominating `tool_counts`.
**Threshold:** >50 tool calls per session OR any single MCP tool called >20× in one session.
**Fix:** Batch tool calls, avoid redundant reads/searches, disable unused MCP servers.

### Category 4: Parallel Session Sprawl
**Signal:** Multiple sessions starting within the same 30-minute window on the same project.
**Threshold:** ≥3 sessions active concurrently on the same project.
**Fix:** Consolidate work into fewer, focused sessions; avoid multiple terminal instances on same project.

### Category 5: Interruption Loops
**Signal:** High `user_interruptions` (>5 in a session) combined with high output tokens.
**Threshold:** interruptions > 5 AND output_tokens > 10,000.
**Fix:** Write clearer prompts, use TodoWrite to maintain shared state between turns, reduce task scope.

### Category 6: Compaction Absence in Long Sessions
**Signal:** `has_compaction = false` AND `duration_minutes > 45`.
**Threshold:** Sessions > 45 min without compaction boundary.
**Fix:** Use `/compact` periodically, or configure auto-compaction thresholds.

### Category 7: Thinking Token Waste
**Signal:** `has_thinking = true` but low output quality (output_tokens < 200 per turn).
**Threshold:** Thinking sessions where output/input ratio < 0.05.
**Fix:** Reserve extended thinking for genuinely complex reasoning tasks; disable for routine operations.

### Category 8: Repeat Tool Hammering
**Signal:** Same tool called many times within a session (e.g., 50+ Bash calls, 30+ Read calls).
**Threshold:** Any single tool called >40× in one session.
**Fix:** Use glob/grep instead of repeated reads, batch Bash operations, use Agent for exploratory work.

---

## Session table and drilldown (agent-oriented)

- **Task column** — First user message in the session (when available from replay or API), truncated with full text in tooltip. Use it to see *what* drove cost (e.g. Paperclip “Continue your work” vs a one-off question).
- **Waste column** — Total waste score plus **mini badges** for every category scoring **>15** (compound waste is visible, not only the top category).
- **Top Issue** — Primary category badge; **“⚠ no /compact”** appears when `duration_minutes > 1000` and `has_compaction` is false.
- **Cost donut** — Uses **full project costs** from the spec (`projects_donut`), not the stacked “waste score” bar chart series (avoids wrong $ / % in the legend).
- **Repeat read %** (drilldown KPI) — Share of read operations that hit the same path again (from replay). Green **&lt;15%**, amber **&lt;30%**, red **≥30%**.
- **Sequential tools %** (drilldown KPI) — Share of tool-using assistant turns that issued **exactly one** tool call (batching signal). Green **&lt;40%**, amber **&lt;60%**, red **≥60%**.
- **What to change** — For tool hammering / tool pollution, the report prefers **replay-derived** text listing repeated commands/signatures (≥3×). Falls back to category playbook text if nothing repeats enough.
- **Cache health (per turn)** — Line chart of cache-read share per assistant turn when replay includes `usage` cache fields (context drift within long sessions).

---

## Visualization Checklist

The HTML report includes:

1. **Bar chart** — Top N projects by waste category scores (stacked)
2. **Scatter plot** — Sessions: duration (x) vs cost (y), colored by waste category
3. **Donut chart** — **Cost** distribution across projects (uses `projects_donut` / session rollup fallback)
4. **Heat map** — Session density by hour-of-day × day-of-week
5. **Waste radar** — Per-project waste score across categories (radar/spider chart)
6. **Turn timeline** — Per-turn cost bar chart with tool call annotations (when replay present)
7. **Cache efficiency** — Session-level bars + optional **per-turn cache read %** sparkline
8. **Tool usage breakdown** — Horizontal bar chart of tool call counts per session

---

## Output Format

Reports always include:

### Executive Summary
- Total cost analyzed
- Top 3 waste categories (ranked by impact)
- Estimated savings if top recommendations are applied

### Per-Project Cards
Each project card shows:
- Cost, sessions, messages, duration
- Waste score (0–100) with breakdown
- Top 3 outlier sessions with one-line forensic note each

### Forensic Session Analysis
For each outlier session:
- Turn-by-turn token burn chart
- Detected waste patterns with evidence (turn numbers, token counts)
- Specific actionable fix for each detected issue

### Recommendations Table
| Priority | Category | Project | Finding | Action |
|----------|----------|---------|---------|--------|
| P1 | Context Bloat | workspace | 15 sessions >60min no compaction | Add /compact to workflow |
| ... | ... | ... | ... | ... |

---

## After `context-os cc-lens analyze`

The HTML dashboard is not the end state. **`/tmp/cc-lens-spec.json`** holds structured waste scores and flags.

Run the **`/cc-lens`** slash command (see `commands/cc-lens.md` in this plugin) for **actionable** next steps:

- **Mode A** — Export a self-contained remediation prompt for another agent (**A1** Generic or **A2** Claude Code), written to `cc-lens-remediation-prompt.md`.
- **Mode B** — Per-project remediation in this session: proposed edits (CLAUDE.md, `.claudeignore`, `.mcp.json`, hooks) with **explicit approval** before any file changes.
- **Mode C** — Re-run analysis scoped with `--project <slug>`, then A or B.
