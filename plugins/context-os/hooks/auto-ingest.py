#!/usr/bin/env python3
"""
Claude Code PostToolUse hook (Write|Edit). Reminds to reinforce the graph when
paths look like knowledge_base writes.
"""
from __future__ import annotations

import json
import sys


def main() -> None:
    try:
        raw = sys.stdin.read()
        d = json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError:
        return
    blob = json.dumps(d)
    if "knowledge_base" in blob:
        print(
            "[context-os] Knowledge graph file touched — link via [[wiki-links]]; "
            "run: context-os graph health --graph knowledge_base",
            file=sys.stderr,
        )


if __name__ == "__main__":
    main()
