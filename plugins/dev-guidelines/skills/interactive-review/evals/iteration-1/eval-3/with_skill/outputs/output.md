# Eval-3: "Here is the final architecture summary we agreed on. Render it in the browser."

## Decision: render-output, not interactive-review

Looking at the skill's decision table:

| Situation | Use |
|---|---|
| Output is final — just needs to be readable | `render-output` |
| Output needs user approval or changes | **this skill** |

The user's phrasing is the key signal: **"the final architecture summary we agreed on."**

- "final" → the content is settled, not a draft
- "we agreed on" → approval already happened in a prior conversation
- "Render it in the browser" → they want to read/display it, not iterate on it

This maps exactly to the first row of the decision table: **output is final, just needs to be readable**. That means `render-output` is the correct tool, not `interactive-review`.

---

## What I would say to the user

I would NOT load `interactive-review`. Instead, I would respond:

> "This looks like a final document you've already agreed on — I'll use `render-output` to display it rather than the interactive review viewer (which is for content that still needs feedback rounds).
>
> Could you paste the architecture summary? I'll render it as a styled HTML report in the browser."

Once the user provides the content, I would invoke the `/render-output` skill (which uses `~/.claude/skills/render-output/generator/render.py`) to produce a styled HTML page.

---

## Why this matters

If I had used `interactive-review` here, I would have:
1. Launched a server on port 3118 with a feedback form the user doesn't need
2. Told the user to "submit feedback" on something they already approved
3. Added unnecessary friction to what should be a simple render

The skill's decision table exists precisely to route these two cases correctly. The word "final" in the prompt is the trigger that routes away from `interactive-review`.
