---
name: limits
description: Rate-limit observability — 5-hour session window + weekly per-model usage vs caps
model: inherit
---

# /limits — Rate-limit view

Show where rate-limit budget is being spent (both human- and agent-readable).

## What it shows

- **Active 5-hour window:** cost, tokens, models, % of configured 5h cap, projection to end of window.
- **Weekly rolling 7d:** total cost, cost split by model family (Opus / Sonnet / Haiku), % of weekly total cap, % of weekly Sonnet cap.
- **Recent 5h blocks:** last ~8 session windows so you can spot the outliers.

## How to run

```bash
context-os limits                    # pretty text
context-os limits --format json      # for agents
```

## Caps

Caps are **estimates**; tune to your plan via env vars:

- `CONTEXT_OS_5H_CAP_USD` (default 35)
- `CONTEXT_OS_WEEKLY_CAP_USD` (default 280)
- `CONTEXT_OS_WEEKLY_SONNET_CAP_USD` (default 140)

## Agent usage

When asked about rate limits, quota, or "where did my usage go this week", call:

```bash
context-os limits --format json
```

Then interpret the report:

- If `weekly_rolling_7d.pct_of_weekly_sonnet_cap` > 80 → warn the user and recommend switching to Opus/Haiku for non-coding work.
- If `active_5h_window.projection.totalCost` will exceed the 5h cap → suggest `/compact`, deferring non-essentials, or pausing.
- Cross-reference with `context-os cc-lens analyze` to explain which *sessions* caused the spend — rate limits tell you how much, cc-lens tells you why.

## Exit

After running, summarize in 3 lines:
1. Active window utilization (% of 5h cap).
2. Weekly Sonnet utilization (% of weekly cap).
3. Top 1 actionable recommendation if any threshold exceeded.
