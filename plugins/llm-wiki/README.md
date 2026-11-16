# llm-wiki plugin

Persistent markdown wiki maintenance for Obsidian vaults.

## Skills

**llm-wiki** — Maintain a living knowledge base by absorbing source documents, answering questions with citations, auditing for drift, and capturing session insights.

Trigger phrases: "ingest this", "add to wiki", "log this to KB", "lint the wiki", "check the KB", "find stale pages", "query the wiki".

## How it works

1. **Ingest** — Absorbs source material (files, URLs, pastes) into a `raw/` directory and updates relevant wiki pages with new facts and cross-references.
2. **Query** — Searches the knowledge base and synthesizes answers with direct citations to wiki pages.
3. **Lint** — Audits the wiki for contradictions, stale claims, orphaned pages, and missing cross-references.
4. **Learnings** — Proactively surfaces context at session start and captures non-obvious patterns or decisions at session end.

## Vault Structure

Uses a structured Obsidian vault at `~/knowledge-base/`:
- `projects/` — Project-specific knowledge
- `topics/` — Domain and conceptual knowledge
- `tools/` — Tool and technique pages
- `raw/` — Immutable source documents
- `index.md` — Navigation index
- `log.md` — Append-only operation log

## Source

`claude-public` — public Claude Code plugins.

## Install and example

```bash
claude plugin marketplace add anhermon/claude-public
claude plugin install llm-wiki@claude-public
```

Example: create `~/knowledge-base/` with an `index.md`, then say "add this to the wiki" with a pasted note or file path. The skill files it under `raw/`, updates the relevant pages and appends to `log.md`.

Requirements: a markdown vault (Obsidian optional). `kb-to-wiki` needs Python 3.
