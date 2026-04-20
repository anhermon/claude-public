#!/usr/bin/env python3
"""
Forensic dashboard generator — reads Claude Code session JSONL files directly
and emits a single-file HTML dashboard plus per-chart JSON data files.

Stdlib only. Works on Windows and POSIX.

Outputs (under --out):
    index.html                 — full single-file dashboard (Chart.js via CDN)
    data/summary.json          — header metrics
    data/projects.json         — per-project waste/cost aggregates
    data/sessions.json         — flat list of scored sessions (for table + deep-dive)
    data/time_series.json      — per-day aggregates
    data/heatmap.json          — weekday × hour session counts
    data/file_heat.json        — file-access aggregates (full path, tokens, accesses)
    data/waste_categories.json — category totals + labels + colors
    data/thresholds.json       — computed dataset percentiles used for scoring

Waste rubric thresholds (documented here):

    tool_hammering     : max single-tool calls in one session vs. dataset p95
    tool_pollution     : total tool calls per session vs. dataset p95
    compaction_absence : session duration > 45 min with no /compact slash command
    context_bloat      : cache_creation_input_tokens above p75 with no compaction
    cache_inefficiency : cache hit rate below dataset median
    parallel_sprawl    : >= 3 sessions concurrent on same project in 30-min window
    interruption_loops : user interruption ratio >= 15% of user turns
    thinking_waste     : thinking tokens > 2× output tokens when both are present
"""

from __future__ import annotations

import html
import json
import math
import re
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

# ── Waste taxonomy ──────────────────────────────────────────────────────────

WASTE_CATEGORIES = [
    "tool_hammering",
    "tool_pollution",
    "compaction_absence",
    "context_bloat",
    "cache_inefficiency",
    "parallel_sprawl",
    "interruption_loops",
    "thinking_waste",
]

CATEGORY_LABELS = {
    "tool_hammering":     "Tool Hammering",
    "tool_pollution":     "Tool Pollution",
    "compaction_absence": "Compaction Absence",
    "context_bloat":      "Context Bloat",
    "cache_inefficiency": "Cache Inefficiency",
    "parallel_sprawl":    "Parallel Sprawl",
    "interruption_loops": "Interruption Loops",
    "thinking_waste":     "Thinking Waste",
}

CATEGORY_COLORS = {
    "tool_hammering":     "#6366f1",
    "tool_pollution":     "#a855f7",
    "compaction_absence": "#06b6d4",
    "context_bloat":      "#ef4444",
    "cache_inefficiency": "#f97316",
    "parallel_sprawl":    "#8b5cf6",
    "interruption_loops": "#ec4899",
    "thinking_waste":     "#84cc16",
}

CATEGORY_FIXES = {
    "tool_hammering":     "Batch repeated commands; use Agent for broad searches; cache shell output locally.",
    "tool_pollution":     "Trim MCP servers; batch reads; avoid redundant Grep/Glob passes.",
    "compaction_absence": "Run /compact every ~45 min or enable auto-compaction in settings.",
    "context_bloat":      "Split the task; run /compact when context feels large; drop unused files from context.",
    "cache_inefficiency": "Keep system prompt stable; avoid reshuffling tool descriptions between turns.",
    "parallel_sprawl":    "Consolidate to one active window per project; finish before spawning more.",
    "interruption_loops": "Write clearer up-front specs; use TodoWrite for persistent plans; scope smaller turns.",
    "thinking_waste":     "Disable extended thinking for routine edits; reserve for genuinely hard reasoning.",
}

# Savings rates if the waste were fully addressed (per category of dominant waste)
CATEGORY_SAVINGS_RATE = {
    "tool_hammering":     0.40,
    "tool_pollution":     0.35,
    "compaction_absence": 0.30,
    "cache_inefficiency": 0.25,
    "context_bloat":      0.20,
    "parallel_sprawl":    0.20,
    "interruption_loops": 0.15,
    "thinking_waste":     0.15,
}

# Approximate token pricing (USD per token). Used only when a session JSONL
# does not surface a precomputed cost. Numbers track Anthropic's published
# Sonnet 4.x rates (input $3/M, output $15/M, cache write $3.75/M, cache read $0.30/M).
# Opus sessions cost ~5× more; we detect that via the model name if present.
PRICING = {
    "sonnet": {"input": 3e-6, "output": 15e-6, "cache_write": 3.75e-6, "cache_read": 0.3e-6},
    "opus":   {"input": 15e-6, "output": 75e-6, "cache_write": 18.75e-6, "cache_read": 1.5e-6},
    "haiku":  {"input": 0.8e-6, "output": 4e-6, "cache_write": 1e-6, "cache_read": 0.08e-6},
}

SLASH_COMPACT_RE = re.compile(r"/compact\b", re.IGNORECASE)


# ── Helpers ─────────────────────────────────────────────────────────────────


def _parse_ts(s: str | None) -> datetime | None:
    if not s or not isinstance(s, str):
        return None
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except ValueError:
        return None


def _pricing_for_model(model: str | None) -> dict:
    if not model:
        return PRICING["sonnet"]
    m = model.lower()
    if "opus" in m:
        return PRICING["opus"]
    if "haiku" in m:
        return PRICING["haiku"]
    return PRICING["sonnet"]


def _project_display(slug: str) -> str:
    """Turn a project folder slug (C--Users-User--paperclip) into a readable tail.

    We keep the last 3 path segments because the leading drive prefix is noise.
    """
    if not slug:
        return "(unknown)"
    # replace double-dash with / to recover real path-ish layout
    parts = [p for p in slug.split("--") if p]
    if len(parts) <= 3:
        return slug
    tail = "/".join(parts[-3:])
    return "…/" + tail


def _percentile(values: list[float], p: float) -> float:
    if not values:
        return 0.0
    s = sorted(v for v in values if v is not None)
    if not s:
        return 0.0
    if len(s) == 1:
        return float(s[0])
    idx = (p / 100.0) * (len(s) - 1)
    lo = int(math.floor(idx))
    hi = min(lo + 1, len(s) - 1)
    frac = idx - lo
    return float(s[lo] + frac * (s[hi] - s[lo]))


def _approx_tokens(text: str) -> int:
    """Rough token count — 4 chars per token is the widely-used approximation."""
    if not text:
        return 0
    return max(1, len(text) // 4)


# ── JSONL ingest ────────────────────────────────────────────────────────────


def parse_session_file(path: Path) -> dict[str, Any] | None:
    """Extract metrics from one Claude Code session JSONL file.

    Returns a dict with per-session aggregates and per-turn data.
    Returns None if the file contains no assistant turns (e.g. aborted launch).
    """
    try:
        raw = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None

    user_turns = 0
    assistant_turns = 0
    interruptions = 0
    compaction_used = False
    has_thinking = False
    thinking_tokens = 0

    input_tokens = 0
    output_tokens = 0
    cache_create = 0
    cache_read = 0

    tool_counts: Counter[str] = Counter()
    tool_sequence: list[str] = []
    file_accesses: Counter[str] = Counter()
    file_access_sessions: defaultdict[str, set] = defaultdict(set)
    read_paths: list[str] = []

    turns: list[dict[str, Any]] = []  # per-assistant-turn detail for deep-dive

    first_ts: datetime | None = None
    last_ts: datetime | None = None
    first_user_msg = ""
    cwd = ""
    model: str | None = None
    session_id = path.stem

    for line in raw.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(row, dict):
            continue

        t = row.get("type")
        ts = _parse_ts(row.get("timestamp"))
        if ts:
            if first_ts is None or ts < first_ts:
                first_ts = ts
            if last_ts is None or ts > last_ts:
                last_ts = ts
        if not cwd and isinstance(row.get("cwd"), str):
            cwd = row["cwd"]
        if not session_id and isinstance(row.get("sessionId"), str):
            session_id = row["sessionId"]

        if t == "user":
            user_turns += 1
            msg = row.get("message") or {}
            content = msg.get("content") if isinstance(msg, dict) else None
            text = ""
            if isinstance(content, str):
                text = content
            elif isinstance(content, list):
                for b in content:
                    if isinstance(b, dict) and b.get("text"):
                        text += str(b["text"])
            # Detect /compact usage
            if SLASH_COMPACT_RE.search(text):
                compaction_used = True
            # Detect interrupt markers — Claude CLI emits a specific sentinel string
            if "[Request interrupted by user" in text:
                interruptions += 1
            if not first_user_msg and text and not text.startswith("<local-command"):
                first_user_msg = text.strip()[:200]

        elif t == "assistant":
            assistant_turns += 1
            msg = row.get("message") or {}
            if not isinstance(msg, dict):
                continue
            if not model:
                model = msg.get("model")
            usage = msg.get("usage") or {}
            it = int(usage.get("input_tokens") or 0)
            ot = int(usage.get("output_tokens") or 0)
            cc = int(usage.get("cache_creation_input_tokens") or 0)
            cr = int(usage.get("cache_read_input_tokens") or 0)
            input_tokens += it
            output_tokens += ot
            cache_create += cc
            cache_read += cr

            # Thinking detection
            turn_tools: list[str] = []
            turn_thinking = 0
            content = msg.get("content")
            if isinstance(content, list):
                for b in content:
                    if not isinstance(b, dict):
                        continue
                    bt = b.get("type")
                    if bt == "thinking":
                        has_thinking = True
                        turn_thinking += _approx_tokens(str(b.get("thinking", "")))
                    elif bt == "tool_use":
                        name = b.get("name") or "?"
                        tool_counts[name] += 1
                        tool_sequence.append(name)
                        turn_tools.append(name)
                        inp = b.get("input") or {}
                        if isinstance(inp, dict):
                            for k in ("file_path", "path", "notebook_path"):
                                v = inp.get(k)
                                if isinstance(v, str) and v:
                                    file_accesses[v] += 1
                                    file_access_sessions[v].add(session_id)
                                    if name in ("Read", "Edit", "MultiEdit", "Write"):
                                        read_paths.append(v)
                                    break
            thinking_tokens += turn_thinking
            turns.append({
                "idx": assistant_turns,
                "timestamp": row.get("timestamp"),
                "input_tokens": it,
                "output_tokens": ot,
                "cache_create": cc,
                "cache_read": cr,
                "tools": turn_tools,
                "thinking_tokens": turn_thinking,
            })

    if assistant_turns == 0:
        return None

    # Duration
    duration_min = 0.0
    if first_ts and last_ts:
        duration_min = max(0.0, (last_ts - first_ts).total_seconds() / 60.0)

    # Cost estimate (best-effort from token counts)
    price = _pricing_for_model(model)
    est_cost = (
        input_tokens * price["input"]
        + output_tokens * price["output"]
        + cache_create * price["cache_write"]
        + cache_read * price["cache_read"]
    )

    # Repeat-read ratio
    repeat_read_pct = None
    if read_paths:
        c = Counter(read_paths)
        dup = sum(n - 1 for n in c.values() if n > 1)
        repeat_read_pct = round(dup / len(read_paths) * 100.0, 1)

    # Sequential tool %: fraction of assistant turns where ≥2 consecutive
    # calls are to the same tool (sign of hammering-within-turn).
    seq_tool_pct = None
    if tool_sequence:
        seq_hits = sum(
            1 for i in range(1, len(tool_sequence)) if tool_sequence[i] == tool_sequence[i - 1]
        )
        seq_tool_pct = round(seq_hits / len(tool_sequence) * 100.0, 1)

    # Turn-by-turn cost + cache-create %
    turn_costs: list[float] = []
    turn_cache_pct: list[float | None] = []
    for t in turns:
        c = (
            t["input_tokens"] * price["input"]
            + t["output_tokens"] * price["output"]
            + t["cache_create"] * price["cache_write"]
            + t["cache_read"] * price["cache_read"]
        )
        t["cost"] = round(c, 4)
        turn_costs.append(round(c, 4))
        denom = t["cache_create"] + t["cache_read"]
        turn_cache_pct.append(round(t["cache_read"] / denom * 100.0, 1) if denom else None)

    total_tokens = input_tokens + output_tokens + cache_create + cache_read
    cache_hit_rate = (
        round(cache_read / (cache_read + cache_create + input_tokens) * 100.0, 1)
        if (cache_read + cache_create + input_tokens) > 0
        else 0.0
    )

    return {
        "session_id": session_id,
        "path": str(path),
        "cwd": cwd,
        "project_slug": path.parent.name,
        "model": model,
        "start_time": first_ts.isoformat() if first_ts else None,
        "end_time": last_ts.isoformat() if last_ts else None,
        "duration_minutes": round(duration_min, 1),
        "user_turns": user_turns,
        "assistant_turns": assistant_turns,
        "interruptions": interruptions,
        "has_compaction": compaction_used,
        "has_thinking": has_thinking,
        "thinking_tokens": thinking_tokens,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "cache_create": cache_create,
        "cache_read": cache_read,
        "total_tokens": total_tokens,
        "cache_hit_rate_pct": cache_hit_rate,
        "estimated_cost": round(est_cost, 4),
        "tool_counts": dict(tool_counts),
        "total_tools": sum(tool_counts.values()),
        "first_user_message": first_user_msg,
        "repeat_read_pct": repeat_read_pct,
        "sequential_tool_pct": seq_tool_pct,
        "turns": turns,
        "turn_costs": turn_costs,
        "turn_cache_pct": turn_cache_pct,
        # file_accesses emitted separately for aggregation
        "_file_accesses": dict(file_accesses),
        "_file_access_sessions": {k: list(v) for k, v in file_access_sessions.items()},
    }


# ── Scoring ────────────────────────────────────────────────────────────────


def compute_thresholds(sessions: list[dict]) -> dict:
    tool_maxes = [max((s["tool_counts"].values() or [0]), default=0) for s in sessions]
    total_tools = [s["total_tools"] for s in sessions]
    cache_creates = [s["cache_create"] for s in sessions if s["cache_create"] > 0]
    cache_hits = [s["cache_hit_rate_pct"] for s in sessions if s["total_tokens"] > 0]
    durations = [s["duration_minutes"] for s in sessions if s["duration_minutes"] > 0]

    return {
        "tool_max_p75":     _percentile(tool_maxes, 75) or 30,
        "tool_max_p95":     _percentile(tool_maxes, 95) or 80,
        "total_tools_p75":  _percentile(total_tools, 75) or 60,
        "total_tools_p95":  _percentile(total_tools, 95) or 200,
        "cache_create_p75": _percentile(cache_creates, 75) or 500_000,
        "cache_hit_median": _percentile(cache_hits, 50) or 60,
        "duration_p95":     _percentile(durations, 95) or 180,
        "n_sessions":       len(sessions),
    }


def score_session(s: dict, thr: dict) -> dict:
    """Return {scores:{cat:0-100}, evidence:{cat:{score,evidence,fix}}, top_waste, total_score}."""
    scores = {c: 0 for c in WASTE_CATEGORIES}
    evidence: dict[str, dict] = {}

    tool_counts = s["tool_counts"]
    max_single = max(tool_counts.values(), default=0)
    top_tool = max(tool_counts, key=tool_counts.get) if tool_counts else "—"
    total_tools = s["total_tools"]

    # Tool Hammering
    p95 = thr["tool_max_p95"]
    p75 = thr["tool_max_p75"]
    if max_single >= p95:
        sc = min(100, 80 + int((max_single - p95) / max(p95, 1) * 20))
        scores["tool_hammering"] = sc
        evidence["tool_hammering"] = {
            "score": sc,
            "evidence": f"{top_tool} called {max_single}× in one session (dataset p95={p95:.0f}).",
            "fix": CATEGORY_FIXES["tool_hammering"],
        }
    elif max_single >= p75:
        sc = 40 + int((max_single - p75) / max(p95 - p75, 1) * 40)
        scores["tool_hammering"] = min(79, sc)
        evidence["tool_hammering"] = {
            "score": scores["tool_hammering"],
            "evidence": f"{top_tool} called {max_single}× (dataset p75={p75:.0f}).",
            "fix": CATEGORY_FIXES["tool_hammering"],
        }

    # Tool Pollution
    tp95 = thr["total_tools_p95"]
    tp75 = thr["total_tools_p75"]
    if total_tools >= tp95:
        sc = min(100, 75 + int((total_tools - tp95) / max(tp95, 1) * 25))
        scores["tool_pollution"] = sc
        evidence["tool_pollution"] = {
            "score": sc,
            "evidence": f"{total_tools} total tool calls (dataset p95={tp95:.0f}).",
            "fix": CATEGORY_FIXES["tool_pollution"],
        }
    elif total_tools >= tp75:
        sc = 30 + int((total_tools - tp75) / max(tp95 - tp75, 1) * 40)
        scores["tool_pollution"] = min(69, sc)
        evidence["tool_pollution"] = {
            "score": scores["tool_pollution"],
            "evidence": f"{total_tools} total tool calls (dataset p75={tp75:.0f}).",
            "fix": CATEGORY_FIXES["tool_pollution"],
        }

    # Compaction Absence
    dur = s["duration_minutes"]
    if not s["has_compaction"]:
        if dur > 180:
            sc = min(100, 80 + int((dur - 180) / 300 * 20))
            scores["compaction_absence"] = sc
            evidence["compaction_absence"] = {
                "score": sc,
                "evidence": f"{dur:.0f} min session with no /compact.",
                "fix": CATEGORY_FIXES["compaction_absence"],
            }
        elif dur > 45:
            sc = 20 + int((dur - 45) / (180 - 45) * 59)
            scores["compaction_absence"] = min(79, sc)
            evidence["compaction_absence"] = {
                "score": scores["compaction_absence"],
                "evidence": f"{dur:.0f} min session without /compact (threshold 45 min).",
                "fix": CATEGORY_FIXES["compaction_absence"],
            }

    # Context Bloat: large cache create, no compaction, long session
    cc_p75 = thr["cache_create_p75"]
    if s["cache_create"] >= cc_p75 and not s["has_compaction"]:
        sc = min(100, 50 + int((s["cache_create"] - cc_p75) / max(cc_p75, 1) * 50))
        scores["context_bloat"] = sc
        evidence["context_bloat"] = {
            "score": sc,
            "evidence": f"{s['cache_create']//1000}K cache-create tokens without compaction.",
            "fix": CATEGORY_FIXES["context_bloat"],
        }

    # Cache Inefficiency
    med = thr["cache_hit_median"]
    if s["total_tokens"] > 0 and s["cache_hit_rate_pct"] < med - 5:
        gap = med - s["cache_hit_rate_pct"]
        sc = min(100, 30 + int(gap / max(med, 1) * 70))
        scores["cache_inefficiency"] = sc
        evidence["cache_inefficiency"] = {
            "score": sc,
            "evidence": (
                f"Cache hit rate {s['cache_hit_rate_pct']:.1f}% "
                f"(dataset median {med:.1f}%)."
            ),
            "fix": CATEGORY_FIXES["cache_inefficiency"],
        }

    # Interruption Loops
    if s["user_turns"] > 0:
        ratio = s["interruptions"] / s["user_turns"]
        if ratio >= 0.15:
            sc = min(100, 40 + int((ratio - 0.15) / 0.35 * 60))
            scores["interruption_loops"] = sc
            evidence["interruption_loops"] = {
                "score": sc,
                "evidence": f"{s['interruptions']} interruptions across {s['user_turns']} user turns.",
                "fix": CATEGORY_FIXES["interruption_loops"],
            }

    # Thinking Waste
    if s["has_thinking"] and s["thinking_tokens"] > 0:
        out = max(s["output_tokens"], 1)
        ratio = s["thinking_tokens"] / out
        if ratio >= 2.0:
            sc = min(100, 40 + int((ratio - 2.0) / 4.0 * 60))
            scores["thinking_waste"] = sc
            evidence["thinking_waste"] = {
                "score": sc,
                "evidence": f"Thinking {s['thinking_tokens']} tok vs output {out} tok ({ratio:.1f}×).",
                "fix": CATEGORY_FIXES["thinking_waste"],
            }

    active = [v for v in scores.values() if v > 0]
    total = int(sum(active) / len(active)) if active else 0
    active_cats = sorted(
        [(c, v) for c, v in scores.items() if v > 0], key=lambda x: -x[1]
    )
    top_waste = active_cats[0][0] if active_cats else None
    return {
        "scores": scores,
        "evidence": evidence,
        "total_score": total,
        "top_waste": top_waste,
    }


def detect_parallel_sprawl(sessions: list[dict]) -> dict[str, int]:
    """Return {project_slug: max_concurrent_sessions_in_30min}."""
    by_proj: defaultdict[str, list[datetime]] = defaultdict(list)
    for s in sessions:
        ts = _parse_ts(s.get("start_time"))
        if ts:
            by_proj[s["project_slug"]].append(ts)
    out: dict[str, int] = {}
    for slug, stamps in by_proj.items():
        if len(stamps) < 3:
            out[slug] = 0
            continue
        stamps.sort()
        best = 1
        for i, t in enumerate(stamps):
            win = t + timedelta(minutes=30)
            n = 1 + sum(1 for other in stamps[i + 1 :] if other <= win)
            best = max(best, n)
        out[slug] = best
    return out


# ── Aggregations ───────────────────────────────────────────────────────────


def build_time_series(sessions: list[dict]) -> list[dict]:
    days: defaultdict[str, dict] = defaultdict(lambda: {
        "cost": 0.0, "sessions": 0, "cache_hit_sum": 0.0,
        "waste_sum": 0.0, "by_project": defaultdict(float),
        "by_waste": defaultdict(float),
    })
    for s in sessions:
        ts = _parse_ts(s.get("start_time"))
        if not ts:
            continue
        key = ts.strftime("%Y-%m-%d")
        d = days[key]
        d["cost"] += s["estimated_cost"]
        d["sessions"] += 1
        d["cache_hit_sum"] += s["cache_hit_rate_pct"]
        d["waste_sum"] += s.get("waste_score", 0)
        d["by_project"][s["project_slug"]] += s["estimated_cost"]
        for c, v in (s.get("waste_scores") or {}).items():
            if v > 0:
                d["by_waste"][c] += v
    out = []
    for k in sorted(days.keys()):
        d = days[k]
        n = max(d["sessions"], 1)
        out.append({
            "date": k,
            "cost": round(d["cost"], 2),
            "sessions": d["sessions"],
            "avg_cache_hit": round(d["cache_hit_sum"] / n, 1),
            "avg_waste_score": round(d["waste_sum"] / n, 1),
            "by_project": {k2: round(v2, 2) for k2, v2 in d["by_project"].items()},
            "by_waste": {k2: round(v2, 1) for k2, v2 in d["by_waste"].items()},
        })
    return out


def build_heatmap(sessions: list[dict]) -> dict[str, dict[str, int]]:
    grid: defaultdict[int, defaultdict[int, int]] = defaultdict(lambda: defaultdict(int))
    for s in sessions:
        ts = _parse_ts(s.get("start_time"))
        if ts:
            grid[ts.weekday()][ts.hour] += 1
    return {str(d): {str(h): n for h, n in hrs.items()} for d, hrs in grid.items()}


def build_file_heat(sessions: list[dict]) -> list[dict]:
    """Aggregate file access by full absolute path (NOT basename)."""
    accesses: Counter[str] = Counter()
    tokens_by_path: dict[str, int] = {}
    sessions_by_path: defaultdict[str, set] = defaultdict(set)

    for s in sessions:
        fa = s.get("_file_accesses") or {}
        for p, n in fa.items():
            accesses[p] += n
        for p, sid_list in (s.get("_file_access_sessions") or {}).items():
            sessions_by_path[p].update(sid_list)

    # Try to read token size from disk (best-effort: paths may be inaccessible on this box)
    for p in list(accesses.keys())[:2000]:
        try:
            fp = Path(p)
            if fp.is_file():
                text = fp.read_text(encoding="utf-8", errors="replace")
                tokens_by_path[p] = _approx_tokens(text)
        except OSError:
            pass

    rows = []
    for p, n in accesses.most_common():
        tok = tokens_by_path.get(p, 0)
        apkt = round(n / (tok / 1000.0), 2) if tok > 0 else None
        rows.append({
            "path": p,
            "accesses": n,
            "tokens": tok,
            "access_per_ktoken": apkt,
            "sessions": len(sessions_by_path.get(p, set())),
        })
    # Sort priority: we want actually-wasteful reads at the top.
    #   Tier A — files with >=3 accesses AND known token size: rank by apkt desc
    #   Tier B — files with >=3 accesses but unknown size: rank by accesses desc
    #   Tier C — everything else (noise: single-access trivial files), rank by accesses
    def _tier(r):
        if r["accesses"] >= 3 and r["tokens"] > 0:
            return (0, -(r["access_per_ktoken"] or 0))
        if r["accesses"] >= 3:
            return (1, -r["accesses"])
        return (2, -r["accesses"])
    rows.sort(key=_tier)
    return rows


def aggregate_projects(sessions: list[dict], sprawl: dict[str, int]) -> list[dict]:
    by_slug: defaultdict[str, list] = defaultdict(list)
    for s in sessions:
        by_slug[s["project_slug"]].append(s)
    out = []
    for slug, ss in by_slug.items():
        cost = sum(x["estimated_cost"] for x in ss)
        dur = sum(x["duration_minutes"] for x in ss)
        # Weighted-by-cost average of category scores
        cost_sum = sum(x["estimated_cost"] for x in ss) or 1.0
        agg = {c: 0.0 for c in WASTE_CATEGORIES}
        for x in ss:
            w = (x["estimated_cost"] or 1e-6) / cost_sum
            for c in WASTE_CATEGORIES:
                agg[c] += (x.get("waste_scores") or {}).get(c, 0) * w
        spr = sprawl.get(slug, 0)
        if spr >= 3:
            agg["parallel_sprawl"] = max(agg["parallel_sprawl"], min(100, spr * 25))
        waste_scores = {c: int(round(v)) for c, v in agg.items()}
        out.append({
            "slug": slug,
            "display_name": _project_display(slug),
            "sessions": len(ss),
            "cost": round(cost, 2),
            "duration_minutes": round(dur, 1),
            "waste_scores": waste_scores,
            "total_waste": int(round(sum(waste_scores.values()) / max(
                sum(1 for v in waste_scores.values() if v > 0), 1))),
            "parallel_sprawl": spr,
        })
    out.sort(key=lambda p: -p["cost"])
    return out


def build_summary(sessions: list[dict], projects: list[dict]) -> dict:
    total_cost = sum(s["estimated_cost"] for s in sessions)
    cat_totals: dict[str, float] = {c: 0.0 for c in WASTE_CATEGORIES}
    for s in sessions:
        for c, v in (s.get("waste_scores") or {}).items():
            cat_totals[c] += v
    top = max(cat_totals, key=cat_totals.get) if any(cat_totals.values()) else None

    # Potential savings: per session, use dominant category's savings rate
    savings = 0.0
    for s in sessions:
        if s.get("waste_score", 0) < 30:
            continue
        scores = s.get("waste_scores") or {}
        rate = max(
            (CATEGORY_SAVINGS_RATE.get(c, 0.15) for c, v in scores.items() if v >= 30),
            default=0.15,
        )
        savings += s["estimated_cost"] * rate

    # Last 7d window vs prior 7d
    now = datetime.now(timezone.utc)
    last7_cut = now - timedelta(days=7)
    prior7_cut = now - timedelta(days=14)
    last7 = 0.0
    prior7 = 0.0
    for s in sessions:
        ts = _parse_ts(s.get("start_time"))
        if not ts:
            continue
        if ts >= last7_cut:
            last7 += s["estimated_cost"]
        elif ts >= prior7_cut:
            prior7 += s["estimated_cost"]
    delta_pct = None
    if prior7 > 0:
        delta_pct = round((last7 - prior7) / prior7 * 100.0, 1)

    avg_waste = (
        round(sum(s.get("waste_score", 0) for s in sessions) / max(len(sessions), 1), 1)
    )

    return {
        "total_cost": round(total_cost, 2),
        "total_sessions": len(sessions),
        "total_projects": len(projects),
        "potential_savings": round(savings, 2),
        "top_waste_category": top,
        "top_waste_label": CATEGORY_LABELS.get(top, "—") if top else "—",
        "last7_cost": round(last7, 2),
        "prior7_cost": round(prior7, 2),
        "last7_delta_pct": delta_pct,
        "avg_waste_score": avg_waste,
        "waste_category_totals": {c: round(v, 1) for c, v in cat_totals.items()},
    }


# ── Top-level build ────────────────────────────────────────────────────────


def _iter_session_files(since: datetime | None, project_filter: str | None) -> list[Path]:
    root = Path.home() / ".claude" / "projects"
    if not root.is_dir():
        return []
    out: list[Path] = []
    for f in root.rglob("*.jsonl"):
        if project_filter and project_filter.lower() not in f.parent.name.lower():
            continue
        try:
            mtime = datetime.fromtimestamp(f.stat().st_mtime, tz=timezone.utc)
        except OSError:
            continue
        if since and mtime < since:
            continue
        out.append(f)
    return sorted(out)


def build_all(days: int, project_filter: str | None) -> dict:
    since = datetime.now(timezone.utc) - timedelta(days=days)
    files = _iter_session_files(since, project_filter)

    sessions: list[dict] = []
    for f in files:
        parsed = parse_session_file(f)
        if parsed:
            sessions.append(parsed)

    if not sessions:
        return {
            "summary": {
                "total_cost": 0.0, "total_sessions": 0, "total_projects": 0,
                "potential_savings": 0.0, "top_waste_category": None,
                "top_waste_label": "—", "last7_cost": 0.0, "prior7_cost": 0.0,
                "last7_delta_pct": None, "avg_waste_score": 0.0,
                "waste_category_totals": {c: 0 for c in WASTE_CATEGORIES},
            },
            "projects": [],
            "sessions": [],
            "time_series": [],
            "heatmap": {},
            "file_heat": [],
            "thresholds": {},
            "waste_categories": {
                c: {"label": CATEGORY_LABELS[c], "color": CATEGORY_COLORS[c],
                    "fix": CATEGORY_FIXES[c]}
                for c in WASTE_CATEGORIES
            },
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "params": {"days": days, "project_filter": project_filter, "n_files": len(files)},
        }

    thr = compute_thresholds(sessions)
    # Score each session in place
    for s in sessions:
        res = score_session(s, thr)
        s["waste_scores"] = res["scores"]
        s["waste_score"] = res["total_score"]
        s["waste_evidence"] = res["evidence"]
        s["top_waste"] = res["top_waste"]

    sprawl = detect_parallel_sprawl(sessions)
    for s in sessions:
        sc = sprawl.get(s["project_slug"], 0)
        if sc >= 3:
            # Surface project sprawl into the session's own scores so radar reflects it
            s["waste_scores"]["parallel_sprawl"] = max(
                s["waste_scores"]["parallel_sprawl"], min(100, sc * 25)
            )

    projects = aggregate_projects(sessions, sprawl)
    summary = build_summary(sessions, projects)
    time_series = build_time_series(sessions)
    heatmap = build_heatmap(sessions)
    file_heat = build_file_heat(sessions)

    # Slim sessions down for JSON (keep deep-dive detail but not raw _file_accesses)
    slim = []
    for s in sessions:
        slim.append({
            "session_id": s["session_id"],
            "path": s["path"],
            "project_slug": s["project_slug"],
            "project_name": _project_display(s["project_slug"]),
            "model": s.get("model"),
            "start_time": s["start_time"],
            "end_time": s["end_time"],
            "duration_minutes": s["duration_minutes"],
            "user_turns": s["user_turns"],
            "assistant_turns": s["assistant_turns"],
            "interruptions": s["interruptions"],
            "has_compaction": s["has_compaction"],
            "has_thinking": s["has_thinking"],
            "input_tokens": s["input_tokens"],
            "output_tokens": s["output_tokens"],
            "cache_create": s["cache_create"],
            "cache_read": s["cache_read"],
            "total_tokens": s["total_tokens"],
            "cache_hit_rate_pct": s["cache_hit_rate_pct"],
            "estimated_cost": s["estimated_cost"],
            "tool_counts": s["tool_counts"],
            "total_tools": s["total_tools"],
            "first_user_message": s["first_user_message"],
            "repeat_read_pct": s["repeat_read_pct"],
            "sequential_tool_pct": s["sequential_tool_pct"],
            "waste_scores": s["waste_scores"],
            "waste_score": s["waste_score"],
            "waste_evidence": s["waste_evidence"],
            "top_waste": s["top_waste"],
            "turns": s["turns"][:500],
            "turn_costs": s["turn_costs"][:500],
            "turn_cache_pct": s["turn_cache_pct"][:500],
        })

    return {
        "summary": summary,
        "projects": projects,
        "sessions": slim,
        "time_series": time_series,
        "heatmap": heatmap,
        "file_heat": file_heat,
        "thresholds": thr,
        "waste_categories": {
            c: {"label": CATEGORY_LABELS[c], "color": CATEGORY_COLORS[c],
                "fix": CATEGORY_FIXES[c]}
            for c in WASTE_CATEGORIES
        },
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "params": {"days": days, "project_filter": project_filter, "n_files": len(files)},
    }


# ── HTML rendering ─────────────────────────────────────────────────────────

_HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>context-os forensic dashboard</title>
<style>
:root{
  --bg:#0b0f14; --panel:#11161d; --panel2:#1a2029; --border:#262e3a;
  --text:#e6edf3; --muted:#8b949e; --accent:#58a6ff; --ok:#3fb950;
  --warn:#d29922; --hi:#db6d28; --crit:#f85149;
  --mono:ui-monospace,SFMono-Regular,"SF Mono",Menlo,Consolas,monospace;
}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--text);
  font:14px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;padding:20px}
h1{margin:0 0 6px;font-size:22px;font-weight:600}
h2{margin:0 0 10px;font-size:13px;color:var(--muted);text-transform:uppercase;letter-spacing:.08em}
h3{margin:0 0 8px;font-size:14px;font-weight:600}
.meta{color:var(--muted);font-size:12px;margin-bottom:16px}
.num{font-family:var(--mono);font-variant-numeric:tabular-nums}
.grid{display:grid;gap:14px;grid-template-columns:repeat(auto-fit,minmax(280px,1fr))}
.card{background:var(--panel);border:1px solid var(--border);border-radius:10px;padding:14px;overflow:hidden}
.card.wide{grid-column:1/-1}
.card.half{grid-column:span 2}
@media(max-width:900px){.card.half{grid-column:1/-1}}
.tile-row{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:10px;margin:10px 0}
.tile{background:var(--panel2);border-radius:8px;padding:12px}
.tile .n{font-size:20px;font-weight:600;color:var(--accent);font-family:var(--mono)}
.tile .l{font-size:11px;color:var(--muted);text-transform:uppercase;letter-spacing:.05em;margin-top:4px}
.tile .sub{font-size:11px;color:var(--muted);margin-top:2px;font-family:var(--mono)}
.delta-up{color:var(--crit)} .delta-down{color:var(--ok)}
table{width:100%;border-collapse:collapse;font-size:12px}
th,td{text-align:left;padding:6px 8px;border-bottom:1px solid var(--border)}
th{color:var(--muted);font-weight:500;font-size:11px;text-transform:uppercase;cursor:pointer}
td.n{font-family:var(--mono);text-align:right}
td .sid{color:var(--accent);cursor:pointer;text-decoration:underline;font-family:var(--mono)}
.badge{display:inline-block;padding:2px 7px;border-radius:10px;font-size:10px;font-weight:600;margin-right:3px}
.b-gray{background:#30363d;color:#c9d1d9}
.b-green{background:#0f2d17;color:#3fb950}
.b-amber{background:#3a2f12;color:#d29922}
.b-red{background:#4d1017;color:#f85149}
.ctrl{display:flex;gap:8px;align-items:center;margin:0 0 10px;flex-wrap:wrap}
.ctrl button{background:var(--panel2);color:var(--text);border:1px solid var(--border);
  border-radius:6px;padding:4px 10px;cursor:pointer;font-size:12px}
.ctrl button.on{background:var(--accent);color:#000;border-color:var(--accent)}
.ctrl input{background:var(--panel2);color:var(--text);border:1px solid var(--border);
  border-radius:6px;padding:4px 8px;font-size:12px}
.bar{height:10px;background:var(--panel2);border-radius:4px;overflow:hidden}
.bar>div{height:100%;background:linear-gradient(90deg,var(--accent),#79c0ff)}
.heatmap{display:grid;grid-template-columns:36px repeat(24,1fr);gap:2px;font-family:var(--mono)}
.heatmap .h,.heatmap .d{font-size:10px;color:var(--muted);text-align:center;padding:2px}
.heatmap .cell{aspect-ratio:1;border-radius:2px;background:#0c121a}
.chart-box{position:relative;height:260px}
.chart-box.tall{height:360px}
.hidden{display:none!important}
.view-toggle a{color:var(--accent);text-decoration:none;cursor:pointer;margin-right:12px}
.fix{font-size:12px;color:var(--warn);margin-top:4px}
.ev{font-size:12px;color:var(--muted);margin-top:2px}
.cat-line{display:flex;justify-content:space-between;padding:6px 0;border-bottom:1px solid var(--border);font-size:12px;gap:8px;flex-wrap:wrap}
.cat-line .sc{font-family:var(--mono);color:var(--warn)}
.path-cell{font-family:var(--mono);font-size:11px;word-break:break-all}
.truncate{max-width:420px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;display:inline-block}
</style>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
</head>
<body>
<h1>context-os — forensic dashboard</h1>
<div class="meta">
  Generated __GENERATED_AT__
  &nbsp;·&nbsp; sessions: <span class="num">__N_SESSIONS__</span>
  &nbsp;·&nbsp; window: last <span class="num">__DAYS__</span> days
  &nbsp;·&nbsp;
  <span class="view-toggle">
    <a onclick="showOverview()" id="view-overview-link">Overview</a>
    <a onclick="showSession()" id="view-session-link" class="hidden">Deep-dive</a>
  </span>
</div>

<!-- ══════════════════════════════════ OVERVIEW ══════════════════════════════════ -->
<div id="view-overview">

<div class="grid">
  <div class="card wide">
    <h2>Overview</h2>
    <div class="tile-row">
      <div class="tile"><div class="n" id="m-cost"></div><div class="l">total cost</div></div>
      <div class="tile"><div class="n" id="m-top-waste"></div><div class="l">top waste</div></div>
      <div class="tile"><div class="n" id="m-sessions"></div><div class="l">sessions</div></div>
      <div class="tile"><div class="n" id="m-savings"></div><div class="l">potential savings</div></div>
      <div class="tile"><div class="n" id="m-last7"></div><div class="l">last 7d cost</div><div class="sub" id="m-delta"></div></div>
      <div class="tile"><div class="n" id="m-avg-waste"></div><div class="l">avg waste score</div></div>
    </div>
  </div>

  <div class="card half"><h3>Projects by waste score</h3><div class="chart-box"><canvas id="chart-projects-waste"></canvas></div></div>
  <div class="card half"><h3>Sessions: duration vs cost</h3><div class="chart-box"><canvas id="chart-scatter"></canvas></div></div>

  <div class="card half"><h3>Waste radar by project</h3><div class="chart-box"><canvas id="chart-radar"></canvas></div></div>
  <div class="card half"><h3>Cost distribution by project</h3><div class="chart-box"><canvas id="chart-donut"></canvas></div></div>

  <div class="card wide"><h3>Session activity heatmap (day × hour)</h3><div id="heatmap"></div></div>

  <div class="card half"><h3>Cost by project over time</h3><div class="chart-box"><canvas id="chart-proj-time"></canvas></div></div>
  <div class="card half"><h3>Waste breakdown over time</h3><div class="chart-box"><canvas id="chart-waste-time"></canvas></div></div>

  <div class="card half"><h3>Daily cost & sessions</h3><div class="chart-box"><canvas id="chart-cost-sessions"></canvas></div></div>
  <div class="card half"><h3>Cache hit rate & avg waste score</h3><div class="chart-box"><canvas id="chart-cache-waste"></canvas></div></div>

  <div class="card wide">
    <h3>File heat (ranked by access-per-Ktoken)</h3>
    <table id="file-heat-table">
      <thead><tr>
        <th>Path</th><th class="n">Accesses</th><th class="n">Tokens</th>
        <th class="n">Access / KTok</th><th class="n">Sessions</th>
      </tr></thead>
      <tbody></tbody>
    </table>
  </div>

  <div class="card wide">
    <h3>Sessions</h3>
    <div class="ctrl">
      <span>Window:</span>
      <button data-win="7" onclick="setWindow(7)">7d</button>
      <button data-win="14" onclick="setWindow(14)">14d</button>
      <button data-win="30" onclick="setWindow(30)" class="on">30d</button>
      <button data-win="99999" onclick="setWindow(99999)">All</button>
      <span style="margin-left:12px">Filter:</span>
      <input type="text" id="sess-filter" placeholder="project or task substring" oninput="renderSessions()">
    </div>
    <table id="sessions-table">
      <thead><tr>
        <th>Date</th><th>Session</th><th>Project</th><th>Task</th>
        <th class="n">Cost</th><th class="n">Dur (min)</th>
        <th class="n">Cache %</th><th class="n">Tools</th>
        <th class="n">Waste</th><th>Top issues</th>
      </tr></thead>
      <tbody></tbody>
    </table>
  </div>
</div>
</div><!-- /view-overview -->

<!-- ══════════════════════════════════ DEEP-DIVE ══════════════════════════════════ -->
<div id="view-session" class="hidden">
<div class="card wide">
  <div style="display:flex;justify-content:space-between;align-items:center">
    <div>
      <h1 id="ds-title" style="font-size:18px">Session deep-dive</h1>
      <div class="meta num" id="ds-meta"></div>
    </div>
    <div><a onclick="showOverview()" style="color:var(--accent);cursor:pointer">← back to overview</a></div>
  </div>
  <div class="tile-row">
    <div class="tile"><div class="n" id="ds-cost"></div><div class="l">cost</div></div>
    <div class="tile"><div class="n" id="ds-dur"></div><div class="l">duration (min)</div></div>
    <div class="tile"><div class="n" id="ds-cache"></div><div class="l">cache hit %</div></div>
    <div class="tile"><div class="n" id="ds-repeat"></div><div class="l">repeat read %</div></div>
    <div class="tile"><div class="n" id="ds-seq"></div><div class="l">sequential tools %</div></div>
    <div class="tile"><div class="n" id="ds-tools"></div><div class="l">total tools</div><div class="sub" id="ds-tools-sub"></div></div>
    <div class="tile"><div class="n" id="ds-waste"></div><div class="l">waste score</div></div>
  </div>
</div>
<div class="grid" style="margin-top:14px">
  <div class="card wide"><h3>Waste findings</h3><div id="ds-findings"></div></div>
  <div class="card half"><h3>Cache efficiency</h3>
    <div id="ds-cache-bars" style="margin-bottom:10px"></div>
    <div class="chart-box"><canvas id="ds-cache-chart"></canvas></div>
  </div>
  <div class="card half"><h3>Tool usage (top 10)</h3><div class="chart-box"><canvas id="ds-tools-chart"></canvas></div></div>
  <div class="card wide"><h3>Turn-by-turn cost</h3><div class="chart-box tall"><canvas id="ds-turn-chart"></canvas></div></div>
  <div class="card wide">
    <h3>Turn details</h3>
    <table id="ds-turn-table">
      <thead><tr><th class="n">#</th><th>Time</th>
      <th class="n">Cost</th><th class="n">Cache create %</th><th class="n">Input</th>
      <th class="n">Output</th><th>Tools</th></tr></thead>
      <tbody></tbody>
    </table>
  </div>
</div>
</div><!-- /view-session -->

<script>
// ── Data (injected) ───────────────────────────────────────────────────────
const DATA = __DATA_JSON__;
const CATS = __WASTE_CATEGORIES_JSON__;
const CAT_ORDER = Object.keys(CATS);
const PALETTE = Object.values(CATS).map(c => c.color);
Chart.defaults.color = "#c9d1d9";
Chart.defaults.borderColor = "#262e3a";
Chart.defaults.font.family = "ui-monospace,SFMono-Regular,Menlo,Consolas,monospace";

// ── Overview rendering ───────────────────────────────────────────────────
function money(n){ return n==null ? "—" : "$" + Number(n).toFixed(2); }
function fmtInt(n){ return n==null ? "—" : Number(n).toLocaleString(); }
function shortPath(p, max=70){
  if(!p) return "";
  if(p.length <= max) return p;
  const head = p.slice(0, 20);
  const tail = p.slice(-Math.max(max - head.length - 3, 10));
  return head + "…" + tail;
}

function renderHeader(){
  const s = DATA.summary || {};
  document.getElementById("m-cost").textContent = money(s.total_cost);
  document.getElementById("m-top-waste").textContent = s.top_waste_label || "—";
  document.getElementById("m-sessions").textContent = fmtInt(s.total_sessions);
  document.getElementById("m-savings").textContent = money(s.potential_savings);
  document.getElementById("m-last7").textContent = money(s.last7_cost);
  const d = s.last7_delta_pct;
  const el = document.getElementById("m-delta");
  if(d == null){ el.textContent = "no prior week"; }
  else {
    const sign = d >= 0 ? "+" : "";
    el.textContent = `${sign}${d}% vs prior week`;
    el.className = "sub " + (d >= 0 ? "delta-up" : "delta-down");
  }
  document.getElementById("m-avg-waste").textContent = s.avg_waste_score ?? "—";
}

function renderProjectsWaste(){
  const projs = (DATA.projects || []).slice(0, 12);
  const ctx = document.getElementById("chart-projects-waste");
  if(!projs.length){ ctx.parentElement.innerHTML = "<p style='color:var(--muted)'>Insufficient data</p>"; return; }
  const datasets = CAT_ORDER.map(c => ({
    label: CATS[c].label,
    data: projs.map(p => p.waste_scores[c] || 0),
    backgroundColor: CATS[c].color,
    stack: "w",
  }));
  new Chart(ctx, {
    type:"bar",
    data:{ labels: projs.map(p => p.display_name), datasets },
    options:{
      indexAxis:"y",
      maintainAspectRatio:false,
      scales:{ x:{ stacked:true, beginAtZero:true }, y:{ stacked:true } },
      plugins:{ legend:{ labels:{ boxWidth:10 }, position:"bottom" } },
    }
  });
}

function renderScatter(){
  const ctx = document.getElementById("chart-scatter");
  const sessions = DATA.sessions || [];
  if(!sessions.length){ ctx.parentElement.innerHTML="<p style='color:var(--muted)'>Insufficient data</p>"; return; }
  const byCat = {};
  sessions.forEach(s => {
    const c = s.top_waste || "_none";
    (byCat[c] = byCat[c] || []).push({ x: s.duration_minutes, y: s.estimated_cost, sid: s.session_id });
  });
  const datasets = Object.keys(byCat).map(c => ({
    label: c === "_none" ? "(no waste)" : (CATS[c]?.label || c),
    data: byCat[c],
    backgroundColor: c === "_none" ? "#6e7681" : (CATS[c]?.color || "#6e7681"),
    pointRadius: 4,
  }));
  new Chart(ctx, {
    type:"scatter", data:{datasets},
    options:{
      maintainAspectRatio:false,
      scales:{
        x:{ title:{display:true,text:"duration (min)"}, type:"logarithmic" },
        y:{ title:{display:true,text:"cost ($)"} },
      },
      plugins:{ legend:{ labels:{ boxWidth:10 }, position:"bottom" } },
    }
  });
}

function renderRadar(){
  const projs = (DATA.projects || []).slice(0, 5);
  const ctx = document.getElementById("chart-radar");
  if(!projs.length){ ctx.parentElement.innerHTML="<p style='color:var(--muted)'>Insufficient data</p>"; return; }
  const datasets = projs.map((p, i) => ({
    label: p.display_name,
    data: CAT_ORDER.map(c => p.waste_scores[c] || 0),
    backgroundColor: PALETTE[i % PALETTE.length] + "33",
    borderColor: PALETTE[i % PALETTE.length],
    pointRadius: 2,
  }));
  new Chart(ctx, {
    type:"radar",
    data:{ labels: CAT_ORDER.map(c => CATS[c].label), datasets },
    options:{ maintainAspectRatio:false, scales:{ r:{ suggestedMin:0, suggestedMax:100 } },
      plugins:{legend:{labels:{boxWidth:10}, position:"bottom"}}
    }
  });
}

function renderDonut(){
  const projs = (DATA.projects || []);
  const ctx = document.getElementById("chart-donut");
  if(!projs.length){ ctx.parentElement.innerHTML="<p style='color:var(--muted)'>Insufficient data</p>"; return; }
  const total = projs.reduce((a,p)=>a+p.cost, 0) || 1;
  const labels = projs.map(p => `${p.display_name} — $${p.cost.toFixed(2)} (${(p.cost/total*100).toFixed(1)}%)`);
  new Chart(ctx, {
    type:"doughnut",
    data:{ labels, datasets:[{ data: projs.map(p=>p.cost), backgroundColor: projs.map((_,i)=>PALETTE[i%PALETTE.length]) }] },
    options:{ maintainAspectRatio:false, plugins:{ legend:{ position:"right", labels:{boxWidth:10,font:{size:11}} } } }
  });
}

function renderHeatmap(){
  const root = document.getElementById("heatmap");
  root.className = "heatmap";
  const hm = DATA.heatmap || {};
  let max = 1;
  for(const d in hm) for(const h in hm[d]) max = Math.max(max, hm[d][h]);
  const days = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"];
  let html = '<div class="d"></div>';
  for(let h=0;h<24;h++) html += `<div class="h">${h}</div>`;
  for(let d=0; d<7; d++){
    html += `<div class="d">${days[d]}</div>`;
    for(let h=0;h<24;h++){
      const v = (hm[d] || {})[h] || 0;
      const alpha = v ? (0.15 + 0.85 * v/max).toFixed(2) : 0;
      html += `<div class="cell" style="background:rgba(88,166,255,${alpha})" title="${days[d]} ${h}:00 — ${v} sessions"></div>`;
    }
  }
  root.innerHTML = html;
}

function renderProjTime(){
  const ts = DATA.time_series || [];
  const ctx = document.getElementById("chart-proj-time");
  if(!ts.length){ ctx.parentElement.innerHTML="<p style='color:var(--muted)'>Insufficient data</p>"; return; }
  const projSet = new Set();
  ts.forEach(d => Object.keys(d.by_project||{}).forEach(k => projSet.add(k)));
  const projs = Array.from(projSet).slice(0, 8);
  const datasets = projs.map((p,i) => ({
    label: p.split("--").slice(-2).join("/"),
    data: ts.map(d => (d.by_project||{})[p] || 0),
    backgroundColor: PALETTE[i % PALETTE.length], stack:"p",
  }));
  new Chart(ctx, { type:"bar",
    data:{ labels: ts.map(d=>d.date), datasets },
    options:{ maintainAspectRatio:false, scales:{x:{stacked:true},y:{stacked:true}},
      plugins:{legend:{position:"bottom",labels:{boxWidth:10,font:{size:10}}}}
    }
  });
}

function renderWasteTime(){
  const ts = DATA.time_series || [];
  const ctx = document.getElementById("chart-waste-time");
  if(!ts.length){ ctx.parentElement.innerHTML="<p style='color:var(--muted)'>Insufficient data</p>"; return; }
  const datasets = CAT_ORDER.map(c => ({
    label: CATS[c].label,
    data: ts.map(d => (d.by_waste||{})[c] || 0),
    backgroundColor: CATS[c].color, stack:"w",
  }));
  new Chart(ctx, { type:"bar",
    data:{ labels: ts.map(d=>d.date), datasets },
    options:{ maintainAspectRatio:false, scales:{x:{stacked:true},y:{stacked:true}},
      plugins:{legend:{position:"bottom",labels:{boxWidth:10,font:{size:10}}}}
    }
  });
}

function renderCostSessions(){
  const ts = DATA.time_series || [];
  const ctx = document.getElementById("chart-cost-sessions");
  if(!ts.length){ ctx.parentElement.innerHTML="<p style='color:var(--muted)'>Insufficient data</p>"; return; }
  new Chart(ctx,{
    data:{ labels: ts.map(d=>d.date), datasets:[
      { type:"bar", label:"sessions", data:ts.map(d=>d.sessions), backgroundColor:"#58a6ff88", yAxisID:"y1" },
      { type:"line", label:"cost ($)", data:ts.map(d=>d.cost), borderColor:"#f85149", pointRadius:2, tension:0.2, yAxisID:"y" },
    ]},
    options:{ maintainAspectRatio:false, scales:{
      y:{position:"left",title:{display:true,text:"$"}},
      y1:{position:"right",grid:{drawOnChartArea:false},title:{display:true,text:"sessions"}},
    }, plugins:{legend:{position:"bottom",labels:{boxWidth:10}}}}
  });
}

function renderCacheWaste(){
  const ts = DATA.time_series || [];
  const ctx = document.getElementById("chart-cache-waste");
  if(!ts.length){ ctx.parentElement.innerHTML="<p style='color:var(--muted)'>Insufficient data</p>"; return; }
  new Chart(ctx,{
    data:{ labels: ts.map(d=>d.date), datasets:[
      { type:"line", label:"avg cache hit %", data:ts.map(d=>d.avg_cache_hit), borderColor:"#3fb950", tension:0.2, yAxisID:"y" },
      { type:"line", label:"avg waste score", data:ts.map(d=>d.avg_waste_score), borderColor:"#d29922", tension:0.2, yAxisID:"y1" },
    ]},
    options:{ maintainAspectRatio:false, scales:{
      y:{position:"left",title:{display:true,text:"cache %"}},
      y1:{position:"right",grid:{drawOnChartArea:false},title:{display:true,text:"waste"}},
    }, plugins:{legend:{position:"bottom",labels:{boxWidth:10}}}}
  });
}

function renderFileHeat(){
  const rows = (DATA.file_heat || []).slice(0, 60);
  const tbody = document.querySelector("#file-heat-table tbody");
  tbody.innerHTML = rows.map(r => `
    <tr>
      <td class="path-cell"><span class="truncate" title="${escapeHtml(r.path)}">${escapeHtml(shortPath(r.path))}</span></td>
      <td class="n">${fmtInt(r.accesses)}</td>
      <td class="n">${r.tokens ? fmtInt(r.tokens) : "—"}</td>
      <td class="n">${r.access_per_ktoken != null ? r.access_per_ktoken.toFixed(2) : "—"}</td>
      <td class="n">${fmtInt(r.sessions)}</td>
    </tr>`).join("");
}

function escapeHtml(s){ return (s||"").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;","'":"&#39;"}[c])); }

let CURR_WINDOW = 30;
function setWindow(d){
  CURR_WINDOW = d;
  document.querySelectorAll(".ctrl button[data-win]").forEach(b => {
    b.classList.toggle("on", Number(b.dataset.win) === d);
  });
  renderSessions();
}
function filterSessions(){
  const cut = Date.now() - CURR_WINDOW * 86400000;
  const q = (document.getElementById("sess-filter").value || "").toLowerCase();
  return (DATA.sessions || [])
    .filter(s => {
      const t = s.start_time ? Date.parse(s.start_time) : 0;
      if(t < cut) return false;
      if(q){
        const blob = [s.project_name, s.first_user_message, s.project_slug].join(" ").toLowerCase();
        if(!blob.includes(q)) return false;
      }
      return true;
    })
    .sort((a,b)=> (b.estimated_cost - a.estimated_cost));
}
function renderSessions(){
  const rows = filterSessions();
  const tbody = document.querySelector("#sessions-table tbody");
  tbody.innerHTML = rows.map(s => {
    const date = s.start_time ? s.start_time.slice(0,10) : "—";
    const shortId = s.session_id.slice(0, 8);
    const topIssues = Object.entries(s.waste_scores||{})
      .filter(([,v]) => v > 0)
      .sort((a,b)=>b[1]-a[1]).slice(0,3)
      .map(([c,v]) => `<span class="badge ${v>=70?'b-red':v>=40?'b-amber':'b-gray'}">${CATS[c].label} ${v}</span>`).join("");
    return `<tr>
      <td class="num">${date}</td>
      <td><span class="sid" onclick="openSession('${s.session_id}')">${shortId}</span></td>
      <td>${escapeHtml(s.project_name)}</td>
      <td><span class="truncate" title="${escapeHtml(s.first_user_message||'')}">${escapeHtml((s.first_user_message||'').slice(0,80))}</span></td>
      <td class="n">${money(s.estimated_cost)}</td>
      <td class="n">${s.duration_minutes.toFixed(1)}</td>
      <td class="n">${s.cache_hit_rate_pct.toFixed(1)}</td>
      <td class="n">${s.total_tools}</td>
      <td class="n">${s.waste_score}</td>
      <td>${topIssues || '<span class="badge b-green">clean</span>'}</td>
    </tr>`;
  }).join("");
}

// ── Deep-dive ─────────────────────────────────────────────────────────────
let DS_CHARTS = [];
function destroyDsCharts(){
  DS_CHARTS.forEach(c => { try { c.destroy(); } catch(e){} });
  DS_CHARTS = [];
}
let SESSIONS_FULL = null; // lazy cache of data/sessions.json (has per-turn detail)
async function loadSessionsFull(){
  if(SESSIONS_FULL) return SESSIONS_FULL;
  try{
    const r = await fetch("data/sessions.json");
    SESSIONS_FULL = await r.json();
  }catch(e){ SESSIONS_FULL = []; }
  return SESSIONS_FULL;
}
async function openSession(sid){
  // Merge the light inline session with its full per-turn detail (fetched once)
  const light = (DATA.sessions || []).find(x => x.session_id === sid);
  if(!light){ alert("session not in snapshot"); return; }
  const full = await loadSessionsFull();
  const heavy = (full || []).find(x => x.session_id === sid) || {};
  const s = Object.assign({}, light, {
    turns: heavy.turns || [],
    turn_costs: heavy.turn_costs || [],
    turn_cache_pct: heavy.turn_cache_pct || [],
  });
  destroyDsCharts();
  document.getElementById("ds-title").textContent = "Session " + sid.slice(0,12);
  document.getElementById("ds-meta").textContent = `${s.project_name} · ${s.start_time || ""} · ${s.model || ""}`;
  document.getElementById("ds-cost").textContent = money(s.estimated_cost);
  document.getElementById("ds-dur").textContent = s.duration_minutes.toFixed(1);
  const cache = s.cache_hit_rate_pct;
  document.getElementById("ds-cache").textContent = cache.toFixed(1);
  const rr = s.repeat_read_pct;
  const rrEl = document.getElementById("ds-repeat");
  rrEl.textContent = rr == null ? "—" : rr.toFixed(1);
  rrEl.style.color = rr == null ? "" : (rr < 15 ? "var(--ok)" : rr < 30 ? "var(--warn)" : "var(--crit)");
  const seq = s.sequential_tool_pct;
  const seqEl = document.getElementById("ds-seq");
  seqEl.textContent = seq == null ? "—" : seq.toFixed(1);
  seqEl.style.color = seq == null ? "" : (seq < 40 ? "var(--ok)" : seq < 60 ? "var(--warn)" : "var(--crit)");
  document.getElementById("ds-tools").textContent = s.total_tools;
  const p95 = (DATA.thresholds||{}).total_tools_p95 || 0;
  document.getElementById("ds-tools-sub").textContent = `p95 baseline ${Math.round(p95)}`;
  document.getElementById("ds-waste").textContent = s.waste_score;

  // Findings
  const findings = document.getElementById("ds-findings");
  const ev = s.waste_evidence || {};
  const ordered = CAT_ORDER.filter(c => ev[c]);
  if(!ordered.length){
    findings.innerHTML = '<p style="color:var(--muted)">No waste findings. This session looks clean.</p>';
  } else {
    findings.innerHTML = ordered.map(c => `
      <div class="cat-line">
        <div>
          <strong>${CATS[c].label}</strong>
          <div class="ev">${escapeHtml(ev[c].evidence || "")}</div>
          <div class="fix">WHAT TO CHANGE: ${escapeHtml(ev[c].fix || "")}</div>
        </div>
        <div class="sc">${ev[c].score}</div>
      </div>
    `).join("");
  }

  // Cache bars + per-turn cache
  const cc = s.cache_create, cr = s.cache_read;
  const reuse = cc > 0 ? (cr/cc) : 0;
  const hitBar = Math.min(100, cache);
  const reuseBar = Math.min(100, reuse * 5); // 20× = full
  document.getElementById("ds-cache-bars").innerHTML = `
    <div style="font-size:11px;color:var(--muted);margin-bottom:4px">Hit rate: ${cache.toFixed(1)}%</div>
    <div class="bar"><div style="width:${hitBar}%"></div></div>
    <div style="font-size:11px;color:var(--muted);margin:8px 0 4px">Reuse ratio: ${reuse.toFixed(1)}×</div>
    <div class="bar"><div style="width:${reuseBar}%"></div></div>
  `;
  const cacheCtx = document.getElementById("ds-cache-chart");
  DS_CHARTS.push(new Chart(cacheCtx, {
    type:"line",
    data:{ labels: (s.turn_cache_pct||[]).map((_,i)=>i+1),
      datasets:[{ label:"cache read % of turn", data: s.turn_cache_pct || [], borderColor:"#58a6ff", tension:0.25, spanGaps:true, pointRadius:0 }]
    },
    options:{ maintainAspectRatio:false, scales:{ y:{min:0,max:100}} }
  }));

  // Tool chart
  const tc = s.tool_counts || {};
  const sorted = Object.entries(tc).sort((a,b)=>b[1]-a[1]).slice(0,10);
  const tCtx = document.getElementById("ds-tools-chart");
  DS_CHARTS.push(new Chart(tCtx, {
    type:"bar",
    data:{ labels:sorted.map(x=>x[0]), datasets:[{label:"calls", data:sorted.map(x=>x[1]), backgroundColor:"#58a6ff"}]},
    options:{ indexAxis:"y", maintainAspectRatio:false, plugins:{legend:{display:false}} }
  }));

  // Turn-by-turn
  const turnCtx = document.getElementById("ds-turn-chart");
  const costs = s.turn_costs || [];
  DS_CHARTS.push(new Chart(turnCtx, {
    type:"bar",
    data:{ labels:costs.map((_,i)=>i+1), datasets:[{label:"cost $", data:costs, backgroundColor:"#f85149"}]},
    options:{ maintainAspectRatio:false, plugins:{legend:{display:false}},
      onClick:(e, els) => { if(els.length){ const row = document.querySelectorAll("#ds-turn-table tbody tr")[els[0].index]; if(row) row.scrollIntoView({behavior:"smooth",block:"center"}); }}
    }
  }));

  // Turn table
  const tbody = document.querySelector("#ds-turn-table tbody");
  tbody.innerHTML = (s.turns || []).map((t,i) => {
    const cc2 = t.cache_create + t.cache_read;
    const pct = cc2 > 0 ? (t.cache_create/cc2*100).toFixed(1) : "—";
    return `<tr><td class="n">${i+1}</td>
      <td class="num">${(t.timestamp||'').slice(11,19)}</td>
      <td class="n">${money(t.cost)}</td>
      <td class="n">${pct}</td>
      <td class="n">${fmtInt(t.input_tokens)}</td>
      <td class="n">${fmtInt(t.output_tokens)}</td>
      <td>${(t.tools||[]).join(", ")}</td>
    </tr>`;
  }).join("");

  showSession();
}
function showSession(){
  document.getElementById("view-overview").classList.add("hidden");
  document.getElementById("view-session").classList.remove("hidden");
  document.getElementById("view-session-link").classList.remove("hidden");
  document.getElementById("view-overview-link").style.color = "var(--muted)";
  document.getElementById("view-session-link").style.color = "var(--accent)";
  window.scrollTo({top:0,behavior:"smooth"});
}
function showOverview(){
  document.getElementById("view-overview").classList.remove("hidden");
  document.getElementById("view-session").classList.add("hidden");
  document.getElementById("view-session-link").classList.add("hidden");
  document.getElementById("view-overview-link").style.color = "var(--accent)";
}

// ── Boot ─────────────────────────────────────────────────────────────────
renderHeader();
renderProjectsWaste();
renderScatter();
renderRadar();
renderDonut();
renderHeatmap();
renderProjTime();
renderWasteTime();
renderCostSessions();
renderCacheWaste();
renderFileHeat();
renderSessions();
</script>
</body>
</html>
"""


def render_html(bundle: dict) -> str:
    """Produce the single-file dashboard HTML.

    We strip per-turn arrays from the embedded payload to keep index.html
    light; deep-dive lazy-loads full turn data from data/sessions.json.
    """
    waste = bundle["waste_categories"]
    inline = dict(bundle)
    inline["sessions"] = [
        {k: v for k, v in s.items() if k not in ("turns", "turn_costs", "turn_cache_pct")}
        for s in bundle["sessions"]
    ]
    return (
        _HTML_TEMPLATE
        .replace("__GENERATED_AT__", html.escape(bundle["generated_at"]))
        .replace("__N_SESSIONS__", str(len(bundle["sessions"])))
        .replace("__DAYS__", str(bundle["params"]["days"]))
        .replace("__DATA_JSON__", json.dumps(inline, default=str))
        .replace("__WASTE_CATEGORIES_JSON__", json.dumps(waste))
    )


def write_dashboard(out_dir: Path, days: int, project_filter: str | None) -> Path:
    """Build bundle, write data/*.json + index.html, return path to index.html."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    data_dir = out_dir / "data"
    data_dir.mkdir(exist_ok=True)

    bundle = build_all(days=days, project_filter=project_filter)

    # Per-chart JSON drops (schema-discovering)
    (data_dir / "summary.json").write_text(
        json.dumps(bundle["summary"], indent=2), encoding="utf-8"
    )
    (data_dir / "projects.json").write_text(
        json.dumps(bundle["projects"], indent=2), encoding="utf-8"
    )
    (data_dir / "sessions.json").write_text(
        json.dumps(bundle["sessions"], indent=2, default=str), encoding="utf-8"
    )
    (data_dir / "time_series.json").write_text(
        json.dumps(bundle["time_series"], indent=2), encoding="utf-8"
    )
    (data_dir / "heatmap.json").write_text(
        json.dumps(bundle["heatmap"], indent=2), encoding="utf-8"
    )
    (data_dir / "file_heat.json").write_text(
        json.dumps(bundle["file_heat"], indent=2), encoding="utf-8"
    )
    (data_dir / "waste_categories.json").write_text(
        json.dumps(bundle["waste_categories"], indent=2), encoding="utf-8"
    )
    (data_dir / "thresholds.json").write_text(
        json.dumps(bundle["thresholds"], indent=2), encoding="utf-8"
    )

    idx = out_dir / "index.html"
    idx.write_text(render_html(bundle), encoding="utf-8")
    return idx
