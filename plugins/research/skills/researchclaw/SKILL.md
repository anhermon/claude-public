---
name: researchclaw
description: AutoResearchClaw sub-skill — run the 23-stage autonomous research pipeline using Claude Code as LLM backend
---

# ResearchClaw

Thin wrapper. Full instructions live at:
`/Users/angelhermon/.paperclip/instances/AutoResearchClaw/.claude/skills/researchclaw/SKILL.md`

Read it for pipeline stages, flags, output structure, and troubleshooting.

---

## Quick Start

### 1. Pre-warm session (required on first run)

`acpx` sessions hang on cold start — always warm before running the pipeline:

```bash
acpx --ttl 0 --cwd /Users/angelhermon/.paperclip/instances/AutoResearchClaw \
  claude sessions ensure --name researchclaw 2>/dev/null || \
acpx --ttl 0 --cwd /Users/angelhermon/.paperclip/instances/AutoResearchClaw \
  claude sessions new --name researchclaw

acpx --approve-all --max-turns 1 --ttl 0 \
  --cwd /Users/angelhermon/.paperclip/instances/AutoResearchClaw \
  claude -s researchclaw \
  "You are a research assistant. Respond with text only. Do NOT use any tools. Acknowledge with 'Ready'."
```

### 2. Run the pipeline

```bash
cd /Users/angelhermon/.paperclip/instances/AutoResearchClaw
source .venv/bin/activate
researchclaw run --topic "$TOPIC" --config config.arc.yaml
```

---

## Gate Management

Gates pause at stages 5 (literature screen), 9 (experiment design), 20 (quality gate).

```bash
researchclaw status artifacts/<run-id>
researchclaw approve artifacts/<run-id> --message "Looks good"
researchclaw reject artifacts/<run-id> --reason "Need more sources"
```
