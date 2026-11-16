#!/usr/bin/env python3
"""
Per-stage timing for skill runs: durations, a waterfall chart and aggregates.

The source of truth is the executor's transcript (a JSONL file, one message per
line with an ISO timestamp). Time between a tool result (or the prompt) and the
assistant message that follows is model time: thinking plus writing the tool
input. Time between that message and its tool result is tool time. Each
interval belongs to the stage the executor declared in the tool call it was
making, so a stage that is slow because the model writes a lot shows up as
model time, and one that is slow because a script is slow as tool time.

The executor declares a stage at no cost by putting a marker in the call it is
about to make:
- Bash: the first line of the command is a comment, `# stage: collect-stats`
- any other tool: a text line `stage: collect-stats` in the same message,
  before the tool call
- `# stage: end` / `stage: end` after the last stage; what follows is handback

A stage lasts until the next declaration, so calls without a marker belong to
the stage before them. The stages themselves (ordered, with a one-line
description each) are listed once per iteration in <iteration-dir>/stages.json.
Timing.json in a run directory points at the transcript ("transcript_path", or
"agent_id" to look it up under ~/.claude/projects/*/*/subagents/); a
transcript.jsonl in the run directory is found without it.

Total time reconciles: stage time + startup (before the first stage) + handback
(after the last) + unattributed (gaps, tool calls with no result) equals the
transcript's wall time within a second, and this is checked in code.

Without a transcript (claude.ai), the older <run-dir>/stages.jsonl is used, one
JSON object per line:

    {"stage": "extract", "event": "start", "t": 1768473000.12}
    {"stage": "extract", "event": "end",   "t": 1768473012.80}

Those marks only cover shell execution, so that chart is labelled
"shell-only marks: model time not attributed". Legacy mark commands found in a
transcript's tool inputs are also understood as stage declarations.

This script turns that into:
- <run-dir>/stage_timing.json: per-stage durations (model/tool split, output
  tokens), startup, handback, unattributed time and the gaps it found
- <iteration-dir>/stage_timing.json: mean and stddev per stage per configuration
- <iteration-dir>/waterfall.svg: a standalone waterfall chart of those means

Missing or unreadable input never raises: it is reported as gaps.

Usage:
    python -m scripts.stage_timing <iteration-dir> [--previous <iteration-dir>]

aggregate_benchmark.py calls this too, so a normal benchmark run needs no
separate step.
"""

import argparse
import datetime
import json
import math
import os
import re
import sys
from pathlib import Path
from xml.sax.saxutils import escape

STAGES_FILE = "stages.json"
MARKS_FILE = "stages.jsonl"
MARKS_LABEL = "shell-only marks: model time not attributed"
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
        "source": "marks",
        "stages": stages,
        "total_seconds": None if total_seconds is None else round(total_seconds, 4),
        "accounted_seconds": round(accounted, 4),
        "unaccounted_seconds": unaccounted,
        "gaps": gaps,
    }


# ---------------------------------------------------------------------------
# Transcript-based timing
#
# The executor's transcript is the source of truth for where wall time went.
# Every line has a timestamp. Time between a tool_result (or the prompt) and
# the assistant message that follows is model time: thinking plus writing the
# tool input. Time between that message and its tool_result is tool time.
# Each interval belongs to the stage the executor declared in the tool call.
# ---------------------------------------------------------------------------

END_STAGE = "end"
RECONCILE_TOLERANCE_SECONDS = 1.0
UNATTRIBUTED = "\0unattributed"
STARTUP = "\0startup"
HANDBACK = "\0handback"

# `# stage: name` (Bash command, must be the first non-blank line) or `stage: name` (a description or a text line)
STAGE_LINE = re.compile(r"^[ \t]*(#[ \t]*)?stage:[ \t]*([A-Za-z0-9][A-Za-z0-9_.-]*)[ \t]*$", re.MULTILINE | re.IGNORECASE)
# Legacy marks, from runs that appended {"stage": ..., "event": ...} lines to stages.jsonl with python3 -c
LEGACY_JSON = re.compile(r'"stage"\s*:\s*"([A-Za-z0-9][\w.-]*)"\s*,\s*"event"\s*:\s*"(start|end)"')
LEGACY_HELPER_DEF = re.compile(r"(\w+)\(\)\s*\{[^}]*[\"']stage[\"']")
# Tool calls that are bookkeeping, not work: before the first stage they are startup, after the last one handback
BOOKKEEPING_TOOL = re.compile(r"checklist|todo|handback|narrate|^task(create|update)", re.IGNORECASE)


def extract_markers(text: str, kind: str = "command") -> list[dict]:
    """
    Stage declarations in one piece of text, in order: [{"stage", "event", "pos"}].

    kind is where the text came from:
      command      a Bash command: `# stage: name` as the first non-blank line, plus legacy mark forms anywhere
      description  a tool's description field: `stage: name` as the first non-blank line
      text         an assistant text block: `stage: name` on any line
    `stage: end` declares that no stage is running any more (event "end", stage None).
    """
    kind = "command" if kind == "Bash" else kind
    found = []
    if kind == "text":
        matches = list(STAGE_LINE.finditer(text))
    else:
        first = re.search(r"\S", text)
        line = STAGE_LINE.match(text, text.rfind("\n", 0, first.start()) + 1) if first else None
        matches = [line] if line and (kind == "description" or line.group(1)) else []
    for m in matches:
        name = m.group(2)
        found.append({"stage": None if name.lower() == END_STAGE else name,
                      "event": "end" if name.lower() == END_STAGE else "start", "pos": m.start()})
    if kind == "command":
        for m in LEGACY_JSON.finditer(text):
            found.append({"stage": m.group(1), "event": m.group(2), "pos": m.start()})
        for helper in LEGACY_HELPER_DEF.findall(text):
            call = re.compile(r"(?<![\w$])" + re.escape(helper) + r"[ \t]+['\"]?([A-Za-z0-9][\w.-]*)['\"]?[ \t]+(start|end)\b")
            for m in call.finditer(text):
                found.append({"stage": m.group(1), "event": m.group(2), "pos": m.start()})
    return sorted(found, key=lambda f: f["pos"])


def parse_timestamp(value):
    """An ISO timestamp as epoch seconds, or None."""
    if not isinstance(value, str):
        return None
    try:
        return datetime.datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp()
    except ValueError:
        return None


def read_transcript(path: Path) -> tuple[list[dict], list[str]]:
    """The JSON lines of a transcript. Lines that are not JSON objects are skipped and reported."""
    try:
        raw = path.read_text(encoding="utf-8").splitlines()
    except OSError as e:
        return [], [f"transcript {path} cannot be read ({e})"]
    lines, gaps = [], []
    for number, line in enumerate(raw, start=1):
        if not line.strip():
            continue
        try:
            item = json.loads(line)
        except ValueError:
            item = None
        if isinstance(item, dict):
            lines.append(item)
        else:
            gaps.append(f"line {number} of the transcript is not a JSON object, so it is ignored")
    return lines, gaps


def string_values(value, key=None):
    """Every string in a tool input, with the key it sits under."""
    if isinstance(value, str):
        yield key, value
    elif isinstance(value, dict):
        for k, v in value.items():
            yield from string_values(v, k)
    elif isinstance(value, list):
        for v in value:
            yield from string_values(v, key)


def build_calls(lines: list[dict]):
    """
    Group the transcript into model turns. Returns (turns, results, first_ts, last_ts).

    A turn is one assistant message (its blocks may be spread over several
    lines, even with other lines in between): {"id", "first_ts", "last_ts",
    "units", "tools", "tokens"}. units are the strings the model wrote, in
    order, as (call id or None, kind, text); tools are (call id, tool name).
    results maps a tool_use id to the time its tool_result arrived.
    """
    turns: dict[str, dict] = {}
    results: dict[str, float] = {}
    stamps = []
    for index, line in enumerate(lines):
        ts = parse_timestamp(line.get("timestamp"))
        if ts is not None:
            stamps.append(ts)
        message = line.get("message") if isinstance(line.get("message"), dict) else None
        if message is None or ts is None:
            continue
        content = message.get("content")
        if line.get("type") == "assistant" and isinstance(content, list):
            key = message.get("id") if isinstance(message.get("id"), str) else f"line-{index}"
            turn = turns.setdefault(key, {"id": key, "first_ts": ts, "last_ts": ts, "units": [], "tools": [], "tokens": None, "index": index})
            turn["last_ts"] = max(turn["last_ts"], ts)
            usage = message.get("usage")
            if isinstance(usage, dict) and is_number(usage.get("output_tokens")):
                turn["tokens"] = max(turn["tokens"] or 0, usage["output_tokens"])
            for block in content:
                if not isinstance(block, dict):
                    continue
                if block.get("type") == "text" and isinstance(block.get("text"), str):
                    turn["units"].append((None, "text", block["text"]))
                elif block.get("type") == "tool_use" and isinstance(block.get("id"), str):
                    call_id = block["id"]
                    turn["tools"].append((call_id, str(block.get("name") or "")))
                    for k, text in string_values(block.get("input")):
                        turn["units"].append((call_id, "command" if k == "command" else "description" if k == "description" else "other", text))
        elif line.get("type") == "user" and isinstance(content, list):
            for block in content:
                if isinstance(block, dict) and block.get("type") == "tool_result" and isinstance(block.get("tool_use_id"), str):
                    results.setdefault(block["tool_use_id"], ts)
    ordered = sorted(turns.values(), key=lambda t: t["index"])
    return ordered, results, (min(stamps) if stamps else None), (max(stamps) if stamps else None)


def split_pieces(turn: dict) -> list[dict]:
    """A turn's text cut at stage declarations: [{"call", "marker", "weight"}], in the order the model wrote them."""
    pieces = []
    for call_id, kind, text in turn["units"]:
        markers = extract_markers(text, kind) if kind != "other" else []
        at = {}
        for m in markers:
            at.setdefault(m["pos"], m)
        cuts = sorted({0, len(text)} | {pos for pos in at if 0 < pos < len(text)})
        for start, end in zip(cuts, cuts[1:]):
            pieces.append({"call": call_id, "marker": at.get(start), "weight": max(end - start, 1)})
        if len(cuts) == 1:
            pieces.append({"call": call_id, "marker": at.get(0), "weight": 1})
    return pieces


def switches(marker) -> bool:
    """Whether a marker changes the running stage: a start, or `stage: end`. Legacy end marks do not."""
    return bool(marker) and (marker["event"] == "start" or marker["stage"] is None)


def resolve_stages(pieces: list[dict], current):
    """
    Give every piece a stage. Returns (pieces with "stage", the stage after the turn, whether the turn declares one).

    A start marker switches the stage and `stage: end` ends it (stage None). A
    legacy end mark is ignored: the work after it belongs to the stage until
    the next start. Text before the turn's first marker belongs to that
    marker's stage, because it is the preparation for it; when the turn
    declares several stages that setup text (variables, helper definitions)
    serves all of them, so it is left out of how the model time is shared.
    """
    first = next((p["marker"] for p in pieces if switches(p["marker"])), None)
    cur, leading, resolved = current, True, []
    for piece in pieces:
        if switches(piece["marker"]):
            cur, leading = piece["marker"]["stage"], False
        resolved.append(dict(piece, stage=first["stage"] if first and leading else cur, lead=bool(first and leading)))
    return resolved, cur, first is not None


def add_segment(segments: list[dict], a: float, b: float, kind: str, stage, turn_index: int, tokens: float = 0.0):
    if b < a:
        b = a
    segments.append({"a": a, "b": b, "kind": kind, "stage": stage, "turn": turn_index, "tokens": tokens})


def share_out(total: float, parts: list[tuple[object, float]]) -> list[tuple[object, float]]:
    """Split total over parts in proportion to their weights."""
    weight = sum(w for _, w in parts)
    if not parts:
        return []
    if weight <= 0:
        return [(key, total / len(parts)) for key, _ in parts]
    return [(key, total * w / weight) for key, w in parts]


def merge_runs(items: list[tuple[object, float]]) -> list[tuple[object, float]]:
    """Join neighbouring entries with the same key, summing their values."""
    merged: list[list] = []
    for key, value in items:
        if merged and merged[-1][0] == key:
            merged[-1][1] += value
        else:
            merged.append([key, value])
    return [(k, v) for k, v in merged]


def split_tool_window(a: float, b: float, runs: list[tuple[object, float]], marks: list[dict], gaps: list[str], call_id: str):
    """
    Split one tool call's execution window [a, b] over the stages it declares.

    With the stage marks the run recorded (legacy runs), a stage owns the time
    from its own start mark to the next stage's start mark. Without them the
    window is split evenly, and that is reported, because only calls that
    declare a single stage can be timed exactly.
    """
    stages = [k for k, _ in runs]
    if len(stages) == 1:
        return [(stages[0], a, b)]
    bounds = []
    for stage in stages[1:]:
        times = [m["t"] for m in marks if m["stage"] == stage and m["event"] == "start" and a - 0.5 <= m["t"] <= b + 0.5]
        bounds.append(min(times) if times else None)
    if all(t is not None for t in bounds) and bounds == sorted(bounds):
        edges = [a] + [min(max(t, a), b) for t in bounds] + [b]
        return [(stage, edges[i], edges[i + 1]) for i, stage in enumerate(stages)]
    gaps.append(f"tool call {call_id} declares {len(stages)} stages and the run has no usable stage marks for them, so its time is split evenly; declare one stage per call for exact timing")
    step = (b - a) / len(stages)
    return [(stage, a + i * step, a + (i + 1) * step) for i, stage in enumerate(stages)]


def compute_transcript_run(lines: list[dict], sidecar_marks: list[dict] | None = None, known_stages: list[str] | tuple = (), gaps: list[str] | None = None) -> dict:
    """
    Per-stage timing of one run from its transcript lines.

    sidecar_marks (the parsed stages.jsonl) only refines how a legacy command
    that batches several stage marks is split. The result's wall_seconds is the
    transcript's first to last timestamp; stage time, startup, handback and
    unattributed time add up to it.
    """
    gaps = list(gaps or [])
    marks = sidecar_marks or []
    turns, results, t0, t_end = build_calls(lines)
    if t0 is None:
        return finish_run([], 0.0, 0.0, [], known_stages, gaps + ["the transcript holds no timestamped lines"])

    segments: list[dict] = []
    cursor = t0
    current = None
    seen_stage = False
    marked_turns: set[int] = set()
    bookkeeping_turns: set[int] = set()
    for index, turn in enumerate(turns):
        pieces, after, saw = resolve_stages(split_pieces(turn), current)
        if saw:
            marked_turns.add(index)
        if all(BOOKKEEPING_TOOL.search(name) for _, name in turn["tools"]) and not saw:
            bookkeeping_turns.add(index)
        seen_stage = seen_stage or any(p["stage"] is not None for p in pieces)

        def label(stage):
            return stage if stage is not None else HANDBACK if seen_stage else STARTUP

        # Model time: from the end of the previous turn to the last line of this message
        gen_start = cursor
        gen_end = max(cursor, turn["last_ts"])
        weight_by_stage: dict = {}
        body = [p for p in pieces if not p["lead"]]
        for p in body if len({label(q["stage"]) for q in body}) > 1 else pieces:
            key = label(p["stage"])
            weight_by_stage[key] = weight_by_stage.get(key, 0) + p["weight"]
        parts = list(weight_by_stage.items()) or [(label(current), 1)]
        tokens = turn["tokens"] or 0
        position = gen_start
        for (key, seconds), (_, token_share) in zip(share_out(gen_end - gen_start, parts), share_out(tokens, parts)):
            add_segment(segments, position, position + seconds, "model", key, index, token_share)
            position += seconds
        cursor = gen_end
        current = after

        # Tool time: every call's window ends when its tool_result arrives
        if not turn["tools"]:
            continue
        next_start = turns[index + 1]["first_ts"] if index + 1 < len(turns) else gen_end
        by_call: dict[str, list[tuple[object, float]]] = {}
        for p in pieces:
            if p["call"]:
                by_call.setdefault(p["call"], []).append((label(p["stage"]), p["weight"]))
        carry = label(current)
        ends = []
        for call_id, name in turn["tools"]:
            if call_id in results:
                ends.append((max(results[call_id], gen_end), call_id, True))
            else:
                gaps.append(f"tool call {call_id} ({name}) has no tool_result, so its execution time is unattributed")
                ends.append((max(next_start, gen_end), call_id, False))
        ends.sort(key=lambda e: (e[0], not e[2]))
        for end, call_id, found in ends:
            window_start, window_end = cursor, max(cursor, end)
            if not found:
                add_segment(segments, window_start, window_end, "tool", UNATTRIBUTED, index)
            else:
                runs = merge_runs(by_call.get(call_id) or [(carry, 1)])
                for key, a, b in split_tool_window(window_start, window_end, runs, marks, gaps, call_id):
                    add_segment(segments, a, b, "tool", key, index)
            cursor = window_end
    add_segment(segments, cursor, max(cursor, t_end), "model", HANDBACK, len(turns))

    # Bookkeeping turns after the last stage work are handback, not the stage's
    last_marked = max(marked_turns) if marked_turns else -1
    trailing = len(turns)
    while trailing - 1 > last_marked and trailing - 1 in bookkeeping_turns:
        trailing -= 1
    for segment in segments:
        if segment["turn"] >= trailing and segment["stage"] not in (UNATTRIBUTED, STARTUP) and marked_turns:
            segment["stage"] = HANDBACK
    wall = max(t_end - t0, 0.0)
    return finish_run(segments, wall, t0, turns, known_stages, gaps)


def finish_run(segments: list[dict], wall: float, t0: float, turns, known_stages, gaps: list[str]) -> dict:
    """Sum the segments into per-stage durations and check that they add up to the wall time."""
    stage_names = []
    for s in segments:
        if s["stage"] not in (UNATTRIBUTED, STARTUP, HANDBACK) and s["stage"] not in stage_names:
            stage_names.append(s["stage"])
    rows = {}
    for name in stage_names:
        mine = [s for s in segments if s["stage"] == name]
        model = sum(s["b"] - s["a"] for s in mine if s["kind"] == "model")
        tool = sum(s["b"] - s["a"] for s in mine if s["kind"] == "tool")
        real = [s for s in mine if s["b"] > s["a"]] or mine
        rows[name] = {
            "name": name,
            "start_offset_seconds": round(min(s["a"] for s in real) - t0, 4),
            "duration_seconds": round(model + tool, 4),
            "model_seconds": round(model, 4),
            "tool_seconds": round(tool, 4),
            "output_tokens": round(sum(s["tokens"] for s in mine), 1),
            "intervals": len({s["turn"] for s in mine}),
        }
    names = [n for n in known_stages if n in rows] + [n for n in stage_names if n not in known_stages]
    for name in stage_names:
        if known_stages and name not in known_stages:
            gaps.append(f"stage {name} is not listed in {STAGES_FILE}")

    def total_of(stage):
        return sum(s["b"] - s["a"] for s in segments if s["stage"] == stage)

    startup, handback, unattributed = total_of(STARTUP), total_of(HANDBACK), total_of(UNATTRIBUTED)
    if not names and wall > 0:
        unattributed += startup + handback
        startup = handback = 0.0
        gaps.append("no stage declarations were found in the transcript, so none of the time is attributed to a stage")
    result = {
        "source": "transcript",
        "stages": [rows[n] for n in names],
        "total_seconds": round(wall, 4),
        "wall_seconds": round(wall, 4),
        "startup_seconds": round(startup, 4),
        "handback_seconds": round(handback, 4),
        "accounted_seconds": round(sum(rows[n]["duration_seconds"] for n in names), 4),
        "unattributed_seconds": round(unattributed, 4),
        "unaccounted_seconds": round(unattributed, 4),
        "gaps": gaps,
    }
    check_reconciliation(result)
    return result


def check_reconciliation(run: dict) -> None:
    """Stage time + startup + handback + unattributed must equal the transcript's wall time within a second."""
    parts = (sum(s["duration_seconds"] or 0.0 for s in run["stages"]) + run["startup_seconds"]
             + run["handback_seconds"] + run["unattributed_seconds"])
    if abs(parts - run["wall_seconds"]) > RECONCILE_TOLERANCE_SECONDS:
        raise ValueError(f"stage timing does not add up: parts {parts:.2f}s, transcript wall time {run['wall_seconds']:.2f}s")


def find_transcript(run_dir: Path, home: Path | None = None):
    """
    The executor's transcript for a run, or None. Looked up in this order:
    timing.json "transcript_path" (absolute, or relative to the run directory),
    <run-dir>/transcript.jsonl, then timing.json "agent_id" under
    ~/.claude/projects/*/*/subagents/agent-<id>.jsonl.
    """
    timing = read_json(run_dir / "timing.json")
    timing = timing if isinstance(timing, dict) else {}
    declared = timing.get("transcript_path")
    if isinstance(declared, str) and declared:
        path = Path(declared).expanduser()
        path = path if path.is_absolute() else run_dir / path
        if path.is_file():
            return path
    default = run_dir / "transcript.jsonl"
    if default.is_file():
        return default
    agent_id = timing.get("agent_id")
    if isinstance(agent_id, str) and re.fullmatch(r"[A-Za-z0-9]+", agent_id):
        roots = [Path(p) for p in [os.environ.get("CLAUDE_CONFIG_DIR")] if p] if home is None else []
        roots.append((home or Path.home()) / ".claude")
        for root in roots:
            for candidate in sorted(root.glob(f"projects/*/*/subagents/agent-{agent_id}.jsonl")):
                return candidate
    return None


def analyze_run(run_dir: Path, known_stages: list[str]):
    """
    Compute one run's stage timing: from its transcript when there is one,
    else from stages.jsonl. None when the run has neither.
    """
    marks_path = run_dir / MARKS_FILE
    marks, mark_gaps = parse_marks(marks_path) if marks_path.exists() else ([], [])
    transcript = find_transcript(run_dir)
    note = []
    if transcript is not None:
        lines, gaps = read_transcript(transcript)
        if any(parse_timestamp(line.get("timestamp")) is not None for line in lines):
            try:
                result = compute_transcript_run(lines, marks, known_stages, gaps)
                result["transcript"] = transcript.name
                return result
            except ValueError as e:
                note.append(f"transcript {transcript.name} gave inconsistent timing ({e}), so the marks are used")
        else:
            note.append(f"transcript {transcript.name} has no timestamped lines, so the marks are used")
        note += gaps[:3]
    if not marks_path.exists():
        return None
    if not marks:
        mark_gaps.append(f"{MARKS_FILE} holds no usable marks")
    result = compute_run(marks, note + mark_gaps, known_stages, total_seconds_of(run_dir))
    return result


def stats_of(rows: list[dict], key: str):
    values = [r[key] for r in rows if is_number(r.get(key))]
    return calculate_stats(values) if values else None


def aggregate(per_config: dict[str, list[tuple[str, dict]]], definitions: list[dict], run_counts: dict[str, int]) -> dict:
    """
    per_config maps a configuration to [(run label, run result)] for the runs with timing.
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
                for key in ("model_seconds", "tool_seconds", "output_tokens"):
                    stat = stats_of(rows, key)
                    if stat:
                        stages[name][key] = stat
        results = [r for _, r in runs]
        totals = [r["total_seconds"] for r in results if r["total_seconds"] is not None]
        unaccounted = [r["unaccounted_seconds"] for r in results if r["unaccounted_seconds"] is not None]
        sources = {r.get("source", "marks") for r in results}
        configurations[config] = {
            "runs": len(runs),
            "runs_total": run_counts.get(config, len(runs)),
            "source": sources.pop() if len(sources) == 1 else "mixed",
            "stages": stages,
            "total_seconds": calculate_stats(totals) if totals else None,
            "startup_seconds": stats_of(results, "startup_seconds"),
            "handback_seconds": stats_of(results, "handback_seconds"),
            "unaccounted_seconds": calculate_stats(unaccounted) if unaccounted else None,
        }
        for label, result in runs:
            gaps.extend({"run": label, "issue": g} for g in result["gaps"])
        if len(runs) < run_counts.get(config, len(runs)):
            gaps.append({"run": config, "issue": f"only {len(runs)} of {run_counts[config]} runs have a transcript or {MARKS_FILE}"})
    kinds = {c["source"] for c in configurations.values()}
    return {
        "source": kinds.pop() if len(kinds) == 1 else "mixed",
        "stages": definitions or [{"name": n, "description": ""} for n in order],
        "configurations": configurations,
        "gaps": gaps,
    }


def build_stage_timing(iteration_dir: Path, runs: list[tuple[str, str, Path]]):
    """
    Analyze every run, write each run's stage_timing.json and return the aggregate.

    runs is a list of (configuration, run label, run directory). Returns None
    when no run has a transcript or a stages.jsonl, so callers can skip the
    stage section.
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
svg.wf .seg-model { fill: #5c6bc0; }
svg.wf .seg-tool { fill: #26a69a; }
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


def has_split(panel_data: dict) -> bool:
    """Whether a panel's stages carry the model/tool split (they do when they come from a transcript)."""
    return any("model_seconds" in s and "tool_seconds" in s for s in panel_data.get("stages", {}).values())


def render_waterfall_svg(stage_timing: dict, previous: dict | None = None, standalone: bool = False) -> str:
    """
    Waterfall chart as one SVG string: a panel per configuration (and the
    previous iteration), a row per stage, each bar starting at the stage's mean
    start offset. A bar from a transcript is stacked: model time, then tool
    time, with a legend. A bar from shell-only marks is one colour and the
    chart says so. All panels share one time axis so they can be compared.
    """
    panels = panels_for(stage_timing, previous)
    names = [s["name"] for s in stage_timing.get("stages", [])]
    for panel in panels:
        names += [n for n in panel["data"].get("stages", {}) if n not in names]

    width, label_w, right_pad, top_pad = 640, 118, 96, 8
    row_h, axis_h, panel_gap = 20, 20, 12
    any_split = any(has_split(p["data"]) for p in panels)
    any_marks = any(not has_split(p["data"]) for p in panels)
    title_h = 36 if any_split else 22
    legend_h = 20 if (any_split or any_marks) else 0
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
    height = top_pad + legend_h + max(len(panels), 1) * (panel_h + panel_gap)
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" class="wf{" wf-standalone" if standalone else ""}" '
        f'viewBox="0 0 {width} {height}" width="100%" role="img" aria-label="Stage duration waterfall">',
        f"<style>{SVG_STYLE}{(chr(10) + SVG_STANDALONE_DARK) if standalone else ''}</style>",
    ]
    if standalone:
        parts.append(f'<rect class="bg" width="{width}" height="{height}"/>')
    if not panels or not names:
        parts.append(f'<text x="{width // 2}" y="24" text-anchor="middle" class="muted">No stage timing recorded</text>')

    if legend_h:
        x = 0
        parts.append(f'<g class="legend" transform="translate(0,{top_pad + 4})">')
        if any_split:
            for label, css in (("model (thinking and writing tool input)", "model"), ("tool (execution)", "tool")):
                parts.append(f'<rect class="seg-{css}" x="{x}" y="0" width="10" height="10" rx="2"/>')
                parts.append(f'<text x="{x + 14}" y="9">{escape(label)}</text>')
                x += 14 + 6 * len(label) + 12
        if any_marks:
            parts.append(f'<text class="muted" x="{x}" y="9">{escape(MARKS_LABEL if any_split else "Chart note: " + MARKS_LABEL)}</text>')
        parts.append("</g>")

    for p_index, panel in enumerate(panels):
        data = panel["data"]
        y0 = top_pad + legend_h + p_index * (panel_h + panel_gap)
        color = BAR_COLORS[min(p_index, len(BAR_COLORS) - 1)]
        split = has_split(data)
        total = (data.get("total_seconds") or {}).get("mean")
        unaccounted = (data.get("unaccounted_seconds") or {}).get("mean")
        title = f"{panel['label']} ({data.get('runs', 0)} of {data.get('runs_total', data.get('runs', 0))} runs timed)"
        if total is not None:
            title += f" - total {total:.1f}s"
        if unaccounted is not None and not split:
            title += f", unaccounted {unaccounted:.1f}s"
        parts.append(f'<text class="title" x="0" y="{y0 + 14}">{escape(title)}</text>')
        if split:
            extra = []
            for key, label in (("startup_seconds", "startup"), ("handback_seconds", "handback"), ("unaccounted_seconds", "unattributed")):
                value = (data.get(key) or {}).get("mean")
                if value is not None:
                    extra.append(f"{label} {value:.1f}s")
            parts.append(f'<text class="muted" x="0" y="{y0 + 29}">{escape(" · ".join(extra))}</text>')
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
            model = (stage.get("model_seconds") or {}).get("mean")
            tool = (stage.get("tool_seconds") or {}).get("mean")
            detail = f"{name}: {duration:.1f}s +/- {stddev:.1f}s, starts at {start:.1f}s, {stage['runs']} runs"
            if model is not None and tool is not None:
                detail += f", model {model:.1f}s, tool {tool:.1f}s"
                tokens = (stage.get("output_tokens") or {}).get("mean")
                if tokens:
                    detail += f", {tokens:.0f} output tokens"
                model_w = min(bar_w * (model / duration if duration > 0 else 0.5), bar_w)
                x = x_of(start)
                parts.append(f'<rect class="seg-model" x="{x:.1f}" y="{y + 3}" width="{model_w:.1f}" height="{row_h - 6}" rx="2"><title>{escape(detail)}</title></rect>')
                parts.append(f'<rect class="seg-tool" x="{x + model_w:.1f}" y="{y + 3}" width="{bar_w - model_w:.1f}" height="{row_h - 6}" rx="2"><title>{escape(detail)}</title></rect>')
            else:
                parts.append(f'<rect x="{x_of(start):.1f}" y="{y + 3}" width="{bar_w:.1f}" height="{row_h - 6}" rx="2" fill="{color}"><title>{escape(detail)}</title></rect>')
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
    split = any("model_seconds" in r for c in stage_timing["configurations"].values() for r in c["stages"].values())
    lines = [
        "## Stage Timing",
        "",
        "| Stage | " + " | ".join(c.replace("_", " ").title() for c in configs) + " |",
        "|-------|" + "|".join("---" for _ in configs) + "|",
    ]

    def cell(stats):
        return f"{stats['mean']:.1f}s ± {stats['stddev']:.1f}s" if stats else "—"

    for stage in stage_timing["stages"]:
        cells = []
        for config in configs:
            row = stage_timing["configurations"][config]["stages"].get(stage["name"])
            text = cell(row["duration_seconds"]) if row else "—"
            if row and "model_seconds" in row and "tool_seconds" in row:
                text += f" (model {row['model_seconds']['mean']:.1f}s / tool {row['tool_seconds']['mean']:.1f}s"
                tokens = (row.get("output_tokens") or {}).get("mean")
                text += f", {tokens:.0f} tokens)" if tokens else ")"
            cells.append(text)
        lines.append(f"| {stage['name']} | " + " | ".join(cells) + " |")
    extra = [("startup", "startup_seconds"), ("handback", "handback_seconds")] if split else []
    for label, key in extra:
        lines.append(f"| {label} | " + " | ".join(cell(stage_timing["configurations"][c].get(key)) for c in configs) + " |")
    lines.append(f"| {'unattributed' if split else 'unaccounted'} | " + " | ".join(cell(stage_timing["configurations"][c]["unaccounted_seconds"]) for c in configs) + " |")
    counts = ", ".join(f"{c}: {d['runs']} of {d['runs_total']}" for c, d in stage_timing["configurations"].items())
    lines.extend(["", f"Runs with timing: {counts}."])
    sources = {c: d.get("source", "marks") for c, d in stage_timing["configurations"].items()}
    if all(v == "transcript" for v in sources.values()):
        lines.append("Source: executor transcript timestamps. Stage time + startup + handback + unattributed = transcript wall time.")
    else:
        flagged = ", ".join(c for c, v in sources.items() if v != "transcript")
        lines.append(f"Source for {flagged}: {MARKS_LABEL}.")
    if stage_timing["gaps"]:
        lines.extend(["", f"{len(stage_timing['gaps'])} gap(s) in the timing input; see stage_timing.json."])
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
        print(f"No transcript or {MARKS_FILE} with stage markers found under {args.iteration_dir}, so there is no stage timing.", file=sys.stderr)
        sys.exit(1)
    for path in write_artifacts(args.iteration_dir, stage_timing, args.previous):
        print(f"Generated: {path}")
    for gap in stage_timing["gaps"]:
        print(f"Gap in {gap['run']}: {gap['issue']}")


if __name__ == "__main__":
    main()
