# code-review plugin

Review code for correctness, security, performance, and style.

## Skills

**code-review** — Reviews staged changes, a file, or a PR and returns structured findings
with P0–P3 severity levels. P0 = security, P1 = bugs, P2 = performance, P3 = style.

Trigger phrases: "review", "code review", "review my code", "review this", "review my PR",
"review changes", "/code-review", "check my code", "audit this".

## How it works

1. **Scope** — Detects what to review: `git diff HEAD`, a specific file, or a GitHub PR.
2. **Analyze** — Checks security, correctness, performance, and maintainability.
3. **Report** — Returns a structured markdown report grouped by severity.
4. **Fix** (optional) — If you say "review and fix", applies P0/P1 fixes automatically.

## Severity levels

| Level | Meaning |
|-------|---------|
| P0-SECURITY | Exploitable vulnerability — block merge |
| P1-BUG | Incorrect behavior, crash, data loss — block merge |
| P2-PERF | Performance problem at scale — fix before ship |
| P3-STYLE | Readability, convention — nice to have |
| LGTM | No issues found |

## Source

`claude-public` — Angel Hermon's public Claude/Paperclip plugins.
