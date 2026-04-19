---
name: improve
description: One-shot — dispatch the token-efficiency-analyzer agent to analyze, classify, prioritize, and interactively apply improvements
model: inherit
---

# /improve — out-of-the-box token efficiency loop

The out-of-the-box entrypoint for context-os. One command: analyze sessions, classify + prioritize waste, ask the user which improvements to implement, then implement the selected ones.

## Step 0 — preflight

Run `context-os doctor` before anything else. If any check FAILs, surface the printed `fix:` lines
to the user (especially cc-lens and ccusage — `/improve` depends on both) and ask whether to proceed
with **degraded analysis** or **stop** and fix the environment first. Only continue once the user chooses.

## What this does

1. Verifies `npx cc-lens` is running (starts it if needed).
2. Runs `context-os limits` so the user sees current rate-limit state before we start.
3. Dispatches the **token-efficiency-analyzer** subagent, which:
   - Runs `context-os cc-lens analyze`
   - Inspects the top 8–12 forensic session targets
   - Clusters findings into root-cause patterns
   - Writes `/tmp/token-analysis-review.md` + `/tmp/token-analysis-options.json`
   - Launches the interactive review server on :3118
4. User picks improvements; agent implements the selected items.

## Invocation

Launch the `token-efficiency-analyzer` agent with the prompt:

> Run the full token efficiency loop per your 8-phase workflow. Before Phase 1, run `context-os limits` and include the active-window utilization and weekly Sonnet % in the executive summary of `/tmp/token-analysis-review.md`. Then proceed normally. When the interactive review server is up, stop and tell the user to open http://localhost:3118.

## Why separate from /cc-lens

- `/cc-lens` = one-step action (generate paste-prompt or per-project edits).
- `/improve` = the full out-of-box loop including rate-limit context and interactive selection.
- `/audit` = graph + token audit HTML bundle (diagnostic artifact, not a loop).

Prefer `/improve` as the default entrypoint for new users.
