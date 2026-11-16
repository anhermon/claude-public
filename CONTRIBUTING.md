# Contributing to claude-public

Thank you for your interest in contributing! This repo is Angel Hermon's public collection
of Claude Code plugins. Contributions that add useful, well-crafted plugins are welcome.

**Layout:** Each plugin’s source lives under `plugins/<name>/` (manifest, README, and skill). [`.claude-plugin/marketplace.json`](./.claude-plugin/marketplace.json) lists every plugin for Claude Code’s marketplace UI.

---

## What is a plugin?

A **plugin** is a directory under `plugins/<name>/`, listed in the marketplace, that users install with
`claude plugin install <name>@claude-public`. It contains:

```
.claude-plugin/plugin.json   ← manifest (required)
README.md                    ← user-facing description (required)
skills/<name>/SKILL.md       ← skill instructions (required)
```

The `SKILL.md` is a markdown file with YAML front matter that Claude reads as a skill:
it defines when to trigger and provides step-by-step instructions for Claude to follow.

---

## Plugin naming conventions

| Item | Convention | Example |
|------|------------|---------|
| Plugin directory | `plugins/<name>/` | `plugins/llm-wiki/` |
| Skill directory | `plugins/<name>/skills/<name>/` | `plugins/llm-wiki/skills/llm-wiki/` |
| Skill name | lowercase, hyphenated | `agent-repo-search` |
| Version | semver `X.Y.Z` | `1.0.0` |

---

## `plugin.json` schema

```json
{
  "name": "my-skill",
  "version": "1.0.0",
  "description": "One sentence: what it does and when to use it.",
  "author": { "name": "Your Name" },
  "keywords": ["keyword1", "keyword2"]
}
```

All fields are required. `description` appears in the plugin catalog — keep it concise
and scannable (under 200 characters).

---

## `SKILL.md` format

```markdown
---
name: my-skill
description: >
  One or two sentences for Claude. Includes the trigger phrases so Claude knows when
  to activate this skill. Example: "Trigger on: 'do X', '/x', 'help with X'."
metadata:
  version: "1.0.0"
  author: "Your Name"
---

# Skill Title

Brief intro.

## Step 1: ...
## Step 2: ...
```

**Tips for writing good skills:**
- Be explicit and step-by-step. Claude follows instructions literally.
- List trigger phrases in the `description` front matter — this is how Claude decides
  when to load the skill.
- Prefer concrete bash commands and code snippets over vague instructions.
- Keep each skill focused: one skill, one job.
- Test against real scenarios before submitting.

---

## Submitting a plugin

1. **Fork** this repo and create a feature branch:
   ```bash
   git checkout -b feature/my-skill-name
   ```

2. **Add your files:**
   - `plugins/my-skill/` — `.claude-plugin/plugin.json`, `README.md`, and `skills/my-skill/SKILL.md`
   - A `README.md` with an install line and an example
   - An entry in [`.claude-plugin/marketplace.json`](./.claude-plugin/marketplace.json) (`name`, `source`, `description`, `category`, and a `version` matching `plugin.json`)

3. **Validate and test locally:**
   ```bash
   sh scripts/validate.sh
   ```
   It must end with `validate: OK`. Then verify the skill triggers correctly.

4. **Open a PR** against `main`. Include in the PR description:
   - What the skill does
   - Trigger phrases
   - Any prerequisites (API keys, tools, etc.)

5. **Review** — the maintainer will review and merge or request changes.

---

## Quality bar

Plugins in this repo should meet a basic quality bar:

- [ ] Skill triggers reliably on the documented phrases
- [ ] Steps are clear and concrete, not vague
- [ ] No hardcoded personal paths (use `~/` or env vars)
- [ ] `plugin.json` has all required fields with accurate description
- [ ] Tested at least once against a real scenario

To stay in the repo a plugin must also meet the four criteria under "What belongs here" in the [README](./README.md#what-belongs-here): no official or built-in equivalent, works on a clean machine, README with install line and example, and tests or evals.

---

## Code of Conduct

See [CODE_OF_CONDUCT.md](./CODE_OF_CONDUCT.md).

---

## Questions?

Open an issue with the `question` label.
