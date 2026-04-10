# claude-public

Angel Hermon's public collection of Claude Code plugins — install them directly from GitHub.

## Claude Code marketplace

This repository is a **marketplace**: it includes [\".claude-plugin/marketplace.json\"]. In Claude Code, add the marketplace URL:

`https://github.com/anhermon/claude-public`

Then install individual plugins from the catalog (for example `commit`, `code-review`, or `image-gen`). Each plugin’s source lives under [\"plugins/\"].

Plugin entries use **`git-subdir`** sources so each plugin can be fetched from this monorepo without separate repositories.

### If the catalog shows “No plugins available”

1. **Refresh or re-add** the marketplace after updates, or run **`/plugin marketplace update`** (Desktop) / `claude plugin marketplace update` (CLI).

2. **Claude Desktop / Cowork** may validate the catalog strictly (for example every entry needs an **`author`** field) or route third-party marketplaces through a remote sync path that [does not load external plugin sources yet](https://github.com/anthropics/claude-code/issues/41653). If the UI stays empty, install from the **terminal** (often more reliable for custom marketplaces):

   ```bash
   claude plugin marketplace add https://github.com/anhermon/claude-public
   claude plugin install commit@claude-public
   ```

   Use `code-review` or `image-gen` instead of `commit` for the other plugins.

## Install a plugin

```bash
claude install anhermon/claude-public
```

This installs all plugins in this repo. To install a specific plugin by file:

```bash
claude install anhermon/claude-public/commit.plugin
```

---

## Plugin catalog

### commit
**v1.0.0** — Write and execute a conventional commit automatically.

### code-review
**v1.0.0** — Structured code review with severity-ranked findings.

### image-gen
**v0.2.0** — AI image generation with expert prompt engineering.

### search
**v1.0.0** — Precise codebase exploration using ripgrep and tree-sitter.

Finds definitions, call sites, and usages with structural awareness. Faster and more precise than default search for large codebases.

**Trigger phrases:** \"search for\", \"find where X is defined\", \"trace call sites of X\", \"how is X used\", \"explore the codebase\"

No prerequisites. `ripgrep` and `tree-sitter-cli` recommended for full power.

---

### memory
**v1.0.0** — Long-term memory management using the Memory Palace (MemPalace) pattern.

Persists project facts, user preferences, and session snapshots to a structured `.memory/` directory.

**Trigger phrases:** \"remember this\", \"recall from memory\", \"save my preferences\", \"load my memory\", \"manage project context\"

No prerequisites. Storage defaults to `.memory/` in current project or `~/.memory/` globally.

---

### agent-repo-search
**v0.1.0** — Structural indexing and CXML chunking for massive codebases.

Efficiently search and ingest repositories that exceed context limits using structural indexing.

**Trigger phrases:** \"ingest repo\", \"search indexed repo\", \"use structural search\"

Requires `uv` and `python 3.10+`.

---

### research
**v1.0.0** — Research any topic via AutoResearchClaw or Regular Research.

Autonomous 23-stage pipeline (ResearchClaw) for academic-depth papers or fast Claude-native synthesis (Regular Research) for structured briefs.

**Trigger phrases:** \"research X\", \"/research\", \"investigate X\", \"look into X\", \"write a paper on X\", \"give me a brief on X\"

No prerequisites. Web search capability recommended.

---

### llm-wiki
**v1.1.0** — Persistent markdown wiki maintenance for Obsidian.

Maintain a living knowledge base by absorbing source documents, answering questions with citations, auditing for drift, and capturing session insights. Includes `kb-to-wiki` skill for publishing the KB as a browsable HTML wiki.

**Trigger phrases:** \"ingest this\", \"add to wiki\", \"log this to KB\", \"lint the wiki\", \"check the KB\", \"find stale pages\", \"query the wiki\"

No prerequisites. Vault defaults to `~/knowledge-base/`.

---

### setup-telemetry
**v1.0.0** — Instrument Claude with Langfuse telemetry and local dashboard.

Visualizes session metrics, tool usage, and performance insights.

**Trigger phrases:** \"set up telemetry\", \"instrument my project\", \"visualize session metrics\", \"show me telemetry dashboard\"

No prerequisites. Requires Langfuse account (optional for local-only).

---

## Development Philosophy

**Purpose:** This repo is the Claude Code fork — improved dev tooling and a learning knowledge base. Plugins here are not context-specific and aim to be useful to any Claude Code user.

### Evolution Workflow

This repo evolves through usage, not roadmaps:

1. **Use** — Run these plugins in real dev workflows. Observe what works and what breaks.
2. **Journal** — Record friction, failures, and surprises as structured feedback.
3. **Derive** — Convert feedback into concrete issues with measurable acceptance criteria.
4. **Branch** — Implement on feature branches. One concern per branch.
5. **Benchmark** — CI runs the benchmark suite on every PR. Scores are emitted as `benchmark-results.json` in a standard format.
6. **Merge** — Only merge when benchmarks confirm the change improves (or at minimum does not regress) the overall score.

---

## Contributing

See [CONTRIBUTING.md](./CONTRIBUTING.md) for how to author and submit plugins.

## Code of Conduct

See [CODE_OF_CONDUCT.md](./CODE_OF_CONDUCT.md).
