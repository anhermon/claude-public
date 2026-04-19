#!/usr/bin/env python3
"""Rate-limit observability: 5-hour session blocks + weekly per-model usage.

Wraps `npx ccusage blocks --json` and `npx ccusage daily --json --breakdown`
and reshapes the output into a personal-baseline-aware view.

Rather than comparing to hardcoded caps (which Anthropic doesn't publish and
which differ per plan), this derives baselines from the user's own trailing
90 days of ccusage history and expresses current usage as deviation from
their personal normal (p50/p95/max).
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from typing import Any


HISTORY_DAYS = 90
MIN_HISTORY_DAYS = 14


def _npx() -> str:
    npx = shutil.which("npx")
    if not npx:
        print("npx not found; install Node.js", file=sys.stderr)
        sys.exit(1)
    return npx


def _run_ccusage(args: list[str]) -> dict[str, Any]:
    cmd = [_npx(), "--yes", "ccusage@latest", *args, "--json"]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if r.returncode != 0:
        print(f"ccusage failed: {r.stderr[:400]}", file=sys.stderr)
        sys.exit(r.returncode)
    try:
        return json.loads(r.stdout)
    except json.JSONDecodeError as e:
        print(f"ccusage returned non-JSON: {e}", file=sys.stderr)
        sys.exit(1)


def _model_family(name: str) -> str:
    n = (name or "").lower()
    if "opus" in n:
        return "opus"
    if "sonnet" in n:
        return "sonnet"
    if "haiku" in n:
        return "haiku"
    return "other"


def _blocks() -> list[dict[str, Any]]:
    data = _run_ccusage(["blocks"])
    return [b for b in data.get("blocks", []) if not b.get("isGap")]


def _daily_breakdown() -> list[dict[str, Any]]:
    data = _run_ccusage(["daily", "--breakdown"])
    return data.get("daily", [])


def _active_block(blocks: list[dict[str, Any]]) -> dict[str, Any] | None:
    for b in blocks:
        if b.get("isActive"):
            return b
    return None


def _parse_date(s: str) -> datetime | None:
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00")).replace(tzinfo=timezone.utc) \
            if "T" in s else datetime.fromisoformat(s).replace(tzinfo=timezone.utc)
    except (ValueError, AttributeError):
        return None


def _percentile(sorted_vals: list[float], pct: float) -> float:
    """Linear-interpolation percentile. `pct` in [0, 100]."""
    if not sorted_vals:
        return 0.0
    if len(sorted_vals) == 1:
        return sorted_vals[0]
    k = (len(sorted_vals) - 1) * (pct / 100.0)
    lo = int(k)
    hi = min(lo + 1, len(sorted_vals) - 1)
    frac = k - lo
    return sorted_vals[lo] * (1 - frac) + sorted_vals[hi] * frac


def _stats(vals: list[float]) -> dict[str, float]:
    if not vals:
        return {"mean": 0.0, "p50": 0.0, "p95": 0.0, "max": 0.0, "n": 0}
    s = sorted(vals)
    return {
        "mean": round(sum(s) / len(s), 2),
        "p50": round(_percentile(s, 50), 2),
        "p95": round(_percentile(s, 95), 2),
        "max": round(s[-1], 2),
        "n": len(s),
    }


def _daily_aggregates(daily: list[dict[str, Any]], cutoff: datetime) -> list[dict[str, Any]]:
    """Return [{date, total, sonnet, opus, ...}] for days >= cutoff, chronologically."""
    rows: list[dict[str, Any]] = []
    for d in daily:
        dt = _parse_date(d.get("date", ""))
        if dt is None or dt < cutoff:
            continue
        fam: dict[str, float] = {"sonnet": 0.0, "opus": 0.0, "haiku": 0.0, "other": 0.0}
        for mb in d.get("modelBreakdowns", []):
            f = _model_family(mb.get("modelName", ""))
            fam[f] = fam.get(f, 0.0) + float(mb.get("cost", 0))
        rows.append({
            "date": d["date"],
            "dt": dt,
            "total": float(d.get("totalCost", 0)),
            "total_tokens": int(d.get("totalTokens", 0)),
            **fam,
        })
    rows.sort(key=lambda r: r["dt"])
    return rows


def _rolling_7d_windows(rows: list[dict[str, Any]]) -> list[dict[str, float]]:
    """For each day d in rows, compute sum over [d-6d, d] inclusive (if that window
    has any data). Yields one window per day that has a fully-covered 7-day span."""
    if not rows:
        return []
    by_date: dict[str, dict[str, float]] = {r["date"]: r for r in rows}
    first_dt = rows[0]["dt"]
    last_dt = rows[-1]["dt"]
    windows: list[dict[str, float]] = []
    cur = first_dt + timedelta(days=6)
    while cur <= last_dt:
        tot = son = opu = 0.0
        for i in range(7):
            d = (cur - timedelta(days=i)).date().isoformat()
            r = by_date.get(d)
            if r:
                tot += r["total"]
                son += r["sonnet"]
                opu += r["opus"]
        windows.append({"total": tot, "sonnet": son, "opus": opu})
        cur += timedelta(days=1)
    return windows


def _compute_baselines(daily: list[dict[str, Any]], blocks: list[dict[str, Any]]) -> dict[str, Any]:
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=HISTORY_DAYS)
    rows = _daily_aggregates(daily, cutoff)

    days_n = len(rows)
    if days_n < MIN_HISTORY_DAYS:
        return {"status": "insufficient_history", "days_available": days_n, "min_required": MIN_HISTORY_DAYS}

    windows = _rolling_7d_windows(rows)
    weekly_total = [w["total"] for w in windows]
    weekly_sonnet = [w["sonnet"] for w in windows]
    weekly_opus = [w["opus"] for w in windows]

    block_costs: list[float] = []
    for b in blocks:
        if b.get("isActive") or b.get("isGap"):
            continue
        dt = _parse_date(b.get("startTime", ""))
        if dt is None or dt < cutoff:
            continue
        block_costs.append(float(b.get("costUSD", 0)))

    return {
        "status": "ok",
        "days_available": days_n,
        "history_days": HISTORY_DAYS,
        "weekly_total": _stats(weekly_total),
        "weekly_sonnet": _stats(weekly_sonnet),
        "weekly_opus": _stats(weekly_opus),
        "block_5h": _stats(block_costs),
    }


def _vs_normal(current: float, stats: dict[str, float]) -> str:
    p50 = stats.get("p50", 0.0)
    p95 = stats.get("p95", 0.0)
    mx = stats.get("max", 0.0)
    if current > mx:
        return "record"
    if current > p95:
        return "high"
    if current > p50:
        return "elevated"
    return "below normal"


def _pct(num: float, denom: float) -> float | None:
    if denom <= 0:
        return None
    return round(100.0 * num / denom, 1)


def _format_ts(s: str) -> str:
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00")).strftime("%Y-%m-%d %H:%M UTC")
    except Exception:  # noqa: BLE001
        return s


def _weekly_current(daily: list[dict[str, Any]]) -> dict[str, Any]:
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=7)
    total_cost = 0.0
    by_family: dict[str, float] = {"sonnet": 0.0, "opus": 0.0, "haiku": 0.0, "other": 0.0}
    total_tokens = 0
    days_included: list[str] = []
    for d in daily:
        dt = _parse_date(d.get("date", ""))
        if dt is None or dt < cutoff:
            continue
        days_included.append(d["date"])
        total_cost += float(d.get("totalCost", 0))
        total_tokens += int(d.get("totalTokens", 0))
        for mb in d.get("modelBreakdowns", []):
            fam = _model_family(mb.get("modelName", ""))
            by_family[fam] = by_family.get(fam, 0.0) + float(mb.get("cost", 0))
    return {
        "total_cost_usd": round(total_cost, 2),
        "total_tokens": total_tokens,
        "cost_by_family_usd": {k: round(v, 2) for k, v in by_family.items()},
        "days_included": sorted(days_included),
    }


def _with_baseline_context(current_val: float, baseline_stats: dict[str, float] | None) -> dict[str, Any]:
    out: dict[str, Any] = {"cost_usd": round(current_val, 2)}
    if not baseline_stats or baseline_stats.get("n", 0) == 0:
        out["baseline"] = "insufficient_history"
        return out
    out["baseline"] = {k: baseline_stats[k] for k in ("mean", "p50", "p95", "max", "n") if k in baseline_stats}
    out["pct_of_personal_p95"] = _pct(current_val, baseline_stats.get("p95", 0.0))
    out["pct_of_personal_max"] = _pct(current_val, baseline_stats.get("max", 0.0))
    out["vs_normal"] = _vs_normal(current_val, baseline_stats)
    return out


def compute_report() -> dict[str, Any]:
    blocks = _blocks()
    daily = _daily_breakdown()
    active = _active_block(blocks)
    recent_blocks = blocks[-8:]

    baselines = _compute_baselines(daily, blocks)
    insufficient = baselines.get("status") == "insufficient_history"

    active_view = None
    if active:
        cost = float(active.get("costUSD", 0))
        bstats = None if insufficient else baselines.get("block_5h")
        ctx = _with_baseline_context(cost, bstats)
        active_view = {
            "start": _format_ts(active.get("startTime", "")),
            "end": _format_ts(active.get("endTime", "")),
            "cost_usd": round(cost, 2),
            "tokens": int(active.get("totalTokens", 0)),
            "models": active.get("models", []),
            "burn_rate": active.get("burnRate"),
            "projection": active.get("projection"),
            **{k: v for k, v in ctx.items() if k != "cost_usd"},
        }

    weekly = _weekly_current(daily)
    if insufficient:
        weekly["baseline"] = "insufficient_history"
    else:
        weekly["total"] = _with_baseline_context(weekly["total_cost_usd"], baselines.get("weekly_total"))
        weekly["sonnet"] = _with_baseline_context(
            weekly["cost_by_family_usd"].get("sonnet", 0.0), baselines.get("weekly_sonnet")
        )
        weekly["opus"] = _with_baseline_context(
            weekly["cost_by_family_usd"].get("opus", 0.0), baselines.get("weekly_opus")
        )

    return {
        "active_5h_window": active_view,
        "weekly_rolling_7d": weekly,
        "baselines": baselines,
        "recent_5h_blocks": [
            {
                "start": _format_ts(b.get("startTime", "")),
                "cost_usd": round(float(b.get("costUSD", 0)), 2),
                "tokens": int(b.get("totalTokens", 0)),
                "models": b.get("models", []),
                "active": b.get("isActive", False),
            }
            for b in recent_blocks
        ],
    }


def _fmt_baseline(stats: dict[str, float]) -> str:
    return f"p50=${stats.get('p50', 0):.2f} p95=${stats.get('p95', 0):.2f} max=${stats.get('max', 0):.2f} (n={stats.get('n', 0)})"


def render_text(report: dict[str, Any]) -> str:
    lines: list[str] = []
    baselines = report.get("baselines", {})
    insufficient = baselines.get("status") == "insufficient_history"

    lines.append("=== Active 5-hour window ===")
    a = report.get("active_5h_window")
    if a:
        lines.append(f"  {a['start']} -> {a['end']}")
        extra = ""
        if "vs_normal" in a:
            extra = f"  [{a['vs_normal']}]"
            if a.get("pct_of_personal_p95") is not None:
                extra += f" ({a['pct_of_personal_p95']}% of personal p95)"
        lines.append(f"  cost=${a['cost_usd']:.2f}{extra}  tokens={a['tokens']:,}")
        if not insufficient and isinstance(a.get("baseline"), dict):
            lines.append(f"  your 5h block baseline: {_fmt_baseline(a['baseline'])}")
        lines.append(f"  models={a['models']}")
        if a.get("projection"):
            lines.append(f"  projection: {a['projection']}")
    else:
        lines.append("  (no active block — idle)")
    lines.append("")

    lines.append("=== Weekly rolling 7d ===")
    w = report["weekly_rolling_7d"]
    fam = w["cost_by_family_usd"]
    if insufficient:
        lines.append(f"  total=${w['total_cost_usd']:.2f}  tokens={w['total_tokens']:,}")
        lines.append(
            f"  by_model: opus=${fam.get('opus', 0):.2f}  "
            f"sonnet=${fam.get('sonnet', 0):.2f}  haiku=${fam.get('haiku', 0):.2f}"
        )
        lines.append(
            f"  baseline: insufficient_history "
            f"({baselines.get('days_available', 0)}/{baselines.get('min_required', MIN_HISTORY_DAYS)} days)"
        )
    else:
        wt = w["total"]
        lines.append(
            f"  total=${wt['cost_usd']:.2f}  [{wt['vs_normal']}]  tokens={w['total_tokens']:,}"
        )
        if isinstance(wt.get("baseline"), dict):
            lines.append(f"    your 90d weekly-total baseline: {_fmt_baseline(wt['baseline'])}")
        ws = w["sonnet"]
        lines.append(
            f"  sonnet=${ws['cost_usd']:.2f}  [{ws['vs_normal']}]"
        )
        if isinstance(ws.get("baseline"), dict):
            lines.append(f"    your 90d weekly-sonnet baseline: {_fmt_baseline(ws['baseline'])}")
        wo = w["opus"]
        lines.append(
            f"  opus=${wo['cost_usd']:.2f}  [{wo['vs_normal']}]"
        )
        if isinstance(wo.get("baseline"), dict):
            lines.append(f"    your 90d weekly-opus baseline: {_fmt_baseline(wo['baseline'])}")
        lines.append(f"  haiku=${fam.get('haiku', 0):.2f}  other=${fam.get('other', 0):.2f}")
    lines.append(f"  days: {', '.join(w['days_included']) or '(none)'}")
    lines.append("")

    lines.append("=== Recent 5-hour blocks ===")
    for b in report["recent_5h_blocks"]:
        mark = "*" if b["active"] else " "
        mlist = ",".join(b["models"]) or "-"
        lines.append(f"  {mark} {b['start']}  ${b['cost_usd']:>6.2f}  {b['tokens']:>12,} tok  [{mlist}]")
    lines.append("")

    if insufficient:
        lines.append(
            f"Baselines unavailable: only {baselines.get('days_available', 0)} days of history "
            f"(need >= {MIN_HISTORY_DAYS}). Showing absolute numbers."
        )
    else:
        lines.append(
            f"Baselines computed from your trailing {baselines.get('history_days', HISTORY_DAYS)} days "
            f"of ccusage history ({baselines.get('days_available', 0)} days with data)."
        )
    return "\n".join(lines)


def cmd_limits(args) -> int:
    report = compute_report()
    if getattr(args, "format", "text") == "json":
        print(json.dumps(report, indent=2))
    else:
        print(render_text(report))
    return 0
