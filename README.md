# claude-public

Angel Hermon's public collection of Claude Code plugins — install them directly from GitHub.

## Install a plugin

```bash
claude install anhermon/claude-public
```

This installs all plugins in this repo. To install a specific plugin by file:

```bash
claude install anhermon/claude-public/commit.plugin
claude install anhermon/claude-public/code-review.plugin
claude install anhermon/claude-public/image-gen.plugin
```

---

## Plugin catalog

### commit
**v1.0.0** — Write and execute a conventional commit automatically.

Stage your changes and say "commit" — the skill reads your diff and crafts a
[Conventional Commits](https://www.conventionalcommits.org/)-compliant message.

**Trigger phrases:** "commit", "git commit", "/commit", "commit my changes",
"commit and push", "write a commit message"

No prerequisites.

---

### code-review
**v1.0.0** — Structured code review with severity-ranked findings.

Reviews staged changes, a file, or a GitHub PR. Returns a report with P0–P3
severity levels covering security, correctness, performance, and style.

**Trigger phrases:** "review", "code review", "review my code", "/code-review",
"review my PR", "audit this", "check my code"

No prerequisites. For PR review, `gh` CLI recommended.

---

### image-gen
**v0.2.0** — AI image generation with expert prompt engineering.

Analyzes your request (icon? avatar? scene?) and builds a detailed,
model-optimized prompt. Tries API keys first, falls back to browser automation
(Higgsfield Nano Banana Pro, Google Gemini).

**Trigger phrases:** "generate an image", "create an avatar for", "icon for [app]",
"make me an image of", "design a logo for", "use nano banana", "use gemini to generate"

**Optional API keys** (add to `.env`):
```
TOGETHER_API_KEY=...   # FLUX.1-schnell-Free (free tier)
FAL_KEY=...            # ~$0.003/image
REPLICATE_API_TOKEN=...
OPENAI_API_KEY=...     # DALL-E 3 — best for text-in-image
STABILITY_API_KEY=...
```

**Browser fallback setup:**
- Higgsfield: log into higgsfield.ai in Chrome
- Gemini: log into google.com in Chrome

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
