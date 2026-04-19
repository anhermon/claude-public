"""
Resolve the cc-lens HTTP API base URL.

Upstream `npx cc-lens` picks a free port (often 3001) and only one dev server may run.
Starting a second instance can bind to e.g. 3002 but Next.js may error and leave a blank page.
"""

from __future__ import annotations

import os
import urllib.error
import urllib.request


def find_running_cc_lens() -> str | None:
    """Return http://localhost:<port> for the first port in range that serves /api/stats."""
    for port in range(3001, 3011):
        base = f"http://127.0.0.1:{port}"
        try:
            with urllib.request.urlopen(f"{base}/api/stats", timeout=0.9) as r:
                if r.status == 200:
                    return f"http://localhost:{port}"
        except Exception:
            continue
    return None


def resolve_cc_lens_base_url() -> str:
    """
    Order: CC_LENS_BASE_URL, CONTEXT_OS_CC_LENS_URL, auto-discover running server,
    else default http://localhost:3001.
    """
    env = os.environ.get("CC_LENS_BASE_URL") or os.environ.get("CONTEXT_OS_CC_LENS_URL")
    if env:
        return env.rstrip("/")
    found = find_running_cc_lens()
    if found:
        return found
    return "http://localhost:3001"
