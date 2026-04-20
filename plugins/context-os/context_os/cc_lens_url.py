"""
Resolve the cc-lens HTTP API base URL and auth headers.

Upstream `npx cc-lens` picks a free port (often 3001) and only one dev server may run.
Starting a second instance can bind to e.g. 3002 but Next.js may error and leave a blank page.
"""

from __future__ import annotations

import os
import urllib.error
import urllib.request
from pathlib import Path


_TOKEN_FILE = Path.home() / ".cc-lens" / "token"


def resolve_cc_lens_auth() -> dict[str, str]:
    """
    Return HTTP headers to use when calling the cc-lens API.

    Order:
      1. CC_LENS_TOKEN env var     -> Authorization: Bearer <token>
      2. CC_LENS_API_KEY env var   -> X-Api-Key: <key>
      3. ~/.cc-lens/token file     -> Authorization: Bearer <file contents>
      4. (no auth)                 -> {}
    """
    tok = os.environ.get("CC_LENS_TOKEN")
    if tok:
        return {"Authorization": f"Bearer {tok.strip()}"}
    key = os.environ.get("CC_LENS_API_KEY")
    if key:
        return {"X-Api-Key": key.strip()}
    try:
        if _TOKEN_FILE.is_file():
            t = _TOKEN_FILE.read_text(encoding="utf-8").strip()
            if t:
                return {"Authorization": f"Bearer {t}"}
    except OSError:
        pass
    return {}


def cc_lens_auth_hint() -> str:
    """Actionable one-liner telling the user how to provide auth."""
    return (
        "cc-lens returned 401 Unauthorized. Provide credentials with one of:\n"
        "  - export CC_LENS_TOKEN=<token>         (sent as: Authorization: Bearer ...)\n"
        "  - export CC_LENS_API_KEY=<key>         (sent as: X-Api-Key: ...)\n"
        f"  - write the token to {_TOKEN_FILE}\n"
        "If your local cc-lens does not require auth, ensure it is running without "
        "auth middleware (e.g. `npx cc-lens` default mode)."
    )


def _probe(base: str, timeout: float = 0.9) -> int | None:
    """Return HTTP status for GET {base}/api/stats with auth headers, or None on network error."""
    req = urllib.request.Request(f"{base}/api/stats", headers=resolve_cc_lens_auth())
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status
    except urllib.error.HTTPError as e:
        return e.code
    except Exception:
        return None


def find_running_cc_lens() -> str | None:
    """
    Return http://localhost:<port> for the first port in range that serves /api/stats.

    A 401 response still indicates cc-lens is running (just needs auth), so we return
    that base URL — the caller can surface a clear auth error later.
    """
    for port in range(3001, 3011):
        base = f"http://127.0.0.1:{port}"
        status = _probe(base)
        if status == 200 or status == 401:
            return f"http://localhost:{port}"
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
