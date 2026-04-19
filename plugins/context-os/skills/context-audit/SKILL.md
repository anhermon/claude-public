---
name: context-audit
description: >
  Run a unified audit: local knowledge graph health (orphans, hubs, stale nodes) plus
  session/token analytics via context-os audit, cc-lens, and ccusage. Trigger on:
  "audit context", "graph health", "session waste", "full context audit".
---

# Context audit

## Steps

1. Ensure the bundled CLI is on PATH: `context-os --help`
2. Run:
   ```bash
   context-os audit --graph knowledge_base
   ```
3. Open `/tmp/context-os-audit-bundle-latest.html` (or the timestamped `/tmp/context-os-audit-bundle-*.html`) in a browser
4. If the cc-lens section is empty, run `npx cc-lens` and re-run, or use `context-os cc-lens analyze`
5. Load **token-efficiency** for waste taxonomy and prioritize fixes (graph linking vs token burn)

## Output expectations

- Orphan and stale counts from graph health
- ccusage daily snapshot (if `npx` / `ccusage` available)
- cc-lens HTML path when dashboard API is reachable
