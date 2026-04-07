# claude-public

Angel Hermon's public collection of Claude Code plugins — install them directly from GitHub.

## Claude Code marketplace

This repository is a **marketplace**: it includes [`.claude-plugin/marketplace.json`](./.claude-plugin/marketplace.json). In Claude Code, add the marketplace URL:

`https://github.com/anhermon/claude-public`

Then install individual plugins from the catalog (for example `commit`, `code-review`, or `image-gen`). Each plugin’s source lives under [`plugins/`](./plugins/).

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

## Contributing

See [CONTRIBUTING.md](./CONTRIBUTING.md) for how to author and submit plugins.

## Code of Conduct

See [CODE_OF_CONDUCT.md](./CODE_OF_CONDUCT.md).
