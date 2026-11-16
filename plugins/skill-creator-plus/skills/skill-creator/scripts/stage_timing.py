#!/usr/bin/env python3
"""
Per-stage timing for skill runs: durations, a waterfall chart and aggregates.

Each run can record stage boundary marks in <run-dir>/stages.jsonl, one JSON
object per line:

    {"stage": "extract", "event": "start", "t": 1768473000.12}
    {"stage": "extract", "event": "end",   "t": 1768473012.80}

The stages themselves (ordered, with a one-line description each) are listed
once per iteration in <iteration-dir>/stages.json.

This script turns the marks into:
- <run-dir>/stage_timing.json: per-stage durations and start offsets of one
  run, the time no stage accounts for, and the gaps it found in the marks
- <iteration-dir>/stage_timing.json: mean and stddev per stage per configuration
- <iteration-dir>/waterfall.svg: a standalone waterfall chart of those means

Missing, unbalanced or unreadable marks never raise: they are reported as gaps.

Usage:
    python -m scripts.stage_timing <iteration-dir> [--previous <iteration-dir>]

aggregate_benchmark.py calls this too, so a normal benchmark run needs no
separate step.
"""

import argparse
import json
import math
import re
import sys
from pathlib import Path
from xml.sax.saxutils import escape

STAGES_FILE = "stages.json"
MARKS_FILE = "stages.jsonl"
RUN_OUTPUT = "stage_timing.json"
AGGREGATE_OUTPUT = "stage_timing.json"
WATERFALL_OUTPUT = "waterfall.svg"


def read_json(path: Path):
    """Return the parsed JSON in a file, or None when it is missing or unreadable."""
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def is_number(value) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def calculate_stats(values: list[float]) -> dict:
    """Mean, stddev (sample), min and max, in the same shape aggregate_benchmark uses."""
    if not values:
        return {"mean": 0.0, "stddev": 0.0, "min": 0.0, "max": 0.0}
    mean = sum(values) / len(values)
    stddev = math.sqrt(sum((x - mean) ** 2 for x in values) / (len(values) - 1)) if len(values) > 1 else 0.0
    return {
        "mean": round(mean, 4),
        "stddev": round(stddev, 4),
        "min": round(min(values), 4),
        "max": round(max(values), 4),
    }


def load_stage_definitions(iteration_dir: Path) -> list[dict]:
    """The ordered stage list from stages.json: [{"name": ..., "description": ...}]. Empty when absent."""
    data = read_json(iteration_dir / STAGES_FILE)
    stages = data.get("stages") if isinstance(data, dict) else data
    result = []
    for item in stages if isinstance(stages, list) else []:
        if isinstance(item, str):
            item = {"name": item}
        if isinstance(item, dict) and isinstance(item.get("name"), str) and item["name"]:
            result.append({"name": item["name"], "description": str(item.get("description") or "")})
    return result


def parse_marks(path: Path) -> tuple[list[dict], list[str]]:
    """Read stages.jsonl. Returns (valid marks, gap messages). A missing file gives ([], [])."""
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return [], []
    marks, gaps = [], []
    for number, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        try:
            mark = json.loads(line)
        except ValueError:
            gaps.append(f"line {number} of {MARKS_FILE} is not JSON, so it is ignored")
            continue
        if (
            not isinstance(mark, dict)
            or not isinstance(mark.get("stage"), str)
            or mark.get("event") not in ("start", "end")
            or not is_number(mark.get("t"))
        ):
            gaps.append(f"line {number} of {MARKS_FILE} needs stage, event (start or end) and a numeric t, so it is ignored")
            continue
        marks.append({"stage": mark["stage"], "event": mark["event"], "t": float(mark["t"]), "order": len(marks)})
    return marks, gaps


def merge_intervals(intervals: list[tuple[float, float]]) -> list[tuple[float, float]]:
    """Union of intervals, sorted, with overlapping or touching ones joined."""
    merged: list[list[float]] = []
    for start, end in sorted(intervals):
        if merged and start <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], end)
        else:
            merged.append([start, end])
    return [(s, e) for s, e in merged]


def total_seconds_of(run_dir: Path):
    """The run's total duration from timing.json, or None."""
    timing = read_json(run_dir / "timing.json")
    if not isinstance(timing, dict):
        return None
    if is_number(timing.get("total_duration_seconds")):
        return float(timing["total_duration_seconds"])
    if is_number(timing.get("duration_ms")):
        return timing["duration_ms"] / 1000.0
    return None


def compute_run(marks: list[dict], gaps: list[str], known_stages: list[str], total_seconds=None) -> dict:
    """
    Turn one run's marks into per-stage durations.

    A stage's duration is the union of its own start/end pairs. A stage that is
    open inside another one (nesting) keeps its own time and the outer stage
    keeps its time too, so stage durations may add up to more than the run; the
    accounted time is the union over all stages and counts every second once.
    Start offsets are relative to the earliest valid start.
    """
    gaps = list(gaps)
    # Marks are ordered by time; marks with the same time keep the order they were written in
    ordered = sorted(marks, key=lambda m: (m["t"], m["order"]))
    open_at: dict[str, float] = {}
    intervals: dict[str, list[tuple[float, float]]] = {}
    seen_order: list[str] = []
    for mark in ordered:
        stage = mark["stage"]
        if stage not in seen_order:
            seen_order.append(stage)
        if mark["event"] == "start":
            if stage in open_at:
                gaps.append(f"stage {stage} started again at {mark['t']:.2f} before it ended, so the second start is ignored")
            else:
                open_at[stage] = mark["t"]
        elif stage in open_at:
            intervals.setdefault(stage, []).append((open_at.pop(stage), mark["t"]))
        else:
            gaps.append(f"stage {stage} ended at {mark['t']:.2f} without a start, so it is ignored")
    for stage in open_at:
        gaps.append(f"stage {stage} has no end mark, so its duration is unknown and left out")

    # Marks that are not in stages.json still show up, after the known ones
    names = [s for s in known_stages if s in seen_order] + [s for s in seen_order if s not in known_stages]
    for stage in seen_order:
        if known_stages and stage not in known_stages:
            gaps.append(f"stage {stage} is not listed in {STAGES_FILE}")

    all_starts = [iv[0] for ivs in intervals.values() for iv in ivs]
    origin = min(all_starts) if all_starts else None
    stages = []
    for stage in names:
        merged = merge_intervals(intervals.get(stage, []))
        if merged:
            stages.append({
                "name": stage,
                "start_offset_seconds": round(merged[0][0] - origin, 4),
                "duration_seconds": round(sum(e - s for s, e in merged), 4),
                "intervals": len(intervals[stage]),
            })
        else:
            stages.append({"name": stage, "start_offset_seconds": None, "duration_seconds": None, "intervals": 0})

    # Nesting or overlap: any two stages whose intervals cross
    flat = sorted((s, e, stage) for stage, ivs in intervals.items() for s, e in ivs)
    reported = set()
    for i, (s1, e1, a) in enumerate(flat):
        for s2, e2, b in flat[i + 1:]:
            if s2 >= e1:
                break
            if a != b and (a, b) not in reported:
                reported.add((a, b))
                kind = "nested in" if e2 <= e1 else "overlaps"
                gaps.append(f"stage {b} {kind} stage {a}, so their durations share time")

    accounted = sum(e - s for s, e in merge_intervals([iv for ivs in intervals.values() for iv in ivs]))
    unaccounted = None
    if total_seconds is not None:
        unaccounted = round(max(total_seconds - accounted, 0.0), 4)
        if accounted > total_seconds + 0.5:
            gaps.append(f"stages add up to {accounted:.1f}s, more than the {total_seconds:.1f}s recorded in timing.json")
    return {
        "stages": stages,
        "total_seconds": None if total_seconds is None else round(total_seconds, 4),
        "accounted_seconds": round(accounted, 4),
        "unaccounted_seconds": unaccounted,
        "gaps": gaps,
    }


def analyze_run(run_dir: Path, known_stages: list[str]):
    """Compute one run's stage timing. None when the run has no stages.jsonl."""
    marks_path = run_dir / MARKS_FILE
    if not marks_path.exists():
        return None
    marks, gaps = parse_marks(marks_path)
    if not marks:
        gaps.append(f"{MARKS_FILE} holds no usable marks")
    return compute_run(marks, gaps, known_stages, total_seconds_of(run_dir))


def aggregate(per_config: dict[str, list[tuple[str, dict]]], definitions: list[dict], run_counts: dict[str, int]) -> dict:
    """
    per_config maps a configuration to [(run label, compute_run result)] for the runs with marks.
    run_counts maps it to the number of runs it has in total.
    """
    known = [d["name"] for d in definitions]
    order = list(known)
    for runs in per_config.values():
        for _, result in runs:
            for stage in result["stages"]:
                if stage["name"] not in order:
                    order.append(stage["name"])

    configurations = {}
    gaps = []
    for config, runs in per_config.items():
        stages = {}
        for name in order:
            rows = [s for _, r in runs for s in r["stages"] if s["name"] == name and s["duration_seconds"] is not None]
            if rows:
                stages[name] = {
                    "duration_seconds": calculate_stats([s["duration_seconds"] for s in rows]),
                    "start_offset_seconds": calculate_stats([s["start_offset_seconds"] for s in rows]),
                    "runs": len(rows),
                }
        totals = [r["total_seconds"] for _, r in runs if r["total_seconds"] is not None]
        unaccounted = [r["unaccounted_seconds"] for _, r in runs if r["unaccounted_seconds"] is not None]
        configurations[config] = {
            "runs": len(runs),
            "runs_total": run_counts.get(config, len(runs)),
            "stages": stages,
            "total_seconds": calculate_stats(totals) if totals else None,
            "unaccounted_seconds": calculate_stats(unaccounted) if unaccounted else None,
        }
        for label, result in runs:
            gaps.extend({"run": label, "issue": g} for g in result["gaps"])
        if len(runs) < run_counts.get(config, len(runs)):
            gaps.append({"run": config, "issue": f"only {len(runs)} of {run_counts[config]} runs have {MARKS_FILE}"})
    return {"stages": definitions or [{"name": n, "description": ""} for n in order], "configurations": configurations, "gaps": gaps}


def build_stage_timing(iteration_dir: Path, runs: list[tuple[str, str, Path]]):
    """
    Analyze every run, write each run's stage_timing.json and return the aggregate.

    runs is a list of (configuration, run label, run directory). Returns None
    when no run has a stages.jsonl, so callers can skip the stage section.
    """
    definitions = load_stage_definitions(iteration_dir)
    known = [d["name"] for d in definitions]
    per_config: dict[str, list[tuple[str, dict]]] = {}
    run_counts: dict[str, int] = {}
    for config, label, run_dir in runs:
        run_counts[config] = run_counts.get(config, 0) + 1
        result = analyze_run(run_dir, known)
        if result is None:
            continue
        per_config.setdefault(config, []).append((label, result))
        try:
            (run_dir / RUN_OUTPUT).write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        except OSError as e:
            print(f"Warning: cannot write {run_dir / RUN_OUTPUT} ({e})", file=sys.stderr)
    if not per_config:
        return None
    return aggregate(per_config, definitions, run_counts)


# ---------------------------------------------------------------------------
# Waterfall chart
# ---------------------------------------------------------------------------

# Bars use the same blue and amber as the benchmark table rows
BAR_COLORS = ["#2196f3", "#ffc107", "#9e9e9e"]

SVG_STYLE = """
svg.wf { --wf-text: var(--text, #141413); --wf-muted: var(--text-muted, #6b6a63); --wf-grid: var(--border, #e8e6dc); --wf-bg: var(--surface, #ffffff); font-family: Poppins, system-ui, sans-serif; }
svg.wf .bg { fill: var(--wf-bg); }
svg.wf text { fill: var(--wf-text); font-size: 11px; }
svg.wf .muted { fill: var(--wf-muted); }
svg.wf .title { font-weight: 600; font-size: 12px; }
svg.wf .grid { stroke: var(--wf-grid); stroke-width: 1; }
svg.wf .gap { fill: none; stroke: var(--wf-muted); stroke-dasharray: 3 2; }
""".strip()

# A standalone file has no page around it, so it follows the reader's colour scheme itself
SVG_STANDALONE_DARK = """
@media (prefers-color-scheme: dark) { svg.wf-standalone { --wf-text: #faf9f5; --wf-muted: #b0aea5; --wf-grid: #3a3935; --wf-bg: #1f1e1b; } }
""".strip()


def nice_step(maximum: float) -> float:
    """A tick spacing that gives about 4 to 6 ticks up to maximum."""
    if maximum <= 0:
        return 1.0
    raw = maximum / 5
    magnitude = 10 ** math.floor(math.log10(raw))
    for factor in (1, 2, 5, 10):
        if raw <= factor * magnitude:
            return factor * magnitude
    return 10 * magnitude


def panels_for(stage_timing: dict, previous: dict | None) -> list[dict]:
    """The chart's panels: each configuration, then the previous iteration's matching one."""
    panels = []
    configs = stage_timing.get("configurations", {})
    for config, data in configs.items():
        panels.append({"label": config.replace("_", " ").title(), "data": data})
    if previous and configs:
        prev_configs = previous.get("configurations", {})
        match = next(iter(configs)) if next(iter(configs)) in prev_configs else next(iter(prev_configs), None)
        if match:
            panels.append({"label": f"{match.replace('_', ' ').title()} (previous iteration)", "data": prev_configs[match]})
    return panels


def render_waterfall_svg(stage_timing: dict, previous: dict | None = None, standalone: bool = False) -> str:
    """
    Waterfall chart as one SVG string: a panel per configuration (and the
    previous iteration), a row per stage, each bar starting at the stage's mean
    start offset. All panels share one time axis so they can be compared.
    """
    panels = panels_for(stage_timing, previous)
    names = [s["name"] for s in stage_timing.get("stages", [])]
    for panel in panels:
        names += [n for n in panel["data"].get("stages", {}) if n not in names]

    width, label_w, right_pad, top_pad = 640, 118, 96, 8
    row_h, title_h, axis_h, panel_gap = 20, 22, 20, 12
    plot_w = width - label_w - right_pad

    maximum = 0.0
    for panel in panels:
        data = panel["data"]
        total = (data.get("total_seconds") or {}).get("mean") or 0.0
        maximum = max(maximum, total)
        for stage in data.get("stages", {}).values():
            maximum = max(maximum, stage["start_offset_seconds"]["mean"] + stage["duration_seconds"]["mean"])
    step = nice_step(maximum)
    axis_max = math.ceil(maximum / step) * step if maximum > 0 else step

    def x_of(seconds: float) -> float:
        return label_w + plot_w * seconds / axis_max

    panel_h = title_h + row_h * len(names) + axis_h
    height = top_pad + max(len(panels), 1) * (panel_h + panel_gap)
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" class="wf{" wf-standalone" if standalone else ""}" '
        f'viewBox="0 0 {width} {height}" width="100%" role="img" aria-label="Stage duration waterfall">',
        f"<style>{SVG_STYLE}{(chr(10) + SVG_STANDALONE_DARK) if standalone else ''}</style>",
    ]
    if standalone:
        parts.append(f'<rect class="bg" width="{width}" height="{height}"/>')
    if not panels or not names:
        parts.append(f'<text x="{width // 2}" y="24" text-anchor="middle" class="muted">No stage timing recorded</text>')

    for p_index, panel in enumerate(panels):
        data = panel["data"]
        y0 = top_pad + p_index * (panel_h + panel_gap)
        color = BAR_COLORS[min(p_index, len(BAR_COLORS) - 1)]
        total = (data.get("total_seconds") or {}).get("mean")
        unaccounted = (data.get("unaccounted_seconds") or {}).get("mean")
        title = f"{panel['label']} ({data.get('runs', 0)} of {data.get('runs_total', data.get('runs', 0))} runs marked)"
        if total is not None:
            title += f" - total {total:.1f}s"
        if unaccounted is not None:
            title += f", unaccounted {unaccounted:.1f}s"
        parts.append(f'<text class="title" x="0" y="{y0 + 14}">{escape(title)}</text>')
        rows_top = y0 + title_h
        # Grid lines and axis labels
        tick = 0.0
        while tick <= axis_max + 1e-9:
            x = x_of(tick)
            parts.append(f'<line class="grid" x1="{x:.1f}" y1="{rows_top}" x2="{x:.1f}" y2="{rows_top + row_h * len(names)}"/>')
            parts.append(f'<text class="muted" x="{x:.1f}" y="{rows_top + row_h * len(names) + 13}" text-anchor="middle">{tick:g}s</text>')
            tick += step
        for r_index, name in enumerate(names):
            y = rows_top + r_index * row_h
            parts.append(f'<text x="{label_w - 6}" y="{y + 14}" text-anchor="end">{escape(name)}</text>')
            stage = data.get("stages", {}).get(name)
            if not stage:
                parts.append(f'<text class="muted" x="{label_w + 4}" y="{y + 14}">no data</text>')
                continue
            start = stage["start_offset_seconds"]["mean"]
            duration = stage["duration_seconds"]["mean"]
            stddev = stage["duration_seconds"]["stddev"]
            bar_w = max(plot_w * duration / axis_max, 1.5)
            parts.append(
                f'<rect x="{x_of(start):.1f}" y="{y + 3}" width="{bar_w:.1f}" height="{row_h - 6}" rx="2" fill="{color}">'
                f"<title>{escape(name)}: {duration:.1f}s +/- {stddev:.1f}s, starts at {start:.1f}s, {stage['runs']} runs</title></rect>"
            )
            parts.append(f'<text class="muted" x="{x_of(start) + bar_w + 4:.1f}" y="{y + 14}">{duration:.1f}s ± {stddev:.1f}</text>')
    parts.append("</svg>")
    return "\n".join(parts)


def previous_iteration_dir(iteration_dir: Path):
    """iteration-N's sibling iteration-(N-1), when it exists."""
    match = re.fullmatch(r"(.*iteration-)(\d+)", iteration_dir.name)
    if not match or int(match.group(2)) <= 1:
        return None
    candidate = iteration_dir.parent / f"{match.group(1)}{int(match.group(2)) - 1}"
    return candidate if candidate.is_dir() else None


def load_aggregate(iteration_dir: Path | None):
    """An iteration's aggregate stage timing: its stage_timing.json, else the section of its benchmark.json."""
    if iteration_dir is None:
        return None
    for path, key in ((iteration_dir / AGGREGATE_OUTPUT, None), (iteration_dir / "benchmark.json", "stage_timing")):
        data = read_json(path)
        data = data.get(key) if key and isinstance(data, dict) else data
        if isinstance(data, dict) and isinstance(data.get("configurations"), dict):
            return data
    return None


def write_artifacts(iteration_dir: Path, stage_timing: dict, previous_dir: Path | None = None) -> list[Path]:
    """Write the iteration's stage_timing.json and waterfall.svg. Returns the paths written."""
    previous = load_aggregate(previous_dir or previous_iteration_dir(iteration_dir))
    written = []
    for name, content in (
        (AGGREGATE_OUTPUT, json.dumps(stage_timing, indent=2) + "\n"),
        (WATERFALL_OUTPUT, render_waterfall_svg(stage_timing, previous, standalone=True) + "\n"),
    ):
        path = iteration_dir / name
        try:
            path.write_text(content, encoding="utf-8")
            written.append(path)
        except OSError as e:
            print(f"Warning: cannot write {path} ({e})", file=sys.stderr)
    return written


def markdown_table(stage_timing: dict) -> str:
    """The stage table for benchmark.md: one column per configuration, mean ± stddev in seconds."""
    configs = list(stage_timing["configurations"])
    lines = [
        "## Stage Timing",
        "",
        "| Stage | " + " | ".join(c.replace("_", " ").title() for c in configs) + " |",
        "|-------|" + "|".join("---" for _ in configs) + "|",
    ]
    for stage in stage_timing["stages"]:
        cells = []
        for config in configs:
            row = stage_timing["configurations"][config]["stages"].get(stage["name"])
            cells.append(f"{row['duration_seconds']['mean']:.1f}s ± {row['duration_seconds']['stddev']:.1f}s" if row else "—")
        lines.append(f"| {stage['name']} | " + " | ".join(cells) + " |")
    cells = []
    for config in configs:
        stats = stage_timing["configurations"][config]["unaccounted_seconds"]
        cells.append(f"{stats['mean']:.1f}s ± {stats['stddev']:.1f}s" if stats else "—")
    lines.append("| unaccounted | " + " | ".join(cells) + " |")
    counts = ", ".join(f"{c}: {d['runs']} of {d['runs_total']}" for c, d in stage_timing["configurations"].items())
    lines.extend(["", f"Runs with stage marks: {counts}."])
    if stage_timing["gaps"]:
        lines.extend(["", f"{len(stage_timing['gaps'])} gap(s) in the marks; see stage_timing.json."])
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Compute per-stage timing and a waterfall chart for an iteration")
    parser.add_argument("iteration_dir", type=Path, help="Path to the iteration directory")
    parser.add_argument("--previous", type=Path, default=None, help="Previous iteration directory (default: iteration-(N-1) beside this one)")
    args = parser.parse_args()
    if not args.iteration_dir.is_dir():
        print(f"Directory not found: {args.iteration_dir}")
        sys.exit(1)

    try:
        from scripts.aggregate_benchmark import find_eval_dirs, find_run_dirs
    except ImportError:
        from aggregate_benchmark import find_eval_dirs, find_run_dirs
    search_dir = args.iteration_dir / "runs" if (args.iteration_dir / "runs").exists() else args.iteration_dir
    runs = []
    for eval_dir in find_eval_dirs(search_dir):
        for config_dir in sorted(p for p in eval_dir.iterdir() if p.is_dir()):
            for number, run_dir in find_run_dirs(config_dir):
                runs.append((config_dir.name, f"{eval_dir.name}/{config_dir.name}/run-{number}", run_dir))

    stage_timing = build_stage_timing(args.iteration_dir, runs)
    if stage_timing is None:
        print(f"No {MARKS_FILE} found under {args.iteration_dir}, so there is no stage timing.", file=sys.stderr)
        sys.exit(1)
    for path in write_artifacts(args.iteration_dir, stage_timing, args.previous):
        print(f"Generated: {path}")
    for gap in stage_timing["gaps"]:
        print(f"Gap in {gap['run']}: {gap['issue']}")


if __name__ == "__main__":
    main()
