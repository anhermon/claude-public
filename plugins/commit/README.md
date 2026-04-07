# commit plugin

Write conventional commits automatically.

## Skills

**commit** — Stage changes and write a Conventional Commits-compliant message from the diff.
No need to craft a message yourself — the skill reads the diff and determines the right type,
scope, and summary.

Trigger phrases: "commit", "commit my changes", "commit this", "git commit",
"write a commit", "make a commit", "commit and push".

## How it works

1. **Stage** — Stages all tracked modifications (or specific files if you name them).
2. **Diff** — Reads `git diff --cached` to understand what changed.
3. **Compose** — Writes a Conventional Commits message: `type(scope): summary` with a body
   when the change warrants explanation.
4. **Commit** — Runs `git commit`. Pushes if you ask.

## Commit types

| Type | When |
|------|------|
| `feat` | New feature |
| `fix` | Bug fix |
| `refactor` | Code restructure, no behavior change |
| `perf` | Performance improvement |
| `test` | Tests added or updated |
| `docs` | Documentation only |
| `chore` | Tooling, deps, config |
| `ci` | CI/CD changes |

## Source

`claude-public` — Angel Hermon's public Claude/Paperclip plugins.
