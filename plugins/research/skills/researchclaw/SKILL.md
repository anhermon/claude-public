---
name: researchclaw
description: AutoResearchClaw sub-skill — run the 23-stage autonomous research pipeline using Claude Code as LLM backend
---

# ResearchClaw

Thin Claude Code wrapper around [AutoResearchClaw](https://github.com/aiming-lab/AutoResearchClaw) — a 23-stage autonomous research pipeline ("Chat an Idea. Get a Paper."). Not vendored here; this skill drives a local checkout.

## Setup (first time on a machine)

```bash
export RESEARCHCLAW_DIR="${RESEARCHCLAW_DIR:-$HOME/workspace/AutoResearchClaw}"
[ -d "$RESEARCHCLAW_DIR" ] || git clone https://github.com/aiming-lab/AutoResearchClaw "$RESEARCHCLAW_DIR"
cd "$RESEARCHCLAW_DIR" && python3 -m venv .venv && source .venv/bin/activate && pip install -e .
```

Read `$RESEARCHCLAW_DIR/.claude/skills/researchclaw/SKILL.md` (if present in the upstream repo) for the authoritative pipeline stages, flags, and output structure — it supersedes this file if they disagree.

---

## Quick Start

### 1. Pre-warm session (required on first run)

If you're driving the pipeline through `acpx` (Paperclip's session-multiplexing proxy) rather than directly, sessions hang on cold start — always warm before running the pipeline:

```bash
acpx --ttl 0 --cwd "$RESEARCHCLAW_DIR" claude sessions ensure --name researchclaw 2>/dev/null || \
acpx --ttl 0 --cwd "$RESEARCHCLAW_DIR" claude sessions new --name researchclaw

acpx --approve-all --max-turns 1 --ttl 0 --cwd "$RESEARCHCLAW_DIR" claude -s researchclaw \
  "You are a research assistant. Respond with text only. Do NOT use any tools. Acknowledge with 'Ready'."
```

`acpx` is optional — skip this step entirely if you're not running under Paperclip.

### 2. Run the pipeline

```bash
cd "$RESEARCHCLAW_DIR"
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
