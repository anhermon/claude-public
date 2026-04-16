# System Prompt Audit Plugin

Audits and refines agent system prompts against context engineering best practices. Catches token waste, redundant API calls, and verbosity issues before they hit production.

## What It Does

Runs a nine-point structured audit against any instruction file (`AGENTS.md`, `HEARTBEAT.md`, or similar):

### Part A — Context Efficiency (Heartbeat / Agent-Loop Prompts)

1. **Wake Payload Usage** — is the agent using inline wake data before making API calls?
2. **Incremental Comment Fetching** — is the agent using `?after=` deltas instead of full thread replays?
3. **Skill Loading Discipline** — is the agent loading full skill docs for tasks that only need direct API calls?
4. **Tool Priority** — is the agent using `Read`/`Grep`/`Glob` instead of Bash for file operations?
5. **Response Verbosity** — are issue comments capped to bullets + key facts?

### Part B — General Prompt Quality

6. **Role and Scope Clarity** — is the agent's role, authority, and out-of-scope behavior explicitly defined?
7. **Instruction Specificity** — are instructions concrete and actionable, or abstract and aspirational?
8. **Safety and Guardrails** — does the prompt explicitly define what the agent must NOT do?
9. **Output Format Consistency** — does the prompt specify expected output structure for recurring outputs?

## Triggers

- `audit system prompt`
- `audit agent instructions`
- `audit my AGENTS.md`
- `refine system prompt`
- `context engineering audit`
- `optimize system prompt`
- `/system-prompt-audit`

## Output

A markdown table with PASS/FAIL/PARTIAL per dimension, evidence quotes, and numbered fix recommendations. Optionally applies fixes inline via `Edit`.

## Installation

```bash
claude install anhermon/claude-public/system-prompt-audit.plugin
```

## Origin

Part of Angel Hermon's public Claude/Paperclip plugins collection. Based on context engineering best practices and informed by prompt testing methodology (ref: Prompt-Engineering-Toolkit).
