---
name: commit
description: >
  Write and execute a conventional commit. Trigger on: "commit", "git commit", "/commit",
  "commit my changes", "commit this", "write a commit", "make a commit", "commit and push",
  "save my work". Stages changes, writes a Conventional Commits-compliant message, and runs
  `git commit`. Optionally pushes when asked.
metadata:
  version: "1.0.0"
  author: "Angel Hermon"
---

# Conventional Commit Skill

Stages changes and writes a high-quality Conventional Commits message automatically.
You only need to say "commit" — the skill inspects the diff and crafts the message.

---

## Step 1: Understand the Current State

```bash
git status --short
git diff --cached --stat
git diff --stat
```

If nothing is staged and nothing is modified, report "Nothing to commit" and stop.

---

## Step 2: Stage Files

If the user specified files (e.g. "commit src/foo.ts"), stage only those:
```bash
git add <specified-files>
```

Otherwise, stage all tracked modifications:
```bash
git add -u
```

If there are untracked files the user probably wants included, ask before staging them.
For new files explicitly mentioned by the user, stage them directly.

---

## Step 3: Read the Diff

```bash
git diff --cached
```

Read the full diff. Understand:
- **What changed** (code-level: functions added/removed/modified, config updated, etc.)
- **Why it likely changed** (infer from context, variable names, surrounding code)
- **Scope**: which package, module, or feature area is affected

---

## Step 4: Write the Commit Message

Follow [Conventional Commits v1.0.0](https://www.conventionalcommits.org/).

### Format

```
<type>(<scope>): <short summary>

[optional body — required for non-trivial changes]

[optional footer(s)]
```

### Type selection

| Type | Use when |
|------|----------|
| `feat` | New feature or capability |
| `fix` | Bug fix |
| `refactor` | Code restructure with no behavior change |
| `perf` | Performance improvement |
| `test` | Adding or updating tests |
| `docs` | Documentation only |
| `style` | Formatting, whitespace (no logic change) |
| `chore` | Build, tooling, deps, config (no app logic) |
| `ci` | CI/CD pipeline changes |
| `revert` | Reverts a previous commit |

### Scope

Derive from the affected area: module name, directory, component, or package.
Examples: `auth`, `api`, `dashboard`, `deps`, `cli`, `config`.

Leave scope empty only when the change is genuinely cross-cutting.

### Summary line rules

- Imperative mood: "add", "fix", "remove", "update" — not "added", "fixed"
- Max 72 characters
- No period at the end
- Lowercase after the colon

### Body (include when the diff is non-trivial)

- Explain *why*, not *what* (the diff shows what)
- Wrap at 72 characters
- Separate from summary with a blank line

### Breaking changes

If the change breaks a public API or interface, add:
```
BREAKING CHANGE: <description of what broke and migration path>
```

### Issue references (if known)

```
Closes #123
Refs #456
```

---

## Step 5: Commit

```bash
git commit -m "$(cat <<'EOF'
<type>(<scope>): <summary>

<body if needed>

<footers if needed>
EOF
)"
```

Confirm to the user:
- The commit hash and summary line
- Files committed
- Whether the working tree is clean

---

## Step 6: Push (if requested)

If the user said "commit and push" or "push":
```bash
git push
```

If the branch has no upstream set:
```bash
git push -u origin $(git branch --show-current)
```

Report the remote URL and branch name after a successful push.

---

## Error Reference

| Error | Cause | Fix |
|-------|-------|-----|
| `nothing to commit` | No staged changes | Report and stop |
| `not a git repository` | Not inside a git repo | Report the working directory |
| `rejected (non-fast-forward)` | Remote has newer commits | Run `git pull --rebase` first |
| `pre-commit hook failed` | Hook blocked the commit | Read the hook output, fix the issue |
| Permission denied on push | Auth issue | Check SSH key or HTTPS credentials |
