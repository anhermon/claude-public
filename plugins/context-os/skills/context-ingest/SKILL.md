---
name: context-ingest
description: >
  Three ingestion modes: AUTO (hooks document behavior), SOURCE (files/URLs/Confluence stubs),
  HISTORICAL (session JSONL to knowledge_base). Trigger on "ingest confluence",
  "auto capture knowledge", "import session to graph".
---

# Context ingest

## AUTO — while the agent works

Document-only (no background daemon in this plugin):

1. User installs Claude Code hooks from `hooks/settings-snippet.json` (merge into project settings)
2. `PostToolUse` on `Write`/`Edit` under `knowledge_base/` logs a reminder to add `[[wiki-links]]`
3. `Stop` can run `context-os ingest session --summary-only` when `CONTEXT_OS_SESSION_INGEST=1`

## SOURCE — external or local files

```bash
context-os ingest file path/to/doc.md --graph knowledge_base
context-os ingest source https://example.com/page --graph knowledge_base
```

Confluence / Notion: `ingest_source.py` returns stubs until API env vars are configured.

## HISTORICAL — past sessions

```bash
context-os sessions list --since 30d --path-contains myproject
context-os ingest session SESSION_ID --graph knowledge_base
```

Always write emergent nodes under `knowledge_base/emergent/` with `source.session_id` when applicable.
