---
name: interactive-review
description: >
  Render a plan, report, or analysis in a browser-based interactive viewer where
  the user can submit feedback directly from the page. Claude reads the feedback
  and iterates. Use this instead of render-output whenever the output needs user
  approval or changes before it's final — plans, proposals, designs, eval results,
  architecture decisions, task breakdowns. Trigger on: "show me", "review this",
  "get my feedback", "iterate on", "send for review", or any output that will
  need at least one round of user input before it's done.
---

## When to use this vs render-output

| Situation | Use |
|---|---|
| Output is final — just needs to be readable | `render-output` |
| Output needs user approval or changes | **this skill** |
| Eval results need grading | skill-creator eval viewer |

---

## Workflow

### Step 1 — Write the content

Write the plan, report, or analysis as markdown. Save to a temp file:

```
/tmp/<topic>-review.md
```

Use standard markdown. No special schema required (unlike render-output).

### Step 2 — Start the interactive viewer

```bash
python3 ~/.claude/skills/interactive-review/server.py \
  /tmp/<topic>-review.md \
  --workspace /tmp/<topic>-workspace \
  --title "<Human-readable title>"
```

- Server starts on **port 3118** and opens the browser automatically.
- Feedback is saved to `/tmp/<topic>-workspace/feedback.json`.
- The page re-reads the markdown on each browser refresh — edit the file and refresh to see updates without restarting.

**With selectable options** (proposals, multi-choice decisions):
```bash
python3 ~/.claude/skills/interactive-review/server.py \
  /tmp/<topic>-review.md \
  --options /tmp/<topic>-options.json \
  --preview-dir /tmp/<topic>-previews \   # optional: serve preview files at /preview/<file>
  --workspace /tmp/<topic>-workspace \
  --title "<Human-readable title>"
```

Options JSON format — each option can include a `preview_url` (relative `/preview/file.html` or absolute):
```json
[
  {"id": "1", "label": "Short label", "description": "One-line explanation.", "preview_url": "/preview/preview-1.html"},
  {"id": "2", "label": "Another option", "description": "..."}
]
```

### Step 3 — Hand off to user

Output exactly this, then stop:

> **Open http://localhost:3118**, review the content, and submit — then say **proceed**.

Do NOT continue until the user responds. Do NOT ask "should I check feedback?" — just wait.

### Step 4 — Read feedback immediately on return

**As soon as the user responds**, read the feedback file before doing anything else:

```bash
cat /tmp/<topic>-workspace/feedback.json
```

**Feedback.json format:**
```json
{
  "reviews": [
    {
      "feedback": "Add a risk section for the DB migration",
      "timestamp": "2026-03-20T10:42:00Z",
      "selected": ["2", "4"]
    }
  ]
}
```

- `feedback` — free-text from the textarea (empty = approved)
- `selected` — array of option IDs checked (only present when `--options` was used)

**Act on the latest review entry** (last item in `reviews` array). Do not re-ask the user what they want — read it and act.

**Stopping condition:**
- `feedback` is empty string AND no `selected` (or `selected` is empty) → user approved, stop iterating
- `feedback` contains "looks good", "approved", "done" → stop
- Otherwise → revise the markdown / implement `selected` items, then loop back to Step 3

### Step 5 — Revise and re-render

Edit the markdown file in place — the browser just needs a refresh, no server restart needed.

For significant structural changes, kill and restart the server:
```bash
kill $(lsof -ti :3118) 2>/dev/null
python3 ~/.claude/skills/interactive-review/server.py /tmp/<topic>-review.md ...
```

---

## Example session

```
User: "Draft a migration plan for the auth service and show it to me"

Claude:
1. Writes /tmp/auth-migration-review.md
2. Runs server.py → browser opens
3. Says: "Open http://localhost:3118, review, and submit — then say proceed."
   [Stops. Waits.]

User: "proceed"

Claude:
4. Reads feedback.json immediately — finds: "Add rollback steps for each phase"
5. Edits the markdown, says: "Added rollback steps. Refresh the page → http://localhost:3118"
   [Stops. Waits.]

User: "proceed"

Claude:
6. Reads feedback.json — feedback is empty string
7. Says: "Approved. Plan is final." Stops iterating.
```

---

## Workspace layout

```
/tmp/<topic>-workspace/
└── feedback.json     ← written by the server when user submits
```

If you want to keep iterations, use a versioned workspace:
```
/tmp/<topic>-workspace/
├── iteration-1/feedback.json
├── iteration-2/feedback.json
└── ...
```

Pass `--workspace /tmp/<topic>-workspace/iteration-N` for each round.
