#!/usr/bin/env python3
"""
cc-lens analyzer — fetches data from cc-lens API, scores sessions using
percentile-based thresholds computed from the actual dataset, and writes a
JSON spec file consumed by the dashboard generator.

Usage:
    python analyze.py [--top-n N] [--sort-by cost|tokens] [--project SLUG]
                      [--session ID_PREFIX] [--output PATH]
"""

import argparse
import json
import sys
import urllib.request
from collections import defaultdict
from datetime import datetime, timedelta

BASE_URL = "http://localhost:3001"

# ─── Waste categories ──────────────────────────────────────────────────────────

WASTE_CATEGORIES = [
    "context_bloat",
    "cache_inefficiency",
    "tool_hammering",
    "compaction_absence",
    "parallel_sprawl",
    "interruption_loops",
    "thinking_waste",
]

CATEGORY_LABELS = {
    "context_bloat":      "Context Bloat",
    "cache_inefficiency": "Cache Inefficiency",
    "tool_hammering":     "Tool Hammering",
    "compaction_absence": "Compaction Absence",
    "parallel_sprawl":    "Parallel Sprawl",
    "interruption_loops": "Interruption Loops",
    "thinking_waste":     "Thinking Waste",
}

CATEGORY_COLORS = {
    "context_bloat":      "#ef4444",
    "cache_inefficiency": "#f97316",
    "tool_hammering":     "#6366f1",
    "compaction_absence": "#06b6d4",
    "parallel_sprawl":    "#8b5cf6",
    "interruption_loops": "#ec4899",
    "thinking_waste":     "#84cc16",
}

CATEGORY_RECOMMENDATIONS = {
    "context_bloat":      "Break into smaller focused sessions, run /compact when context feels large",
    "cache_inefficiency": "Keep system prompts stable across turns, avoid randomizing tool descriptions",
    "tool_hammering":     "Batch shell commands into fewer calls, use Agent for exploratory file searches",
    "compaction_absence": "Add /compact to your workflow for sessions >45 min, or configure auto-compaction in settings",
    "parallel_sprawl":    "Consolidate work into fewer focused sessions; avoid multiple terminal windows on the same project",
    "interruption_loops": "Write clearer prompts upfront, use TodoWrite for shared task state, reduce task scope per session",
    "thinking_waste":     "Reserve extended thinking for complex reasoning; disable for routine file edits or searches",
}

CATEGORY_FIXES = {
    "context_bloat":      "Break into smaller focused sessions, run /compact when context feels large.",
    "cache_inefficiency": "Keep system prompts stable, avoid randomizing tool descriptions, use stable context blocks.",
    "tool_hammering":     "Batch shell commands into fewer calls, use Agent for exploratory file searches.",
    "compaction_absence": "Add /compact to your workflow for sessions >45 min, or configure auto-compaction.",
    "parallel_sprawl":    "Consolidate work into fewer focused sessions, avoid multiple terminal windows simultaneously.",
    "interruption_loops": "Write clearer prompts upfront, use TodoWrite for shared task state, reduce scope per session.",
    "thinking_waste":     "Reserve extended thinking for complex reasoning; disable for routine file edits or searches.",
}


# ─── API helpers ───────────────────────────────────────────────────────────────

def api_get(path, timeout=60):
    """GET from the cc-lens API. Returns parsed JSON or None on failure."""
    url = f"{BASE_URL}{path}"
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:
            return json.loads(r.read())
    except Exception as e:
        print(f"[ERROR] GET {path}: {e}", file=sys.stderr)
        return None


# ─── Percentile computation ────────────────────────────────────────────────────

def percentile(values, p):
    """Compute the p-th percentile (0–100) of a list using linear interpolation."""
    if not values:
        return 0
    sorted_vals = sorted(v for v in values if v is not None)
    if not sorted_vals:
        return 0
    n = len(sorted_vals)
    if n == 1:
        return sorted_vals[0]
    idx = (p / 100.0) * (n - 1)
    lo = int(idx)
    hi = min(lo + 1, n - 1)
    frac = idx - lo
    return sorted_vals[lo] + frac * (sorted_vals[hi] - sorted_vals[lo])


def rank_percentile_of(value, sorted_values):
    """Return 0–100 percentile rank of value within a pre-sorted list."""
    if not sorted_values:
        return 50
    n = len(sorted_values)
    count_below = sum(1 for v in sorted_values if v < value)
    return round(count_below / n * 100)


def compute_thresholds(sessions):
    """
    Compute percentile thresholds from the actual session dataset.
    Falls back to known real-world values when the dataset is too small (<10 qualifying samples).

    Returns a dict with keys used throughout score_session().
    """
    # Cache reuse ratios — only for sessions with meaningful cache creation (>50K tokens)
    cache_ratios = []
    for s in sessions:
        cc = s.get("cache_creation_input_tokens", 0) or 0
        cr = s.get("cache_read_input_tokens", 0) or 0
        if cc > 50_000:
            cache_ratios.append(cr / cc)

    # Max single-tool call count per session
    max_tools = []
    for s in sessions:
        tc = s.get("tool_counts", {}) or {}
        if tc:
            max_tools.append(max(tc.values()))

    # Cost values (positive only)
    costs = [s.get("estimated_cost", 0) or 0 for s in sessions if (s.get("estimated_cost") or 0) > 0]

    # Duration values (positive only)
    durations = [s.get("duration_minutes", 0) or 0 for s in sessions if (s.get("duration_minutes") or 0) > 0]

    # Cache creation token counts (positive only)
    cache_creations = [
        s.get("cache_creation_input_tokens", 0) or 0
        for s in sessions
        if (s.get("cache_creation_input_tokens") or 0) > 0
    ]

    def _p(vals, pct, fallback):
        return percentile(vals, pct) if len(vals) >= 10 else fallback

    return {
        # Cache reuse ratio percentiles (ratio = cache_read / cache_create)
        "cache_ratio_p10":    _p(cache_ratios, 10,  4.6),
        "cache_ratio_p25":    _p(cache_ratios, 25,  9.5),
        "cache_ratio_median": _p(cache_ratios, 50, 15.8),
        "cache_ratio_p75":    _p(cache_ratios, 75, 25.4),

        # Max single-tool call count percentiles
        "max_tool_p25":       _p(max_tools, 25,   14),
        "max_tool_p50":       _p(max_tools, 50,   28),
        "max_tool_p75":       _p(max_tools, 75,   54),
        "max_tool_p95":       _p(max_tools, 95,  143),

        # Cost percentiles (USD)
        "cost_p25":           _p(costs, 25,   5.4),
        "cost_p50":           _p(costs, 50,  11.0),
        "cost_p75":           _p(costs, 75,  24.3),
        "cost_p95":           _p(costs, 95,  86.2),

        # Duration percentiles (minutes)
        "duration_p25":       _p(durations, 25,    3.6),
        "duration_p50":       _p(durations, 50,   12.8),
        "duration_p75":       _p(durations, 75,  156.0),
        "duration_p95":       _p(durations, 95, 2998.0),

        # Cache creation token count percentiles
        "cache_create_p50":   _p(cache_creations, 50,   201_000),
        "cache_create_p75":   _p(cache_creations, 75,   404_000),
        "cache_create_p95":   _p(cache_creations, 95, 1_450_000),

        # Raw sorted lists for rank-percentile lookups inside score_session
        "_sorted_max_tools":    sorted(max_tools),
        "_sorted_cache_ratios": sorted(cache_ratios),

        "n": len(sessions),
    }


# ─── Per-session scoring ───────────────────────────────────────────────────────

def score_session(s, thresholds):
    """
    Score one session across all waste categories using calibrated
    percentile-based thresholds. Returns:
        scores            — dict[category -> 0-100]
        flags             — dict[category -> list[str]]
        evidence          — dict[category -> {finding, recommendation}]
        total_score       — int (average of non-zero category scores)
        active_categories — list[(category, score)] sorted desc
    """
    scores = {c: 0 for c in WASTE_CATEGORIES}
    flags  = {c: [] for c in WASTE_CATEGORIES}
    evidence = {}

    cache_create   = s.get("cache_creation_input_tokens", 0) or 0
    cache_read     = s.get("cache_read_input_tokens", 0) or 0
    output_tok     = s.get("output_tokens", 0) or 0
    duration       = s.get("duration_minutes", 0) or 0
    interruptions  = s.get("user_interruptions", 0) or 0
    has_compaction = bool(s.get("has_compaction", False))
    has_thinking   = bool(s.get("has_thinking", False))
    tool_counts    = s.get("tool_counts", {}) or {}
    # Use assistant_message_count if available, fall back to turn_count
    assistant_msgs = s.get("assistant_message_count") or s.get("turn_count") or 1
    assistant_msgs = max(assistant_msgs, 1)

    max_single_tool = max(tool_counts.values(), default=0)
    top_tool_name   = max(tool_counts, key=tool_counts.get) if tool_counts else "unknown"

    t = thresholds  # shorthand

    # ── 1. TOOL HAMMERING ─────────────────────────────────────────────────────
    # Measures whether a single tool is called an unusually high number of times.
    p25 = t["max_tool_p25"]
    p50 = t["max_tool_p50"]
    p75 = t["max_tool_p75"]
    p95 = t["max_tool_p95"]

    if max_single_tool > 0:
        if max_single_tool >= p95:
            # Top 5%: score 85–100
            excess_ratio = min((max_single_tool - p95) / max(p95, 1), 1.0)
            th_score = int(85 + excess_ratio * 15)
            scores["tool_hammering"] = min(100, th_score)
            # Compute approximate percentile rank for the finding string
            sorted_mt = t.get("_sorted_max_tools", [])
            rank_pct = rank_percentile_of(max_single_tool, sorted_mt)
            top_pct = 100 - rank_pct
            flags["tool_hammering"].append(
                f"{top_tool_name} called {max_single_tool}× "
                f"(dataset p95={p95:.0f}×, median={p50:.0f}×)"
            )
            evidence["tool_hammering"] = {
                "finding": (
                    f"{top_tool_name} called {max_single_tool}× "
                    f"(dataset p95={p95:.0f}×, you are in the top {max(top_pct, 1):.0f}%)"
                ),
                "recommendation": CATEGORY_RECOMMENDATIONS["tool_hammering"],
            }
        elif max_single_tool >= p75:
            # p75–p95: score 40–84
            span = max(p95 - p75, 1)
            frac = (max_single_tool - p75) / span
            th_score = int(40 + frac * 44)
            scores["tool_hammering"] = min(84, th_score)
            flags["tool_hammering"].append(
                f"{top_tool_name} called {max_single_tool}× "
                f"(dataset p95={p95:.0f}×, median={p50:.0f}×)"
            )
            evidence["tool_hammering"] = {
                "finding": (
                    f"{top_tool_name} called {max_single_tool}× "
                    f"(dataset p95={p95:.0f}×, above p75={p75:.0f}×)"
                ),
                "recommendation": CATEGORY_RECOMMENDATIONS["tool_hammering"],
            }
        else:
            # Below p75: score 0–39 proportionally
            span = max(p75, 1)
            frac = max_single_tool / span
            scores["tool_hammering"] = min(39, int(frac * 39))

    # ── 2. CACHE INEFFICIENCY ─────────────────────────────────────────────────
    # Only meaningful when cache_creation is substantial (>50K tokens).
    # HIGH cache reuse ratio is NORMAL (median ~15.8×); LOW ratio is wasteful.
    reuse_ratio = 0.0  # computed here, also used in context_bloat below
    if cache_create > 50_000:
        reuse_ratio = cache_read / cache_create

        cr_p10    = t["cache_ratio_p10"]
        cr_p25    = t["cache_ratio_p25"]
        cr_median = t["cache_ratio_median"]

        if reuse_ratio < cr_p10:
            # Bottom 10%: score 70–100
            frac = max(0.0, (cr_p10 - reuse_ratio) / max(cr_p10, 0.1))
            frac = min(frac, 1.0)
            ci_score = int(70 + frac * 30)
            scores["cache_inefficiency"] = min(100, ci_score)
            # Compute percentile rank for display
            sorted_cr = t.get("_sorted_cache_ratios", [])
            rank_pct = rank_percentile_of(reuse_ratio, sorted_cr)
            flags["cache_inefficiency"].append(
                f"Cache reuse ratio {reuse_ratio:.1f}× "
                f"(dataset median {cr_median:.1f}×, yours is in bottom {max(rank_pct, 1):.0f}%)"
            )
            evidence["cache_inefficiency"] = {
                "finding": (
                    f"Cache reuse ratio {reuse_ratio:.1f}× "
                    f"(dataset median {cr_median:.1f}×, in the bottom 10%)"
                ),
                "recommendation": CATEGORY_RECOMMENDATIONS["cache_inefficiency"],
            }
        elif reuse_ratio < cr_p25:
            # p10–p25: score 30–69
            span = max(cr_p25 - cr_p10, 0.1)
            frac = (cr_p25 - reuse_ratio) / span
            frac = min(max(frac, 0.0), 1.0)
            ci_score = int(30 + frac * 39)
            scores["cache_inefficiency"] = min(69, ci_score)
            flags["cache_inefficiency"].append(
                f"Cache reuse ratio {reuse_ratio:.1f}× "
                f"(dataset median {cr_median:.1f}×, yours is in bottom 25%)"
            )
            evidence["cache_inefficiency"] = {
                "finding": (
                    f"Cache reuse ratio {reuse_ratio:.1f}× "
                    f"(dataset median {cr_median:.1f}×, below p25={cr_p25:.1f}×)"
                ),
                "recommendation": CATEGORY_RECOMMENDATIONS["cache_inefficiency"],
            }
        # >= p25 → score stays 0 (normal or good reuse)

    elif cache_create > 0:
        # Small cache — compute ratio for context_bloat even if not scored here
        reuse_ratio = cache_read / cache_create

    # ── 3. CONTEXT BLOAT ──────────────────────────────────────────────────────
    # Only meaningful when cache_creation is above the median (~201K).
    # Driven by the combination of low cache reuse AND a large context window.
    if cache_create > t["cache_create_p50"]:
        ci_score = scores["cache_inefficiency"]
        cb_score = 0

        if ci_score > 50 and cache_create > t["cache_create_p75"]:
            cb_score = int(ci_score * 0.8)
            flags["context_bloat"].append(
                f"Large context ({cache_create // 1_000}K tokens) "
                f"with low reuse ratio {reuse_ratio:.1f}×"
            )
            evidence["context_bloat"] = {
                "finding": (
                    f"Cache created {cache_create / 1_000_000:.1f}M tokens "
                    f"with only {reuse_ratio:.1f}× reuse (median={t['cache_ratio_median']:.1f}×)"
                ),
                "recommendation": CATEGORY_RECOMMENDATIONS["context_bloat"],
            }

        # Long session without compaction also signals context bloat
        if duration > 120 and not has_compaction:
            cb_score = max(cb_score, 40)
            flags["context_bloat"].append(
                f"{duration:.0f} min session with large context and no /compact"
            )
            if "context_bloat" not in evidence:
                evidence["context_bloat"] = {
                    "finding": (
                        f"{duration:.0f} min session with "
                        f"{cache_create // 1_000}K token context and no compaction"
                    ),
                    "recommendation": CATEGORY_RECOMMENDATIONS["context_bloat"],
                }

        scores["context_bloat"] = min(100, cb_score)

    # ── 4. COMPACTION ABSENCE ─────────────────────────────────────────────────
    # Short sessions (<= 15 min) don't need compaction. Long ones do.
    if not has_compaction:
        if duration > 180:
            # 180+ min: score 80–100
            excess = min((duration - 180) / 300.0, 1.0)
            ca_score = int(80 + excess * 20)
            scores["compaction_absence"] = min(100, ca_score)
            flags["compaction_absence"].append(f"{duration:.0f} min session without /compact")
            evidence["compaction_absence"] = {
                "finding": f"{duration:.0f} min session without /compact",
                "recommendation": CATEGORY_RECOMMENDATIONS["compaction_absence"],
            }
        elif duration > 60:
            # 60–180 min: score 40–79
            frac = (duration - 60) / (180 - 60)
            ca_score = int(40 + frac * 39)
            scores["compaction_absence"] = min(79, ca_score)
            flags["compaction_absence"].append(f"{duration:.0f} min session without /compact")
            evidence["compaction_absence"] = {
                "finding": f"{duration:.0f} min session without /compact",
                "recommendation": CATEGORY_RECOMMENDATIONS["compaction_absence"],
            }
        elif duration > 15:
            # 15–60 min: score 10–39
            frac = (duration - 15) / (60 - 15)
            ca_score = int(10 + frac * 29)
            scores["compaction_absence"] = min(39, ca_score)
            flags["compaction_absence"].append(f"{duration:.0f} min session without /compact")
        # <= 15 min: score stays 0

    # ── 5. INTERRUPTION LOOPS ─────────────────────────────────────────────────
    if interruptions >= 10:
        excess = min((interruptions - 10) / 10.0, 1.0)
        il_score = int(80 + excess * 20)
        scores["interruption_loops"] = min(100, il_score)
        flags["interruption_loops"].append(f"{interruptions} user interruptions")
        evidence["interruption_loops"] = {
            "finding": f"{interruptions} user interruptions",
            "recommendation": CATEGORY_RECOMMENDATIONS["interruption_loops"],
        }
    elif interruptions >= 5:
        frac = (interruptions - 5) / (10 - 5)
        il_score = int(40 + frac * 39)
        scores["interruption_loops"] = min(79, il_score)
        flags["interruption_loops"].append(f"{interruptions} user interruptions")
        evidence["interruption_loops"] = {
            "finding": f"{interruptions} user interruptions",
            "recommendation": CATEGORY_RECOMMENDATIONS["interruption_loops"],
        }
    elif interruptions >= 3:
        frac = (interruptions - 3) / (5 - 3)
        il_score = int(20 + frac * 19)
        scores["interruption_loops"] = min(39, il_score)
        flags["interruption_loops"].append(f"{interruptions} user interruptions")

    # ── 6. THINKING WASTE ─────────────────────────────────────────────────────
    # Only scored when the session used extended thinking. Low output-per-turn
    # while thinking is enabled indicates the thinking budget is not justified.
    if has_thinking:
        output_per_turn = output_tok / assistant_msgs
        if output_per_turn < 50:
            # Very low output relative to thinking: score 80–100
            frac = max(0.0, (50 - output_per_turn) / 50.0)
            tw_score = int(80 + frac * 20)
            scores["thinking_waste"] = min(100, tw_score)
            flags["thinking_waste"].append(
                f"Extended thinking with avg {output_per_turn:.0f} tokens/response"
            )
            evidence["thinking_waste"] = {
                "finding": (
                    f"Extended thinking with avg {output_per_turn:.0f} tokens/response "
                    f"(very low output)"
                ),
                "recommendation": CATEGORY_RECOMMENDATIONS["thinking_waste"],
            }
        elif output_per_turn < 200:
            # Moderate output: score 40–79
            frac = (200 - output_per_turn) / (200 - 50)
            tw_score = int(40 + frac * 39)
            scores["thinking_waste"] = min(79, tw_score)
            flags["thinking_waste"].append(
                f"Extended thinking with avg {output_per_turn:.0f} tokens/response"
            )
            evidence["thinking_waste"] = {
                "finding": (
                    f"Extended thinking with avg {output_per_turn:.0f} tokens/response"
                ),
                "recommendation": CATEGORY_RECOMMENDATIONS["thinking_waste"],
            }
        # >= 200 tokens/response → score stays 0 (output justifies thinking cost)

    # ── 7. PARALLEL SPRAWL ────────────────────────────────────────────────────
    # Computed at project level in detect_parallel_sprawl(); skipped per-session.

    # ── Overall score: average of non-zero category scores ────────────────────
    active_scores = [v for v in scores.values() if v > 0]
    total_score = int(sum(active_scores) / len(active_scores)) if active_scores else 0

    active_categories = sorted(
        [(c, v) for c, v in scores.items() if v > 0],
        key=lambda x: -x[1],
    )

    return {
        "scores":            scores,
        "flags":             flags,
        "evidence":          evidence,
        "total_score":       total_score,
        "active_categories": active_categories,
    }


# ─── Project-level parallel sprawl ────────────────────────────────────────────

def detect_parallel_sprawl(sessions_by_project):
    """
    Detect projects with concurrent session activity within 30-minute windows.
    Returns dict[slug -> max_concurrent_sessions].
    """
    results = {}
    for slug, sessions in sessions_by_project.items():
        timestamps = []
        for s in sessions:
            raw = s.get("start_time")
            if raw:
                try:
                    t = datetime.fromisoformat(raw.replace("Z", "+00:00"))
                    timestamps.append(t)
                except Exception:
                    pass
        if len(timestamps) < 3:
            results[slug] = 0
            continue
        timestamps.sort()
        max_concurrent = 1
        for i, t in enumerate(timestamps):
            window_end = t + timedelta(minutes=30)
            concurrent = sum(1 for other in timestamps[i + 1:] if other <= window_end)
            max_concurrent = max(max_concurrent, concurrent + 1)
        results[slug] = max_concurrent
    return results


# ─── Time series ─────────────────────────────────────────────────────────────

def build_time_series(all_sessions_flat, scores_by_session, project_by_session=None):
    """
    Aggregate sessions by calendar day for trend charts.
    Returns list of dicts sorted by date, each with aggregate totals plus
    per-project cost breakdown and per-waste-category score sums.
    """
    def _empty_day():
        return {
            "cost": 0.0, "sessions": 0,
            "cache_hit_sum": 0.0, "waste_sum": 0.0,
            "by_project": defaultdict(float),
            "by_waste":   defaultdict(float),
        }
    days = defaultdict(_empty_day)

    for s in all_sessions_flat:
        raw = s.get("start_time")
        if not raw:
            continue
        try:
            t = datetime.fromisoformat(raw.replace("Z", "+00:00"))
            day_key = t.strftime("%Y-%m-%d")
        except Exception:
            continue
        sid  = s.get("session_id", "")
        scr  = scores_by_session.get(sid, {})
        cost = s.get("estimated_cost", 0) or 0

        days[day_key]["cost"]     += cost
        days[day_key]["sessions"] += 1
        days[day_key]["cache_hit_sum"] += cache_hit_rate_pct(s)
        days[day_key]["waste_sum"]     += scr.get("total_score", 0)

        if project_by_session:
            slug = (project_by_session.get(sid) or {}).get("slug", "other")
            days[day_key]["by_project"][slug] += cost

        for cat, val in (scr.get("scores") or {}).items():
            if val > 0:
                days[day_key]["by_waste"][cat] += val

    result = []
    for day_key in sorted(days.keys()):
        d = days[day_key]
        n = d["sessions"]
        result.append({
            "date":               day_key,
            "cost":               round(d["cost"], 2),
            "sessions":           n,
            "avg_cache_hit_rate": round(d["cache_hit_sum"] / n, 1) if n else 0,
            "avg_waste_score":    round(d["waste_sum"] / n, 1) if n else 0,
            "by_project":         {k: round(v, 2) for k, v in d["by_project"].items()},
            "by_waste":           {k: round(v, 1) for k, v in d["by_waste"].items()},
        })
    return result


# ─── Heatmap ──────────────────────────────────────────────────────────────────

def build_heatmap(sessions):
    """
    Build a weekday × hour session-count matrix.
    Keys are STRINGS (JSON-compatible, correct for JS object access).
    Format: {"0": {"14": 3}, "1": {"15": 5}, ...}
    Weekday 0 = Monday … 6 = Sunday.
    """
    heatmap = defaultdict(lambda: defaultdict(int))
    for s in sessions:
        raw = s.get("start_time")
        if raw:
            try:
                t = datetime.fromisoformat(raw.replace("Z", "+00:00"))
                heatmap[t.weekday()][t.hour] += 1
            except Exception:
                pass
    return {
        str(day): {str(hour): count for hour, count in hours.items()}
        for day, hours in heatmap.items()
    }


# ─── Helper: cache hit rate ────────────────────────────────────────────────────

def cache_hit_rate_pct(s):
    """Percentage of total input tokens that were served from cache."""
    cc  = s.get("cache_creation_input_tokens", 0) or 0
    cr  = s.get("cache_read_input_tokens", 0) or 0
    inp = s.get("input_tokens", 0) or 0
    total = cc + cr + inp
    if total == 0:
        return 0
    return round(cr / total * 100)


# ─── Potential savings estimate ────────────────────────────────────────────────

def estimate_savings(sessions, scores_by_session):
    """
    Rough estimate: sessions with waste_score > 50 could save ~20% of their
    cost if the top recommendations were applied.
    """
    savings = 0.0
    for s in sessions:
        sid = s.get("session_id", "")
        scr = scores_by_session.get(sid, {})
        if scr.get("total_score", 0) > 50:
            savings += (s.get("estimated_cost", 0) or 0) * 0.20
    return round(savings, 2)


# ─── Spec builder ─────────────────────────────────────────────────────────────

def build_spec(
    args,
    all_projects,
    all_sessions_flat,
    sessions_by_project,
    scores_by_session,
    sprawl_by_project,
    thresholds,
    project_by_session,
):
    """Assemble the full JSON spec dict that the dashboard generator reads."""

    total_cost    = round(sum((s.get("estimated_cost", 0) or 0) for s in all_sessions_flat), 2)
    total_sessions = len(all_sessions_flat)

    potential_savings = estimate_savings(all_sessions_flat, scores_by_session)

    # ── Waste category totals (sum of per-session scores) ──────────────────────
    cat_totals = {c: 0 for c in WASTE_CATEGORIES}
    for scr in scores_by_session.values():
        for c, v in scr["scores"].items():
            cat_totals[c] += v
    # Add project-level parallel sprawl contribution
    for slug, sprawl in sprawl_by_project.items():
        if sprawl >= 3:
            cat_totals["parallel_sprawl"] += min(100, sprawl * 25)

    top_waste_cat = (
        max(cat_totals, key=cat_totals.get)
        if any(cat_totals.values())
        else "tool_hammering"
    )

    # ── Projects ──────────────────────────────────────────────────────────────
    projects_out = []
    for p in all_projects:
        slug     = p.get("slug", "")
        sessions = sessions_by_project.get(slug, [])
        duration_total = sum((s.get("duration_minutes", 0) or 0) for s in sessions)

        # Aggregate waste scores per project: take the maximum across all sessions
        agg_scores = {c: 0 for c in WASTE_CATEGORIES}
        agg_flags  = {c: [] for c in WASTE_CATEGORIES}
        for s in sessions:
            sid = s.get("session_id", "")
            scr = scores_by_session.get(sid, {})
            for c in WASTE_CATEGORIES:
                val = scr.get("scores", {}).get(c, 0)
                if val > agg_scores[c]:
                    agg_scores[c] = val
                agg_flags[c].extend(scr.get("flags", {}).get(c, []))

        sprawl = sprawl_by_project.get(slug, 0)
        if sprawl >= 3:
            agg_scores["parallel_sprawl"] = min(100, sprawl * 25)
            agg_flags["parallel_sprawl"].append(f"Up to {sprawl} concurrent sessions detected")

        # Deduplicate flags, keep at most 3 per category
        for c in WASTE_CATEGORIES:
            seen, deduped = set(), []
            for f in agg_flags[c]:
                if f not in seen:
                    seen.add(f)
                    deduped.append(f)
            agg_flags[c] = deduped[:3]

        projects_out.append({
            "slug":                   slug,
            "display_name":           p.get("display_name", slug),
            "estimated_cost":         round(p.get("estimated_cost", 0) or 0, 2),
            "session_count":          p.get("session_count") or len(sessions),
            "total_duration_minutes": round(duration_total, 1),
            "parallel_sprawl_score":  min(100, sprawl * 25) if sprawl >= 3 else 0,
            "waste_scores":           agg_scores,
            "waste_flags":            {c: v for c, v in agg_flags.items() if v},
        })

    projects_out.sort(key=lambda x: x.get("estimated_cost", 0), reverse=True)

    # ── Sessions: top 50 by cost ───────────────────────────────────────────────
    sorted_sessions = sorted(
        all_sessions_flat,
        key=lambda s: s.get("estimated_cost", 0) or 0,
        reverse=True,
    )[:50]

    # Fetch replay data for the top 3 most expensive sessions
    top3_ids = [s.get("session_id") for s in sorted_sessions[:3] if s.get("session_id")]
    replay_by_id = {}
    for sid in top3_ids:
        print(f"  [replay] Fetching replay for session {sid[:12]}...", flush=True)
        data = api_get(f"/api/sessions/{sid}/replay", timeout=60)
        if isinstance(data, dict):
            turns = data.get("turns", data)
        elif isinstance(data, list):
            turns = data
        else:
            turns = None
        replay_by_id[sid] = turns

    sessions_out = []
    for s in sorted_sessions:
        sid  = s.get("session_id", "")
        scr  = scores_by_session.get(sid, {})
        active_cats = scr.get("active_categories", [])
        top_waste   = active_cats[0][0] if active_cats else None

        tool_counts = s.get("tool_counts", {}) or {}
        top_tools   = dict(sorted(tool_counts.items(), key=lambda x: -x[1])[:5])

        proj      = project_by_session.get(sid, {})
        proj_slug = proj.get("slug", s.get("project_path", ""))
        proj_name = proj.get("display_name", proj_slug)

        cc = s.get("cache_creation_input_tokens", 0) or 0
        cr = s.get("cache_read_input_tokens", 0) or 0
        reuse_ratio = round(cr / cc, 2) if cc > 50_000 else round(cr / cc, 2) if cc > 0 else None

        sessions_out.append({
            "session_id":         sid,
            "project_slug":       proj_slug,
            "project_name":       proj_name,
            "start_time":         s.get("start_time"),
            "estimated_cost":     round(s.get("estimated_cost", 0) or 0, 2),
            "duration_minutes":   round(s.get("duration_minutes", 0) or 0, 1),
            "cache_hit_rate_pct": cache_hit_rate_pct(s),
            "cache_reuse_ratio":  reuse_ratio,
            "total_tools":        sum(tool_counts.values()),
            "tool_breakdown":     top_tools,
            "has_compaction":     bool(s.get("has_compaction", False)),
            "has_thinking":       bool(s.get("has_thinking", False)),
            "waste_score":        scr.get("total_score", 0),
            "top_waste":          top_waste,
            "waste_scores":       scr.get("scores", {c: 0 for c in WASTE_CATEGORIES}),
            "waste_evidence":     scr.get("evidence", {}),
            "replay":             replay_by_id.get(sid),
        })

    # ── Heatmap (all sessions, not just top 50) ────────────────────────────────
    heatmap = build_heatmap(all_sessions_flat)

    # ── Time series (all sessions aggregated by day) ───────────────────────────
    time_series = build_time_series(all_sessions_flat, scores_by_session, project_by_session)

    # ── Summary ───────────────────────────────────────────────────────────────
    summary = {
        "total_cost":         total_cost,
        "total_sessions":     total_sessions,
        "project_count":      len(all_projects),
        "potential_savings":  potential_savings,
        "top_waste_category": top_waste_cat,
        "top_waste_label":    CATEGORY_LABELS[top_waste_cat],
        "top_waste_color":    CATEGORY_COLORS[top_waste_cat],
    }

    return {
        "generated_at":          datetime.now().strftime("%Y-%m-%d %H:%M"),
        "params":                {"top_n": args.top_n, "sort_by": args.sort_by},
        "summary":               summary,
        "waste_category_totals": {c: v for c, v in cat_totals.items() if v > 0},
        "projects":              projects_out,
        "sessions":              sessions_out,
        "heatmap":               heatmap,
        "time_series":           time_series,
        "thresholds": {
            "max_tool_p75":       round(thresholds["max_tool_p75"], 1),
            "max_tool_p95":       round(thresholds["max_tool_p95"], 1),
            "cache_ratio_p10":    round(thresholds["cache_ratio_p10"], 2),
            "cache_ratio_p25":    round(thresholds["cache_ratio_p25"], 2),
            "cache_ratio_median": round(thresholds["cache_ratio_median"], 2),
        },
    }


# ─── Main ─────────────────────────────────────────────────────────────────────

def run(args):
    # ── 1. Fetch projects ──────────────────────────────────────────────────────
    print("[cc-lens] Fetching projects...", flush=True)
    projects_data = api_get("/api/projects")
    if not projects_data:
        print("[ERROR] Cannot reach cc-lens at http://localhost:3001 — is it running?")
        sys.exit(1)

    all_projects = (
        projects_data.get("projects", projects_data)
        if isinstance(projects_data, dict)
        else projects_data
    )
    if not isinstance(all_projects, list):
        print("[ERROR] Unexpected projects response format")
        sys.exit(1)

    # Optional project filter
    if args.project:
        all_projects = [
            p for p in all_projects
            if args.project in p.get("slug", "")
            or args.project.lower() in (p.get("display_name", "") or "").lower()
        ]

    sort_key = "estimated_cost" if args.sort_by == "cost" else "output_tokens"
    all_projects.sort(key=lambda p: p.get(sort_key, 0) or 0, reverse=True)
    print(f"[cc-lens] Found {len(all_projects)} projects", flush=True)

    # ── 2. Fetch sessions ──────────────────────────────────────────────────────
    print("[cc-lens] Fetching sessions (may take up to 60s)...", flush=True)
    sessions_data = api_get("/api/sessions", timeout=60)
    all_sessions_raw = (
        sessions_data.get("sessions", sessions_data)
        if isinstance(sessions_data, dict)
        else sessions_data or []
    )
    print(f"[cc-lens] Got {len(all_sessions_raw)} sessions total", flush=True)

    # Optional single-session filter
    if args.session:
        match = next(
            (s for s in all_sessions_raw if s.get("session_id", "").startswith(args.session)),
            None,
        )
        if match:
            all_sessions_raw = [match]
            proj = next(
                (p for p in all_projects if p.get("project_path") == match.get("project_path")),
                None,
            )
            all_projects = [proj] if proj else [
                {"slug": "unknown", "display_name": "unknown", "estimated_cost": 0}
            ]
        else:
            print(f"[WARN] Session {args.session!r} not found in dataset", flush=True)

    # ── 3. Index sessions by project slug ─────────────────────────────────────
    sessions_by_project = defaultdict(list)
    project_by_session  = {}
    for s in all_sessions_raw:
        proj = next(
            (p for p in all_projects if p.get("project_path") == s.get("project_path")),
            None,
        )
        if proj:
            slug = proj["slug"]
            sessions_by_project[slug].append(s)
            project_by_session[s.get("session_id", "")] = proj

    all_sessions_flat = [s for ss in sessions_by_project.values() for s in ss]
    print(f"[cc-lens] {len(all_sessions_flat)} sessions matched to projects", flush=True)

    # ── 4. Compute percentile thresholds ──────────────────────────────────────
    print(
        f"[cc-lens] Computing percentile thresholds from {len(all_sessions_flat)} sessions...",
        flush=True,
    )
    thresholds = compute_thresholds(all_sessions_flat)
    print(
        f"  max_tool  p75={thresholds['max_tool_p75']:.0f}  "
        f"p95={thresholds['max_tool_p95']:.0f}  |  "
        f"cache_ratio  p10={thresholds['cache_ratio_p10']:.1f}  "
        f"median={thresholds['cache_ratio_median']:.1f}",
        flush=True,
    )

    # ── 5. Score sessions ──────────────────────────────────────────────────────
    print(f"[cc-lens] Scoring {len(all_sessions_flat)} sessions...", flush=True)
    scores_by_session = {
        s.get("session_id", ""): score_session(s, thresholds)
        for s in all_sessions_flat
    }

    # ── 6. Detect parallel sprawl ──────────────────────────────────────────────
    sprawl_by_project = detect_parallel_sprawl(sessions_by_project)

    # ── 7. Build spec (includes replay fetches for top 3) ─────────────────────
    print("[cc-lens] Building spec (fetching replay for top 3 sessions)...", flush=True)
    spec = build_spec(
        args,
        all_projects,
        all_sessions_flat,
        sessions_by_project,
        scores_by_session,
        sprawl_by_project,
        thresholds,
        project_by_session,
    )

    # ── 8. Write spec file ────────────────────────────────────────────────────
    output_path = args.output or "/tmp/cc-lens-spec.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(spec, f, indent=2, default=str)
    print(f"[cc-lens] Spec written to: {output_path}", flush=True)

    # ── 9. Console summary ────────────────────────────────────────────────────
    summary    = spec["summary"]
    cat_totals = spec["waste_category_totals"]
    top3_waste = sorted(cat_totals.items(), key=lambda x: -x[1])[:3]

    print(f"\n{'=' * 60}")
    print("cc-lens Analysis Summary")
    print(f"{'=' * 60}")
    print(f"Total cost analyzed:  ${summary['total_cost']:.2f}")
    print(f"Total sessions:       {summary['total_sessions']}")
    print(f"Projects:             {summary['project_count']}")
    print(f"Potential savings:    ${summary['potential_savings']:.2f}")
    print()
    print("Top 3 waste categories:")
    for i, (cat, total) in enumerate(top3_waste, 1):
        label = CATEGORY_LABELS.get(cat, cat)
        fix   = CATEGORY_FIXES.get(cat, "")[:60]
        print(f"  {i}. {label}: score_sum={total}  — {fix}...")
    print(f"{'=' * 60}\n")

    return output_path


def main():
    parser = argparse.ArgumentParser(
        description="cc-lens token forensics analyzer — generates JSON spec for the dashboard"
    )
    parser.add_argument(
        "--top-n", type=int, default=5,
        help="Top N projects to emphasize in params (default: 5)",
    )
    parser.add_argument(
        "--sort-by", choices=["cost", "tokens"], default="cost",
        help="Primary sort metric (default: cost)",
    )
    parser.add_argument(
        "--project", type=str, default=None,
        help="Filter to a specific project by slug or name substring",
    )
    parser.add_argument(
        "--session", type=str, default=None,
        help="Analyze a single session by ID prefix",
    )
    parser.add_argument(
        "--output", type=str, default="/tmp/cc-lens-spec.json",
        help="Output path for the JSON spec (default: /tmp/cc-lens-spec.json)",
    )
    args = parser.parse_args()
    run(args)


if __name__ == "__main__":
    main()
