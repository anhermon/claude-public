#!/usr/bin/env python3
"""
Extract a summary knowledge node from a Claude Code session JSONL file.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from datetime import date
from pathlib import Path
from typing import Any


def find_session_file(session_id: str) -> Path | None:
    home = Path.home()
    projects = home / ".claude" / "projects"
    if not projects.is_dir():
        return None
    for j in projects.rglob("*.jsonl"):
        if session_id in j.name:
            return j
    sid_short = session_id[:8]
    for j in projects.rglob("*.jsonl"):
        if sid_short in j.name:
            return j
    return None


def parse_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
            if isinstance(row, dict):
                rows.append(row)
        except json.JSONDecodeError:
            continue
    return rows


def extract_tool_paths(obj: Any, acc: list[str]) -> None:
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k in ("file_path", "path") and isinstance(v, str) and ("/" in v or v.endswith(".md")):
                acc.append(v)
            else:
                extract_tool_paths(v, acc)
    elif isinstance(obj, list):
        for x in obj:
            extract_tool_paths(x, acc)


def summarize_session(path: Path, session_id: str, summary_only: bool) -> tuple[str, list[str], Counter[str], str]:
    rows = parse_jsonl(path)
    paths: list[str] = []
    texts: list[str] = []
    tool_names: list[str] = []

    raw = path.read_text(encoding="utf-8", errors="replace")
    for name in ("Read", "Write", "Edit", "Grep", "Glob", "Bash", "Task", "WebFetch"):
        c = raw.count(f'"{name}"')
        if c:
            tool_names.extend([name] * min(c, 50))

    for row in rows:
        extract_tool_paths(row, paths)
        blob = json.dumps(row)
        if len(blob) > 200:
            # capture assistant-like text fields
            if "assistant" in blob.lower() and "content" in blob:
                try:
                    msg = row.get("message") or row
                    if isinstance(msg, dict):
                        content = msg.get("content")
                        if isinstance(content, str) and len(content) > 80:
                            texts.append(content[:1500])
                        elif isinstance(content, list):
                            for block in content:
                                if isinstance(block, dict) and block.get("text"):
                                    t = str(block.get("text", ""))
                                    if len(t) > 80:
                                        texts.append(t[:1500])
                except Exception:
                    pass

    cnt: Counter[str] = Counter(tool_names)
    title = f"Session insights {session_id[:12]}"
    body_lines = [
        "## Automated summary",
        f"- Source session file: `{path.name}`",
        f"- Tool name mentions (heuristic): {dict(cnt)}",
        f"- Paths touched (sample): {list(dict.fromkeys(paths))[:25]}",
        "",
        "## Assistant excerpts",
    ]
    for t in texts[:5]:
        body_lines.append(f"> {t[:400]}...\n")

    body = "\n".join(body_lines)
    if summary_only:
        body = "\n".join(body_lines[:6])
    return title, paths, cnt, body


def write_node(
    graph: Path,
    session_id: str,
    title: str,
    body: str,
    source_path: Path,
) -> Path:
    emergent = graph / "emergent"
    emergent.mkdir(parents=True, exist_ok=True)
    safe = re.sub(r"[^a-zA-Z0-9_-]+", "-", session_id)[:48].strip("-") or "session"
    out = emergent / f"session-{safe}.md"
    today = date.today().isoformat()
    text = f"""---
name: SESSION_{safe.upper().replace('-', '_')[:40]}
description: Insights extracted from Claude Code session
domain: emergent
node_type: concept
status: emergent
last_updated: {today}
tags:
  - emergent
  - session-ingest
topics:
  - session
related_concepts: []
source:
  type: session
  session_id: "{session_id}"
  file: "{source_path.as_posix()}"
---

# {title}

{body}

## Evidence

> [INFERRED: extracted from session JSONL]

## Related Concepts

- Link to canonical concepts after human review.
"""
    out.write_text(text, encoding="utf-8")
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("session_id", help="Session id or prefix")
    ap.add_argument("--graph", default="knowledge_base", help="Knowledge graph root")
    ap.add_argument("--summary-only", action="store_true")
    ap.add_argument("--file", help="Explicit path to jsonl (skip discovery)")
    args = ap.parse_args()

    path: Path | None = Path(args.file) if args.file else find_session_file(args.session_id)
    if not path or not path.is_file():
        print(json.dumps({"error": "session jsonl not found", "session_id": args.session_id}))
        return 1

    title, paths, _cnt, body = summarize_session(path, args.session_id, args.summary_only)
    out = write_node(Path(args.graph), args.session_id, title, body, path)
    print(json.dumps({"ok": True, "written": str(out), "paths_sample": paths[:10]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
