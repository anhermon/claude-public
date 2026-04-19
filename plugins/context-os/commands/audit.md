---
name: audit
description: Full context audit — graph health + token/session analytics
model: inherit
---

# Context audit

Load the **context-audit** skill and run:

1. `context-os audit` — combined HTML at `/tmp/context-os-audit-bundle-<timestamp>.html`, with symlinks `/tmp/context-os-audit-bundle-latest.html` and `/tmp/context-os-audit-bundle.html`
2. Open the latest bundle file; summarize orphans, stale nodes, hubs, and any cc-lens / ccusage sections
3. Cross-reference **token-efficiency** waste taxonomy for prioritized fixes

If `npx cc-lens` is not running, tell the user to start it for session forensics.
