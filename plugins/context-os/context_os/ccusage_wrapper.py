#!/usr/bin/env python3
"""Shell out to `npx ccusage` with the same argv (minus script name)."""

from __future__ import annotations

import shutil
import subprocess
import sys


def main() -> int:
    npx = shutil.which("npx")
    if not npx:
        print("npx not found; install Node.js", file=sys.stderr)
        return 1
    args = sys.argv[1:]
    if not args:
        args = ["daily"]
    cmd = [npx, "--yes", "ccusage@latest", *args]
    try:
        r = subprocess.run(cmd, timeout=120)
    except subprocess.TimeoutExpired:
        print("ccusage timed out", file=sys.stderr)
        return 1
    return r.returncode


if __name__ == "__main__":
    raise SystemExit(main())
