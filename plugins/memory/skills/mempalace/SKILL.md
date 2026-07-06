---
name: mempalace
description: >
  MemPalace CLI — mine projects and conversations into a local ChromaDB-backed memory palace,
  then search them semantically. Use this skill whenever the user asks to: remember something
  across sessions, mine a project or conversation, search past decisions, set up MemPalace,
  use mempalace init/mine/search/status/wake-up/split commands, or store verbatim AI conversation
  history. Also use it when the user references "the palace", "my memories", "what did we decide
  about X", or "mine this chat". Do NOT use MCP tools — this skill works entirely via the CLI.
---

# MemPalace CLI Skill

MemPalace stores everything verbatim in a local ChromaDB palace and finds it later with
semantic search. No cloud, no API key required for core use.

## Quick setup check

```bash
mempalace --version
```

If not installed:
```bash
pip install mempalace
```

## Palace structure

```
Wing        — a person or project ("wing_myapp", "wing_kai")
  Hall      — memory type: hall_facts | hall_events | hall_discoveries | hall_preferences | hall_advice
    Room    — named topic slug ("auth-migration", "ci-pipeline")
      Closet— summary pointing to content
        Drawer — verbatim stored content (what ChromaDB holds)
```

Wings and rooms are just metadata on ChromaDB records. Tunnels (cross-wing rooms) are found
automatically by traversal.

## Core workflow

### 1. Initialize a palace for a directory

```bash
mempalace init ~/projects/myapp
```

This generates `mempalace.yaml` in the directory (wing name, rooms, keywords) and
`~/.mempalace/identity.txt` (Layer 0 — loaded every session).

### 2. Mine content

```bash
# Project files (code, docs, notes)
mempalace mine ~/projects/myapp

# Conversations (Claude exports, ChatGPT JSON, Slack exports)
mempalace mine ~/chats/ --mode convos

# With explicit wing name
mempalace mine ~/chats/ --mode convos --wing myapp

# Preview without writing
mempalace mine ~/projects/myapp --dry-run
```

**First run:** On the first `mine`, MemPalace downloads the `all-MiniLM-L6-v2` ONNX embedding model
(~79MB). Expect **90–120 seconds** for the first mine. Subsequent mines are fast.

**Non-interactive environments:** `mempalace init` prompts for room names interactively. In scripts,
pipe a newline to accept defaults: `echo '' | mempalace init <dir>`

**How mining works:** Files are chunked into exactly **800-char drawers** with **100-char overlap**
(`CHUNK_SIZE=800`, `CHUNK_OVERLAP=100` in `miner.py`). Each drawer gets wing/room/hall metadata.
No summarization — exact text is stored. Room routing is by path > filename > keyword scoring >
fallback "general". Minimum chunk size is 50 chars — smaller chunks are skipped.

**Incremental re-mining:** `file_already_mined()` checks the stored `source_mtime` metadata field
against the file's current mtime. If they match, the file is skipped. If the file was modified
since last mine, it's re-processed. Files with no stored mtime are always re-mined.

### 3. Split mega-files (before mining conversations)

Some exports concatenate multiple sessions. Split them first:

```bash
mempalace split ~/chats/                    # split into per-session files
mempalace split ~/chats/ --dry-run          # preview
mempalace split ~/chats/ --min-sessions 3   # only files with 3+ sessions
```

### 4. Search

```bash
# Basic semantic search
mempalace search "why did we switch to GraphQL"

# Filter to a wing
mempalace search "auth decisions" --wing myapp

# Filter to a specific room
mempalace search "database choice" --wing myapp --room backend

# Control result count (default 5)
mempalace search "deploy approach" --results 10
```

> **Flag placement:** `--palace` is a global arg — it must come **before** the subcommand:
> `mempalace --palace /path/palace search "query"` ✓
> `mempalace search "query" --palace /path/palace` ✗ (ignored or error in v3.x)

Search returns verbatim drawer content with similarity scores. This is raw ChromaDB
vector similarity — no LLM involved, zero API calls.

**What search actually delivers:** The 96.6% LongMemEval R@5 result is from this raw mode.
Wing + room filtering improves recall by up to +34% over unfiltered (this is standard
metadata filtering, not a novel mechanism). Use wing filters when you know the domain.

### 5. Status

```bash
mempalace status
```

Shows total drawers, wings, rooms, and palace path.

### 6. Wake-up (load critical facts into context)

```bash
mempalace --palace ~/.mempalace/palace wake-up          # loads L0 (identity) + L1 (critical facts)
mempalace --palace ~/.mempalace/palace wake-up --wing myapp  # project-specific
```

> **Note:** `--palace` must precede the subcommand. `identity.txt` is always read from
> `~/.mempalace/identity.txt` — there is no path override for this file.

The output is ~168 tokens for a minimal palace (verified). The `--help` text says "600–900 tokens"
but that reflects a fully-populated palace; a fresh palace with a short identity file produces
output well within the claimed ~170 token range.

**Important:** AAAK compression (entity codes + emotion markers) is used in L1 output.
AAAK is lossy — it abbreviates, it does not losslessly compress. At small scales it can
be *larger* than plain text. Its value is at scale with many repeated entities.

### 7. AAAK compression (optional)

```bash
mempalace compress --wing myapp
```

Compresses closet summaries using AAAK dialect. Use only when you have many repeated
entities across thousands of sessions. For normal use, raw mode is better for retrieval
accuracy (84.2% AAAK vs 96.6% raw on standard benchmarks).

### 8. Knowledge graph (CLI via Python API)

The KG is accessible through the MCP tools or directly via Python. There is no dedicated
CLI subcommand for KG operations — use the Python API:

```python
from mempalace.knowledge_graph import KnowledgeGraph
kg = KnowledgeGraph()
kg.add_triple("Kai", "works_on", "Orion", valid_from="2025-06-01")
kg.query_entity("Kai")
kg.timeline("Orion")
kg.invalidate("Kai", "works_on", "Orion", ended="2026-03-01")
```

**Note:** Contradiction detection (`fact_checker.py`) exists as a standalone utility but
is not automatically called by KG operations. It must be invoked manually.

## Configuration files

| File | Purpose |
|---|---|
| `<project>/mempalace.yaml` | Wing name, rooms, keywords for this project |
| `~/.mempalace/config.json` | Palace path, collection name overrides |
| `~/.mempalace/wing_config.json` | Global wing-to-keyword mapping |
| `~/.mempalace/identity.txt` | Layer 0 — plain text, loaded every wake-up |

## Custom palace path

All commands accept `--palace <path>` to override the default `~/.mempalace/palace/`:

```bash
mempalace status --palace /custom/path/palace
mempalace search "query" --palace /custom/path/palace
```

## Common workflows

### "Remember everything from this project"
```bash
mempalace init ~/projects/myapp
mempalace mine ~/projects/myapp
mempalace status  # verify drawer count
```

### "What did we decide about X six months ago?"
```bash
mempalace search "decision about X" --wing myapp
```

### "Mine my Claude conversation exports"
```bash
# First split if they're concatenated
mempalace split ~/Downloads/claude-exports/ --dry-run
mempalace split ~/Downloads/claude-exports/

# Then mine
mempalace mine ~/Downloads/claude-exports/ --mode convos --wing myproject
```

### "Prime Claude's context with my world"
```bash
mempalace wake-up
# Paste the output into your system prompt or inject via identity.txt
```

## What NOT to rely on

- **AAAK as lossless compression** — it's lossy. Don't use it expecting to recover exact text.
- **Automatic contradiction detection** — not wired in yet. `fact_checker.py` is manual only.
- **AAAK mode for better recall** — raw mode is more accurate. Use AAAK only for token budget constraints at scale.
- **Haiku rerank (100% benchmark)** — the rerank pipeline is not in the public CLI yet.

## Bugs to be aware of

- **Shell injection in hooks** (Issue #110) — `.codex-plugin/hooks/mempal-hook.sh` passes `$HOOK_NAME`
  from shell argv into a `python3 -m mempalace hook run --hook "$HOOK_NAME"` call without sanitization.
  Low risk in typical use (controlled environment) but a real vulnerability if hook names are
  externally influenced.
- **ChromaDB version unpinned** (Issue #100) — breaking changes across ChromaDB versions are common.
  macOS ARM64 segfaults reported (Issue #74). If you hit this: `pip install "chromadb>=0.4,<0.5"`
- **CI coverage is only 30%** (`--cov-fail-under=30`) — CI green does not mean the code is well-tested.
