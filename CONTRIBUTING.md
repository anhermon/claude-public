# Contributing to claude-public

Thank you for your interest in contributing! This repo is Angel Hermon's public collection
of Claude Code plugins. Contributions that add useful, well-crafted plugins are welcome.

---

## What is a plugin?

A **plugin** is a `.plugin` file — a zip archive that Claude Code can install directly.
It contains:

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
| Plugin file | `<name>.plugin` | `commit.plugin` |
| Skill directory | `skills/<name>/` | `skills/commit/` |
| Skill name | lowercase, hyphenated | `code-review` |
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

## How to build a `.plugin` file

The `.plugin` file is a standard zip archive. You can create it with any zip tool:

```bash
# From the directory containing .claude-plugin/, README.md, and skills/
zip -r my-skill.plugin .claude-plugin/ README.md skills/my-skill/
```

Or use Node.js, Python, or any zip library. The file must be a valid ZIP with no
compression (stored) or deflate compression — both work with Claude Code.

---

## Submitting a plugin

1. **Fork** this repo and create a feature branch:
   ```bash
   git checkout -b feature/my-skill-name
   ```

2. **Add your files:**
   - `my-skill.plugin` — the installable zip
   - `skills/my-skill/SKILL.md` — source skill (for review and discoverability)

3. **Test the plugin locally:**
   ```bash
   claude install ./my-skill.plugin
   ```
   Verify the skill is listed and triggers correctly.

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

---

## Code of Conduct

See [CODE_OF_CONDUCT.md](./CODE_OF_CONDUCT.md).

---

## Questions?

Open an issue with the `question` label.
