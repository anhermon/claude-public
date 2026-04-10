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

### agent-repo-search
**v0.1.0** — Efficiently search and ingest large codebases using structural indexing and token-aware CXML chunking.

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

### Branch Model

This repo uses long-lived branches with benchmark-driven pruning:

1. **Develop parallel branches** — Multiple approaches to the same problem can coexist.
2. **Evaluate and compare** — The same benchmark suite runs on each branch for side-by-side comparison.
3. **Pick winner / drop loser** — Higher benchmark score wins. The losing branch is cancelled.
4. **Release candidate** — The winner is promoted to an RC for final validation.
5. **Merge to main** — Only after RC passes all gates.

### Benchmark-Driven Merge Decisions

- PRs that regress the overall score below threshold are blocked.
- When competing branches solve the same problem, CI compares their scores and recommends the winner.
- Post-merge regressions trigger revert recommendations.
- Benchmark history is tracked via CI artifacts for trend analysis.

---

## Contributing

See [CONTRIBUTING.md](./CONTRIBUTING.md) for how to author and submit plugins.

## Code of Conduct

See [CODE_OF_CONDUCT.md](./CODE_OF_CONDUCT.md).
