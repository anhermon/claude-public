#!/usr/bin/env python3
"""
file_map — identify context bloat from repeatedly re-read large files.

Scans cc-lens session replays for Read/Edit/Write tool calls, aggregates
by absolute file path, measures on-disk size/line-count, and flags bloat
candidates.

Usage:
    context-os filemap [--days 30] [--min-reads 3] [--min-lines 800]
                       [--min-size 100000] [--output PATH]
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.request
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta, timezone
from pathlib import Path

try:
    from context_os.cc_lens_url import resolve_cc_lens_base_url
except Exception:  # pragma: no cover
    def resolve_cc_lens_base_url() -> str:
        import os
        return os.environ.get("CC_LENS_BASE_URL", "http://localhost:3000").rstrip("/")


READ_LIKE_TOOLS = ("Read", "Edit", "MultiEdit", "Write")
LINE_COUNT_CAP_BYTES = 2 * 1024 * 1024  # read at most 2MB when counting newlines


def _api_get(base: str, path: str, timeout: int = 60):
    url = f"{base}{path}"
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8", errors="replace"))
    except Exception as e:
        print(f"[file_map] GET {path}: {e}", file=sys.stderr)
        return None


def _fetch_sessions_list(base: str) -> list[dict]:
    data = _api_get(base, "/api/sessions", timeout=60) or []
    if isinstance(data, dict):
        data = data.get("sessions", [])
    return data if isinstance(data, list) else []


def _parse_ts(raw) -> datetime | None:
    if not raw or not isinstance(raw, str):
        return None
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except Exception:
        return None


def _fetch_replay(base: str, sid: str) -> dict | None:
    data = _api_get(base, f"/api/sessions/{sid}/replay", timeout=90)
    return data if isinstance(data, dict) else ({"turns": data} if isinstance(data, list) else None)


def _normalize_path(raw: str) -> Path | None:
    if not raw or not isinstance(raw, str):
        return None
    try:
        p = Path(raw)
        # resolve without following symlinks to avoid escape; strict=False for missing files
        try:
            return p.resolve(strict=False)
        except OSError:
            return p.absolute()
    except (OSError, ValueError):
        return None


def _count_lines_bounded(p: Path, cap: int = LINE_COUNT_CAP_BYTES) -> int:
    """Count newlines in the first `cap` bytes. Cheap approximation for huge files."""
    count = 0
    try:
        with open(p, "rb") as f:
            remaining = cap
            while remaining > 0:
                chunk = f.read(min(65536, remaining))
                if not chunk:
                    break
                count += chunk.count(b"\n")
                remaining -= len(chunk)
    except OSError:
        return 0
    return count + 1  # last line may not end with newline


def _suggest(read_count: int, lines: int, size: int, path: Path) -> str:
    name = path.name.lower()
    if any(seg in str(path).lower() for seg in ("node_modules", "dist", "build", ".next", "vendor", "__pycache__", ".venv", "venv")):
        return "add to .claudeignore (generated/vendored)"
    if name.endswith((".min.js", ".lock", ".map", ".bundle.js")):
        return "add to .claudeignore (generated/vendored)"
    if lines > 2000 or size > 200_000:
        return "split into modules"
    if read_count >= 5:
        return "extract the 3 most-read regions and create a CLAUDE.md pointer"
    return "split into modules"


def scan_file_map(
    base_url: str,
    days: int = 30,
    min_reads: int = 3,
    min_lines: int = 800,
    min_size: int = 100_000,
    max_workers: int = 8,
) -> dict:
    """Main entry point. Returns the JSON-serializable result dict."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    sessions = _fetch_sessions_list(base_url)
    recent = []
    for s in sessions:
        ts = _parse_ts(s.get("start_time"))
        if ts and ts >= cutoff:
            recent.append(s)
    print(f"[file_map] {len(recent)}/{len(sessions)} sessions in last {days}d", flush=True)

    # Aggregators keyed by resolved path string
    read_count: dict[str, int] = defaultdict(int)
    session_set: dict[str, set] = defaultdict(set)
    offsets: dict[str, set] = defaultdict(set)
    total_lines: dict[str, int] = defaultdict(int)
    last_ts: dict[str, str] = {}

    sids = [s.get("session_id") for s in recent if s.get("session_id")]

    def _one(sid: str):
        data = _fetch_replay(base_url, sid)
        if not data:
            return sid, []
        turns = data.get("turns", []) if isinstance(data, dict) else data
        events = []
        for t in turns:
            if not isinstance(t, dict) or t.get("type") != "assistant":
                continue
            ts = t.get("timestamp") or ""
            for tc in (t.get("tool_calls") or []):
                if not isinstance(tc, dict):
                    continue
                name = tc.get("name")
                if name not in READ_LIKE_TOOLS:
                    continue
                inp = tc.get("input") or {}
                if not isinstance(inp, dict):
                    continue
                fp = inp.get("file_path") or inp.get("path")
                if not fp:
                    continue
                events.append({
                    "path": fp,
                    "offset": inp.get("offset"),
                    "limit": inp.get("limit"),
                    "tool": name,
                    "ts": ts,
                })
        return sid, events

    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        futs = {ex.submit(_one, sid): sid for sid in sids}
        done = 0
        for fut in as_completed(futs):
            done += 1
            if done % 25 == 0:
                print(f"[file_map] processed {done}/{len(sids)} replays", flush=True)
            try:
                sid, events = fut.result()
            except Exception:
                continue
            for ev in events:
                p = _normalize_path(ev["path"])
                if p is None:
                    continue
                key = str(p)
                read_count[key] += 1
                session_set[key].add(sid)
                off = ev.get("offset")
                lim = ev.get("limit")
                if off is not None or lim is not None:
                    offsets[key].add((off, lim))
                else:
                    offsets[key].add((None, None))
                if lim:
                    try:
                        total_lines[key] += int(lim)
                    except (TypeError, ValueError):
                        pass
                ts = ev.get("ts") or ""
                if ts and ts > last_ts.get(key, ""):
                    last_ts[key] = ts

    # Enrich with on-disk stats
    entries = []
    for key, n in read_count.items():
        p = Path(key)
        size = 0
        lines = 0
        exists = False
        try:
            st = p.stat()
            exists = True
            size = st.st_size
            if st.st_size > 0:
                lines = _count_lines_bounded(p)
        except OSError:
            pass
        except Exception:
            pass
        if not exists:
            continue
        distinct_off = len(offsets[key])
        tl = total_lines[key]
        avg_lines = round(tl / n, 1) if n > 0 and tl > 0 else None
        flagged = (n >= min_reads and lines > min_lines) or (n >= max(min_reads, 5) and size > min_size)
        entry = {
            "path": key,
            "read_count": n,
            "sessions_affected": len(session_set[key]),
            "distinct_offsets_count": distinct_off,
            "total_lines_read": tl or None,
            "avg_lines_per_read": avg_lines,
            "last_read_ts": last_ts.get(key),
            "file_size_bytes": size,
            "file_line_count": lines,
            "bloat": bool(flagged),
            "suggestion": _suggest(n, lines, size, p) if flagged else None,
        }
        entries.append(entry)

    entries.sort(key=lambda e: (e["bloat"], e["read_count"], e["file_line_count"]), reverse=True)
    flagged_entries = [e for e in entries if e["bloat"]]

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "params": {
            "days": days,
            "min_reads": min_reads,
            "min_lines": min_lines,
            "min_size": min_size,
        },
        "sessions_scanned": len(recent),
        "files_observed": len(entries),
        "bloat_candidates": len(flagged_entries),
        "flagged": flagged_entries,
        "all": entries,
    }


def _ts_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")


def run_cli(args) -> int:
    base = resolve_cc_lens_base_url()
    print(f"[file_map] cc-lens base: {base}", flush=True)
    result = scan_file_map(
        base_url=base,
        days=args.days,
        min_reads=args.min_reads,
        min_lines=args.min_lines,
        min_size=args.min_size,
    )
    out_path = args.output or f"C:/tmp/context-os-filemap-{_ts_stamp()}.json"
    try:
        Path(out_path).parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, default=str)
    except OSError as e:
        print(f"[file_map] write failed: {e}", file=sys.stderr)
        return 1
    summary = {
        "ok": True,
        "output": out_path,
        "sessions_scanned": result["sessions_scanned"],
        "files_observed": result["files_observed"],
        "bloat_candidates": result["bloat_candidates"],
        "top5": [
            {
                "path": e["path"],
                "read_count": e["read_count"],
                "file_line_count": e["file_line_count"],
                "file_size_bytes": e["file_size_bytes"],
                "suggestion": e.get("suggestion"),
            }
            for e in result["flagged"][:5]
        ],
    }
    print(json.dumps(summary, indent=2, default=str))
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="context-os filemap")
    p.add_argument("--days", type=int, default=30)
    p.add_argument("--min-reads", type=int, default=3)
    p.add_argument("--min-lines", type=int, default=800)
    p.add_argument("--min-size", type=int, default=100_000)
    p.add_argument("--output", default=None)
    return run_cli(p.parse_args(argv))


if __name__ == "__main__":
    raise SystemExit(main())
