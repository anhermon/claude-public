# cc-lens

Token usage intelligence for Claude Code. Reads session data from `~/.claude/` via the cc-lens dashboard API and generates forensics reports with waste classification, Chart.js visualizations (scatter, radar, heatmap, time-series), interactive session drilldown, and actionable optimization recommendations.

## Skill: `/cc-lens`

Four operations:

- **SETUP** — install and start the cc-lens dashboard (`npx cc-lens`), verify it's live at `http://localhost:3001`
- **ANALYZE** — full top-N workflow: fetch all projects, score waste categories, generate a self-contained HTML forensics report with charts and recommendations
- **PROJECT** — deep dive into a single project: session timeline, cost breakdown, per-session waste classification, and outlier detection
- **FORENSICS** — single-session replay analysis: tool call trace, context growth curve, cache efficiency, and per-turn waste attribution

### Dashboard features (v1.1)

- **Time-series charts** — cost by project (stacked), waste category breakdown (stacked), daily cost & sessions, cache hit rate trend
- **Date filter** — sessions table filters to last 7 / 14 / 30 days or custom range
- **Week-over-week KPIs** — cost and waste score delta vs prior week
- **Session drilldown** — click any session row to see per-turn token breakdown and individual tool call details (what tool, what input)

## Agent: `token-efficiency-analyzer`

A holistic analyst agent that goes beyond statistics to understand *why* sessions are expensive:

1. Connects to the cc-lens API and runs the full analysis pipeline
2. Inspects actual session replays for the worst offenders — reads what the session was doing, traces the approach, identifies where cost concentrated
3. Clusters findings into root-cause patterns (exploration without structure, iterative fix loops, compaction neglect, cache instability, parallel sprawl)
4. Generates prioritized recommendations tied to specific sessions and tasks — not generic advice
5. Presents via interactive selection (`http://localhost:3118`) so you choose what to act on
6. Implements selected improvements

**Trigger phrases:**
- "analyze my token usage"
- "token efficiency report"
- "session audit"
- "why is [project] expensive"

## Prerequisites

- Node.js installed
- `npx cc-lens` available (installs automatically on first run via npx)
- The cc-lens dashboard must be running at `http://localhost:3001` before ANALYZE/PROJECT/FORENSICS operations (use SETUP to start it)
- The `interactive-review` skill must be installed for the agent's review presentation step

## Usage

```
/cc-lens                             → skill: SETUP, ANALYZE, PROJECT, or FORENSICS
/token-efficiency-analyzer           → agent: holistic analysis + interactive recommendations
```

The skill loads `/token-efficiency` automatically for industry-standard waste taxonomy, scoring thresholds, and the optimization playbook.
