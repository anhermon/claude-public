#!/usr/bin/env python3
"""
Ingest from local path, http(s) URL, or stub adapters (Confluence / Notion).
Writes emergent knowledge nodes under knowledge_base/emergent/.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.request
from pathlib import Path


def _slug(s: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9_-]+", "-", s.strip())[:80]
    return s.strip("-").lower() or "concept"


def _strip_html(html: str) -> str:
    t = re.sub(r"(?is)<script.*?>.*?</script>", " ", html)
    t = re.sub(r"(?is)<style.*?>.*?</style>", " ", t)
    t = re.sub(r"<[^>]+>", " ", t)
    t = re.sub(r"\s+", " ", t)
    return t.strip()


def fetch_url(url: str) -> tuple[str, str]:
    req = urllib.request.Request(url, headers={"User-Agent": "context-os-ingest/2.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        raw = r.read().decode("utf-8", errors="replace")
    title_m = re.search(r"<title>([^<]+)</title>", raw, re.I)
    title = title_m.group(1).strip() if title_m else url
    return title, _strip_html(raw)


def ingest_text(title: str, body: str, source_label: str, out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    slug = _slug(title)
    path = out_dir / f"{slug}.md"
    if path.exists():
        path = out_dir / f"{slug}-extra.md"
    today = __import__("datetime").date.today().isoformat()
    node = f"""---
name: {slug.upper().replace('-', '_')}
description: {title[:200]}
domain: emergent
node_type: concept
status: emergent
last_updated: {today}
tags:
  - emergent
  - ingested
topics:
  - imported
related_concepts: []
source:
  type: document
  ref: "{source_label}"
---

# {title}

{body[:8000]}

## Evidence

> [INFERRED: imported from {source_label}]

## Related Concepts

- Add [[wiki-links]] after review.
"""
    path.write_text(node, encoding="utf-8")
    return path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("source", help="File path or https:// URL")
    ap.add_argument("--graph", default="knowledge_base", help="Knowledge root")
    args = ap.parse_args()
    src = args.source.strip()
    out = Path(args.graph) / "emergent"

    if src.lower().startswith("confluence:"):
        print(
            json.dumps(
                {
                    "error": "Confluence adapter not configured",
                    "hint": "Set CONFLUENCE_BASE_URL, CONFLUENCE_USER, CONFLUENCE_TOKEN and implement REST fetch in ingest_source.py",
                },
                indent=2,
            )
        )
        return 1
    if src.lower().startswith("notion:"):
        print(
            json.dumps(
                {
                    "error": "Notion adapter not configured",
                    "hint": "Use Notion API token + page ID (future)",
                },
                indent=2,
            )
        )
        return 1

    if src.startswith("http://") or src.startswith("https://"):
        title, body = fetch_url(src)
        p = ingest_text(title, body, src, out)
        print(json.dumps({"ok": True, "path": str(p)}, indent=2))
        return 0

    path = Path(src)
    if not path.is_file():
        print(json.dumps({"error": f"not a file: {src}"}))
        return 1
    text = path.read_text(encoding="utf-8", errors="replace")
    title = path.stem.replace("_", " ").title()
    p = ingest_text(title, text, str(path.resolve()), out)
    print(json.dumps({"ok": True, "path": str(p)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
