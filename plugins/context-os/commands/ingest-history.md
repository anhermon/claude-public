---
name: ingest-history
description: Extract insights from past Claude sessions into the knowledge graph
model: inherit
---

# Historical ingest

Load the **context-ingest** skill, operation **HISTORICAL**.

1. List candidate sessions: `context-os sessions list --since 30d --format json`
2. For each session ID to capture: `context-os ingest session SESSION_ID --graph knowledge_base`
3. Dedupe against existing nodes in `knowledge_base/emergent/` (same session_id in frontmatter)
4. Report paths created and concepts extracted
