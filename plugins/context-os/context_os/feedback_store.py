#!/usr/bin/env python3
"""
Feedback store for context-os recommendations.

Persists user actions on recommendations to a JSONL file at
~/.claude/plugins/context-os/feedback.jsonl. One JSON object per line:

    {
      "id":         <rec_id>,
      "session_id": <session id string>,
      "category":   <waste category>,
      "signature":  <deterministic pattern signature>,
      "status":     "accepted" | "rejected" | "known",
      "timestamp":  ISO-8601 UTC,
      "note":       optional free text
    }

Stdlib only, Windows-friendly.
"""

from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


VALID_STATUSES = {"accepted", "rejected", "known"}


def feedback_path() -> Path:
    env = os.environ.get("CONTEXT_OS_FEEDBACK_PATH")
    if env:
        return Path(env)
    return Path.home() / ".claude" / "plugins" / "context-os" / "feedback.jsonl"


def make_signature(category: str, tool_names: Iterable[str]) -> str:
    """Deterministic signature: hash(category + sorted top tool names)."""
    tools = sorted({t for t in (tool_names or []) if t})
    payload = category + "|" + ",".join(tools)
    return hashlib.sha1(payload.encode("utf-8")).hexdigest()[:16]


def make_rec_id(session_id: str, category: str, variant: str) -> str:
    """Stable id for a specific (session, category, variant) recommendation."""
    payload = f"{session_id}|{category}|{variant}"
    return hashlib.sha1(payload.encode("utf-8")).hexdigest()[:16]


def load() -> list[dict]:
    """Load all feedback entries (oldest first). Missing file returns []."""
    p = feedback_path()
    if not p.exists():
        return []
    out: list[dict] = []
    try:
        with p.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    out.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    except OSError:
        return []
    return out


def record(
    rec_id: str,
    status: str,
    session_id: str = "",
    category: str = "",
    signature: str = "",
    note: str | None = None,
) -> dict:
    """Append a feedback entry. Returns the written record."""
    if status not in VALID_STATUSES:
        raise ValueError(f"status must be one of {VALID_STATUSES}, got {status!r}")
    entry = {
        "id": rec_id,
        "session_id": session_id,
        "category": category,
        "signature": signature,
        "status": status,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    if note:
        entry["note"] = note
    p = feedback_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return entry


def status_for(rec_id: str) -> str | None:
    """Latest status recorded for a rec_id, or None."""
    latest: dict | None = None
    for e in load():
        if e.get("id") == rec_id:
            latest = e
    return latest.get("status") if latest else None


def history_by_signature(signature: str) -> list[dict]:
    """All feedback entries sharing a pattern signature (for cross-session learning)."""
    return [e for e in load() if e.get("signature") == signature]
