#!/usr/bin/env python3
"""Preflight diagnostic: verify context-os dependencies + external services.

Checks:
  - Python version
  - Node.js / npx available
  - ccusage reachable (`npx ccusage@latest --version`)
  - cc-lens dashboard reachable on common ports (3001-3010)
  - Plugin root resolvable
  - `context-os` on PATH
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


def _check(name: str, fn) -> dict[str, Any]:
    try:
        ok, detail, fix = fn()
    except Exception as e:  # noqa: BLE001
        return {"name": name, "ok": False, "detail": f"error: {e}", "fix": ""}
    return {"name": name, "ok": ok, "detail": detail, "fix": fix}


def _python_ok() -> tuple[bool, str, str]:
    v = sys.version_info
    ok = (v.major, v.minor) >= (3, 10)
    return ok, f"Python {v.major}.{v.minor}.{v.micro}", "Install Python 3.10+" if not ok else ""


def _node_ok() -> tuple[bool, str, str]:
    npx = shutil.which("npx")
    if not npx:
        return False, "npx not on PATH", "Install Node.js (https://nodejs.org), then re-run doctor"
    try:
        r = subprocess.run([npx, "--version"], capture_output=True, text=True, timeout=10)
        return r.returncode == 0, f"npx {r.stdout.strip()}", ""
    except Exception as e:  # noqa: BLE001
        return False, f"npx call failed: {e}", "Reinstall Node.js"


def _ccusage_ok() -> tuple[bool, str, str]:
    npx = shutil.which("npx")
    if not npx:
        return False, "requires npx", "Install Node.js first"
    try:
        r = subprocess.run(
            [npx, "--yes", "ccusage@latest", "--version"],
            capture_output=True, text=True, timeout=60,
        )
        if r.returncode == 0:
            return True, f"ccusage {r.stdout.strip() or 'ok'}", ""
        return False, f"ccusage exit={r.returncode}: {r.stderr[:200]}", "Run: npx --yes ccusage@latest daily"
    except subprocess.TimeoutExpired:
        return False, "ccusage timed out (first install may take a while)", "Retry: npx --yes ccusage@latest daily"


def _cc_lens_ok() -> tuple[bool, str, str]:
    override = os.environ.get("CC_LENS_BASE_URL") or os.environ.get("CONTEXT_OS_CC_LENS_URL")
    ports = [override] if override else [f"http://localhost:{p}" for p in range(3001, 3011)]
    for base in ports:
        if not base:
            continue
        try:
            with urllib.request.urlopen(f"{base.rstrip('/')}/api/stats", timeout=2) as resp:
                if resp.status == 200:
                    return True, f"cc-lens reachable at {base}", ""
        except (urllib.error.URLError, TimeoutError, ConnectionError, OSError):
            continue
    return (
        False,
        "cc-lens dashboard not reachable on 3001-3010",
        "Start it: npx cc-lens   (leave running; context-os cc-lens analyze targets this)",
    )


def _cli_on_path() -> tuple[bool, str, str]:
    which = shutil.which("context-os")
    if which:
        return True, which, ""
    return (
        False,
        "context-os not on PATH (fallback: python3 -m context_os)",
        "uv tool install .   OR   pip install -e .   OR   npm link",
    )


def _plugin_root_ok() -> tuple[bool, str, str]:
    env = os.environ.get("CONTEXT_OS_PLUGIN_ROOT")
    here = Path(__file__).resolve().parent.parent
    if env:
        p = Path(env)
        return p.is_dir(), f"env-set {p}", "Unset or fix CONTEXT_OS_PLUGIN_ROOT"
    return here.is_dir(), f"{here}", ""


CHECKS = [
    ("python", _python_ok),
    ("node/npx", _node_ok),
    ("ccusage", _ccusage_ok),
    ("cc-lens dashboard", _cc_lens_ok),
    ("context-os CLI on PATH", _cli_on_path),
    ("plugin root", _plugin_root_ok),
]


def run_checks() -> list[dict[str, Any]]:
    return [_check(name, fn) for name, fn in CHECKS]


def cmd_doctor(args) -> int:
    results = run_checks()
    if getattr(args, "format", "text") == "json":
        print(json.dumps({"checks": results, "ok": all(r["ok"] for r in results)}, indent=2))
        return 0 if all(r["ok"] for r in results) else 2
    print("context-os doctor")
    print("=" * 60)
    for r in results:
        mark = "OK  " if r["ok"] else "FAIL"
        print(f"[{mark}] {r['name']:<28s} {r['detail']}")
        if not r["ok"] and r["fix"]:
            print(f"       fix: {r['fix']}")
    ok = all(r["ok"] for r in results)
    print("=" * 60)
    print(f"Overall: {'READY' if ok else 'ISSUES FOUND — see fix lines above'}")
    return 0 if ok else 2
