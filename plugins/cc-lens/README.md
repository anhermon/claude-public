# cc-lens

Token usage intelligence for Claude Code. Reads session data from `~/.claude/` via the cc-lens dashboard API and generates forensics reports with waste classification, Chart.js visualizations (scatter, radar, heatmap, trend), and actionable optimization recommendations.

## Operations

- **SETUP** — install and start the cc-lens dashboard (`npx cc-lens`), verify it's live at `http://localhost:3001`
- **ANALYZE** — full top-N workflow: fetch all projects, score waste categories, generate a self-contained HTML forensics report with charts and recommendations
- **PROJECT** — deep dive into a single project: session timeline, cost breakdown, per-session waste classification, and outlier detection
- **FORENSICS** — single-session replay analysis: tool call trace, context growth curve, cache efficiency, and per-turn waste attribution

## Prerequisites

- Node.js installed
- `npx cc-lens` available (installs automatically on first run via npx)
- The cc-lens dashboard must be running at `http://localhost:3001` before ANALYZE/PROJECT/FORENSICS operations (use SETUP to start it)

## Usage

Trigger with `/cc-lens` or any of these phrases:

- "analyze token usage"
- "token report"
- "what's burning tokens"
- "session forensics"
- "why is [project] so expensive"
- "top projects by cost"
- "setup cc-lens"
- "start the dashboard"

The skill loads `/token-efficiency` automatically for industry-standard waste taxonomy, scoring thresholds, and optimization recommendations.
