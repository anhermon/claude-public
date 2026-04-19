# context-os — Alignment Feedback Report

Living document produced while exercising the plugin as an AI agent. Updated iteratively as the plugin evolves toward its declared intent.

## Declared Intent

> A complete suite of tools for analysing agent sessions for effective token/context usage. Full human observability via dashboards + AI-agent-friendly surface (CLI / skills / agents). Out-of-the-box: user installs, runs a single command, and an agent analyzes usage, classifies + prioritizes improvements, and asks which to implement.

## Iteration 01 — 2026-04-19 — Baseline audit

### Inventory (v2.1.1)

- **Commands**: `/quickstart`, `/ingest`, `/audit`, `/ingest-history`, `/cc-lens`
- **Agents**: `token-efficiency-analyzer` (deep 8-phase workflow)
- **Skills**: cc-lens, ccusage, context-audit, context-gap-analysis, context-ingest, context-os-basics, context-os-cli, epistemic-context-grounding, token-efficiency
- **CLI (`context-os`)**: graph health/query/show, sessions list/replay, heat, ingest, audit (HTML), cc-lens, ccusage passthrough
- **Dashboard**: third-party `cc-lens` + local HTML bundle from `context-os audit`

### Gaps vs. Intent

| # | Gap | Severity | Evidence |
|---|---|---|---|
| G1 | No **single-command entrypoint** that dispatches the analyzer end-to-end (analyze → classify → prioritize → interactive select → implement). User has to know to invoke the agent by trigger phrase or stitch `/cc-lens` + agent. | HIGH | README table lists 5 commands; none are "run the whole thing". Agent exists but isn't wired to a slash command. |
| G2 | **No rate-limit observability.** Users cannot see where Sonnet-weekly / total-weekly / 5-hour session quotas went. ccusage exposes `blocks` but plugin doesn't surface a rate-limit-aware view for humans or agents. | HIGH (user-explicit) | Neither the audit HTML nor cc-lens summarizes "% of weekly Sonnet cap used" or per-5h-block breakdown by model. |
| G3 | Dashboard fragmented — cc-lens (third-party, session forensics) and `context-os audit` HTML (graph + summary) are separate artifacts. No unified "cockpit". | MEDIUM | Two separate pages; user must cross-reference. |
| G4 | No **self-improvement loop skill** — plugin doesn't ship the meta-pattern for validating its own outputs against intent. | MEDIUM | No `align-to-intent` or equivalent in `skills/`. |
| G5 | Install friction — Python pkg + Node (`npx`) + optional plugin env var + optional hooks snippet. README lists 5 install paths. Out-of-box promise weak. | LOW–MED | README install section spans ~40 lines of branching. |
| G6 | `audit.md` command and `cc-lens.md` command duplicate scope (both drive remediation paths). User confusion likely. | LOW | Both produce prioritized fixes; entry points unclear. |
| G7 | Agent workflow is solid but long (8 phases). No "lite" mode for quick recurring checks (daily ≤5min). | LOW | `token-efficiency-analyzer.md` 250+ lines, assumes heavy pass. |

### Wins (keep)

- `token-efficiency-analyzer` phase structure is excellent — evidence-based, pattern-library-driven.
- `interactive-review-server.py` + feedback.json loop is exactly the "ask user which to implement" pattern the intent calls for.
- `token-efficiency` skill is a genuinely usable knowledge base.
- CLI is stdlib-first, no heavy deps.

## Iteration 01 — Actions taken

1. **[G2]** Added `context-os limits` CLI + `/context-os:limits` command. Reads `npx ccusage blocks --json` and aggregates:
   - Current 5-hour session window: tokens, cost, % of typical cap, model mix (Sonnet vs Opus vs Haiku).
   - Rolling 7-day: total cost, Sonnet-only cost, estimated weekly-cap utilisation.
   - Machine-readable JSON mode for agent consumption.
2. **[G1]** Added `/context-os:improve` — single command that loads the `token-efficiency-analyzer` agent directly, so "install → `/context-os:improve` → done" is the OOTB path.
3. **[G4]** Added `align-to-intent` skill — reusable protocol: (interview user on intent) → (use the tool) → (write feedback against intent) → (refine) → (loop). Referenced from this report so the plugin dogfoods its own alignment check.

### Not yet addressed (queued)

- **G3** unified cockpit — defer; merging `generate_dashboard.py` HTML with cc-lens requires iframe/proxy work.
- **G5** install simplification — defer; would need a single installer script that handles Python + Node together.
- **G6** audit/cc-lens overlap — defer; suggest renaming `audit` → `graph-audit` in a later iteration.
- **G7** lite-mode daily check — partially addressed by `context-os limits` (fast) but no dedicated lite analyzer yet.

## Iteration 02 — 2026-04-19 — Dogfood new surfaces

### Exercise

- Ran `context-os limits` on real ccusage data. Output is coherent:
  - Active 5h: $1.87 / ~$35 cap (5.3%), projection 35.33 / 235min remaining.
  - Weekly 7d: $151.26 total (54% of ~$280 cap); **Sonnet $147.38 = 105% of ~$140 cap** — over estimated Sonnet weekly cap.
  - Recent blocks show 2026-04-17 was a $113 spike day across 5 back-to-back blocks.
- Report correctly surfaces the single most actionable signal: Sonnet-weekly overrun. Human-readable and agent-consumable (JSON).

### New observations

| # | Finding | Severity | Action |
|---|---|---|---|
| O1 | Caps are estimates; user has no easy way to calibrate to their actual plan. | MEDIUM | Queued: add `context-os limits calibrate` that asks user their plan and writes defaults to `~/.config/context-os/caps.json`. |
| O2 | `limits` output does NOT correlate spending to *sessions* (which cc-lens does). Bridging "you burned 105% of Sonnet cap" with "here are the 3 sessions that caused it" closes the loop. | HIGH | Queued: add per-session cost join — weekly breakdown by top session IDs. |
| O3 | No dashboard widget for rate limits yet — only CLI. Intent said "dashboards" (plural, human observability). | MEDIUM | Queued: render `limits` panel into `generate_dashboard.py` HTML. |
| O4 | `/improve` relies on `token-efficiency-analyzer` trigger phrases — verified the agent file loads Phase 0 correctly. | — | Resolved. |

### Actions taken this iteration

- Wired `Phase 0: Rate-limit snapshot` into `token-efficiency-analyzer.md` so the agent always reports rate-limit state at the top of `/tmp/token-analysis-review.md`.
- Published `/context-os:improve` as the single-command OOTB entrypoint.
- Verified `/context-os:limits` slash command + `context-os limits` CLI.
- Added `align-to-intent` skill — this report is its first artifact.

### Alignment status

| Intent claim | Status |
|---|---|
| "complete suite for analyzing sessions for token/context usage" | ✅ cc-lens + ccusage + limits + analyzer agent |
| "full human observability with dashboards" | ⚠ partial — CLI + cc-lens page; unified dashboard widget for limits queued (O3) |
| "AI-agent friendly: cli / skills / agents" | ✅ |
| "single command dispatch an agent that analyzes / classifies / prioritizes / asks which to implement" | ✅ `/context-os:improve` |
| "rate-limit visibility (weekly Sonnet / total weekly / 5h)" | ✅ CLI, ⚠ dashboard pending |

**Next iteration target:** O2 (session-level attribution of weekly Sonnet spend) — highest leverage because it answers *why* the cap was hit, not just that it was.

## Iteration 03 — 2026-04-19 — Fresh-install feedback

### User feedback

Another user ran a fresh install and reported:

1. `/audit` "doesn't generate a dashboard — it created CLI-like output in HTML, which is wrong." (Confirmed — the old `cmd_audit` dumped JSON + ccusage text into `<pre>` blocks.)
2. Install of cc-lens / ccusage failed silently; the plugin proceeded to "analyze sessions without proper analytics" — hollow output, no warning to the user.
3. On caps in the `limits` command: hardcoded defaults ($140/$280/$35) are untrustworthy when Anthropic doesn't publish per-plan limits — "read and use actual Claude.ai usage, don't use defaults."

### Actions taken (three subagents in parallel)

- **Dashboard rewrite** — `cmd_audit` now renders a dark-theme styled dashboard: CSS grid, 4 cards (Rate limits, Graph health, ccusage bars, cc-lens status), colored `vs_normal` badges, pure-HTML bar chart, no `<pre>` tags. When ccusage/cc-lens are unavailable, the card becomes a visible warn-card with a "Run `context-os doctor`" CTA instead of silently skipping. Top-level JSON payload now includes `rate_limits` + `dependencies: {ccusage, cc_lens}`.
- **Baselines, not caps** — `limits.py` no longer has any hardcoded cap constants or env-var overrides. It computes personal baselines from the user's own trailing 90 days of ccusage history — weekly rolling windows (total / sonnet / opus) and 5h block costs — then expresses current usage as `vs_normal ∈ {below normal, elevated, high, record}` with p50/p95/max context. Graceful fallback with `"baseline": "insufficient_history"` if <14 days.
- **`context-os doctor`** — new preflight command that checks Python, Node/npx, ccusage (`npx --yes ccusage@latest --version`), cc-lens reachability on 3001–3010, CLI on PATH, and plugin root. Supports `--format json`. Exit 0 on clean, 2 on failure. `/context-os:doctor` slash command, and `/audit` + `/improve` now have a mandatory **Step 0 — preflight** that runs doctor and asks proceed-vs-stop on failure.

### Alignment status (after this iteration)

| Intent claim | Status |
|---|---|
| "complete suite for analyzing sessions for token/context usage" | ✅ |
| "full human observability with dashboards" | ✅ real styled dashboard (4 cards, colored state) |
| "AI-agent friendly: cli / skills / agents" | ✅ JSON mode for every command |
| "single command dispatch an agent that analyzes / classifies / prioritizes / asks which to implement" | ✅ `/context-os:improve` |
| "rate-limit visibility (weekly Sonnet / total weekly / 5h)" | ✅ baselined against user's own history, no fake caps |
| "out-of-the-box — user installs and runs a single command" | ✅ `/doctor` guards first-run failures; `/improve` checks before running |

### Current user snapshot (2026-04-19)

- Active 5h: $7.24 — below normal (8.1% of personal p95)
- Weekly 7d total: $156.65 — **elevated** (p50=$151.20, p95=$761.98)
- Weekly Sonnet: $147.38 — **elevated** (p50=$101.24, p95=$588.01)
- Weekly Opus: $7.26 — below normal
- 18 days of history → full baselines active (≥14 days)

### Queued for iteration 04

- O2 (still) — session-level attribution of *why* Sonnet is elevated this week.
- Calibrate dashboard: add sparkline of trailing 14-day total to the rate-limits card.
- Wire `/doctor` into the `token-efficiency-analyzer` agent's Phase 0 alongside `/limits`.

