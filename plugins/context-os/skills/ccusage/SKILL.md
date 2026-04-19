---
name: ccusage
description: >
  Analyze Claude Code usage via ryoppippi/ccusage (local JSONL). Wraps `npx ccusage`.
  Trigger on: "ccusage", "daily token usage", "CLI usage stats".
---

# ccusage

## Setup

Requires Node.js (`npx`). No dashboard — offline CLI.

## Commands

```bash
context-os ccusage daily
context-os ccusage monthly
# or pass through:
context-os ccusage blocks --json
```

The wrapper calls `npx ccusage@latest` with the same arguments.

## When to use

- Quick cost summaries without starting cc-lens
- Complements **cc-lens** (dashboard + forensics) for different views of the same `~/.claude` data
