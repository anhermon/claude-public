#!/usr/bin/env python3
"""Claude Code SessionStart hook — orientation reminder."""
from __future__ import annotations

import sys


def main() -> None:
    print(
        "[context-os] SENSE → ORIENT → ACT → DEPOSIT — "
        "`context-os graph health --graph knowledge_base`",
        file=sys.stderr,
    )


if __name__ == "__main__":
    main()
