#!/usr/bin/env python3
"""Claude Code Stop hook — optional session summary ingest."""
from __future__ import annotations

import os
import sys


def main() -> None:
    if os.environ.get("CONTEXT_OS_SESSION_INGEST") == "1":
        print(
            "[context-os] CONTEXT_OS_SESSION_INGEST=1 — run: "
            "context-os ingest session <SESSION_ID> --summary-only",
            file=sys.stderr,
        )


if __name__ == "__main__":
    main()
