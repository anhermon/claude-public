---
name: audit
description: Full context audit — graph health + forensic token dashboard
model: inherit
---

# Context audit

## What this does

Generates a **cc-lens-style token forensic dashboard** from the user's local
Claude Code session JSONL files (`~/.claude/projects/**/*.jsonl`). No external
dependencies: no cc-lens, no ccusage, no Node.js. If cc-lens IS running, the
dashboard cross-references it; otherwise it proceeds with local data only.

## How to run it

1. Decide the audit-target directory. Default: the current working directory.
2. Run:
   ```bash
   context-os audit --days 30 --out <audit-target>/dashboard-audit
   ```
   Flags:
   - `--days N` — lookback window (default 30).
   - `--out PATH` — output directory. `index.html` + `data/*.json` go here.
   - `--project PATTERN` — filter to sessions whose project folder contains this substring.
3. The command prints the dashboard path and a `file:///...` open-hint. Surface that to the user.
4. Optional: if `npx cc-lens` happens to be running, mention it; otherwise say nothing about it.

## What the dashboard contains

**Overview view** — total cost, top waste category, potential savings, last-7d
cost (+ week-over-week delta), avg waste score; stacked-bar "projects by waste
score", duration-vs-cost scatter, per-project waste radar, project-cost donut,
day×hour activity heatmap, cost-by-project-over-time, waste-over-time, daily
cost & sessions, cache-hit + avg-waste; file-heat table keyed by **full path**
with tokens and access-per-Ktoken; sessions table filtered to 7d/14d/30d/All.

**Session deep-dive** — click any session-id in the table. Shows cost, duration,
cache hit %, repeat-read %, sequential-tool %, total tools (with p95 baseline),
waste score; per-category waste findings with evidence + "WHAT TO CHANGE" fix;
cache efficiency bars + per-turn cache-hit line; top-10 tool usage; turn-by-turn
cost bar chart; expandable turn table.

## After running

Summarize for the user: 1) total cost and top 3 waste categories, 2) 1–2 projects
with the highest waste score, 3) the one change with biggest expected savings
(pick the category with largest `waste_category_totals × savings_rate` product).
Cross-reference **token-efficiency** skill for the fix playbook.
