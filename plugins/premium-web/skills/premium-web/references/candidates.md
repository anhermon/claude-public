# Candidates protocol (premium-web 2.0)

Build several competing candidates, let the user choose in the mod pane, finish only the winner.

## 1. How many (N)

1. A number the user states in the request wins: "3 options", "five candidates", "just one", "give me a couple" (2).
2. Else call the mod tool `premium_web_get_settings` (full name `mcp__premium-web__premium_web_get_settings`); it returns
   `{"candidateCount": n}` from the plugin setting (default 3, range 1-6).
3. Else 3. Cap at 6 (more than 6 is noise the user cannot compare); say so if the user asked for more.
4. N = 1 means no choice to offer: run the normal single build and skip the pane.

Never lower N to save time without telling the user; the time box per candidate is what bounds cost.

## 2. Distinctness gate (before any building)

Write one table row per candidate:

| id | style recipe (styles.md) | palette family | type voice | layout shape | wow family (wow.md) | "left alone it becomes ___" |

Rules, checked by you before dispatch:
- No two candidates share more than two of: style recipe, palette family, type voice, layout shape, wow family.
- Every candidate has its **own** signature wow idea with its own acceptance test (wow.md procedure, >= 5 ideas
  considered per candidate, then one picked). Two candidates with the same wow family fail the gate.
- genre-escape.md applies to each candidate on its own, not to the set as a whole.
- Same facts, different expression: every candidate uses the same proof inventory (trust.md). Candidates differ in
  design, never in claims.
- A "safe" candidate and a "bold" candidate are not two directions. Vary the concept, not the risk dial.
If two rows fail, rewrite the weaker one. Do not build near-duplicates and call them options.

### App mode (mode `app`: the request is WORK, a tool people operate)

Mode comes from SKILL.md routing: WORK -> `app`, READ -> `marketing`, MIXED -> two scoped deliverables (below).
In `app` mode a candidate is a **working prototype of the primary flows**, not a page: clickable, keyboard-reachable,
realistic sample data that is visibly labelled "sample" (never real customer data, never invented claims). The gate
above still applies, plus:

- **Interaction model and information architecture are gate columns**, not only palette/type. Add to every row:
  `interaction model` (e.g. table + inspector, command palette first, board, wizard, canvas) and `IA` (primary
  nav shape, what is one click from the first screen, where the primary object lives). Two candidates that share
  an interaction model AND an IA fail the gate even with different palettes; they share at most one of the two.
- Name 2-4 **primary tasks** from intake (the verbs the user does daily) and use the same tasks for every candidate.
- **Marketing sections are banned from candidates**: no hero pitch, feature grid, testimonial strip, pricing or CTA
  band added to satisfy the critic or a gate. If a gate or critic check seems to demand one, STOP and report that
  gate as mismatched for app mode (name the gate and the check); do not pad the app to pass it.

Capture per candidate (record, do not iterate to green):
1. the first-screen screenshot (`.premium-web/shots/<id>.png`);
2. **one screenshot per primary task end state** (`.premium-web/shots/<id>-t<n>.png`), driven through the real UI;
3. **recorded step counts** per task: clicks plus keystrokes from the first screen to the end state, and
   time-to-first-result (seconds to the first useful result after the task starts). Count by performing the task,
   not by estimating; put them in `tasks[].steps`.

**MIXED requests** (some READ, some WORK, e.g. a product site plus its console): split into two scoped deliverables,
each with its own mode and its own gate, build and decision. Present them one at a time: write `candidates.json` for
the first deliverable (`mode` set, scope named in `brief`), present, handle the reply to a pick, then archive that file
as `.premium-web/candidates.<scope>.json` and run the second. Keep shared tokens (palette, type, proof inventory) so
the two feel like one product, but never apply one mode's rules to the other's pages.

## 3. Build (parallel, bounded, checkpointed)

- One agent per candidate, in its own folder `.premium-web/build/<id>/` (a git worktree is fine). Folders must live
  inside the project; the mod refuses paths that escape it.
- Give each agent: its direction row, the shared intake and proof inventory, tokens (palette, fonts), the wow
  acceptance test, a time box (default 25 minutes) and the rule "write progress and findings to
  `<folder>/NOTES.md` as you go; a killed run must lose nothing". Subagents must not fork.
- Assume some stall. Check progress on disk at the half-way mark; finish a stalled candidate yourself or replace it,
  do not wait indefinitely.
- Imagery quota is shared: generate hero/plate images per candidate sparingly, draw technical figures in code.

## 4. Critic and screenshots (one round)

For each candidate run step 9 once (works, not templaty, section critic). Keep the numbers. In `app` mode run it in
tool/app mode and add the task capture from section 2 (task end-state shots and step counts). Capture a 1440 hero
screenshot to `.premium-web/shots/<id>.png` (PNG only; the terminal pane draws it). Do not iterate a candidate to green
here; that effort is spent on the winner only.

## 5. Present and stop

Write `.premium-web/candidates.json` in the project root (the session's working directory):

```json
{
  "brief": "one line: what is being built, for whom",
  "round": 1,
  "candidates": [
    {
      "id": "a",
      "label": "Halcyon",
      "direction": "one-line concept",
      "dir": ".premium-web/build/a/dist",
      "url": "https://optional-deployed-preview.example",
      "screenshot": ".premium-web/shots/a.png",
      "scores": { "wow": 4, "sections": "4/4/3" },
      "notes": "what is strong, what is weak",
      "tasks": [
        { "task": "Triage a failed run", "steps": 4, "result": "cause visible in the inspector",
          "screenshot": ".premium-web/shots/a-t1.png" },
        { "task": "Find last night's deploy", "steps": "2 clicks, 3 keys, 0.9s to first result", "result": "row highlighted" }
      ]
    }
  ]
}
```

`tasks` is **optional and app-mode only** (omit it for marketing candidates; they work unchanged). Top-level `mode`
(`"marketing"` or `"app"`) is optional too; `app` is shown in the pane header.

Limits (the mod validates and rejects the file otherwise): ids `[a-z0-9-]{1,32}` and unique; 1-9 candidates;
`label` <= 80, `direction` <= 300, `notes` <= 2000 characters; `dir` and `screenshot` must resolve **inside the
project folder** (`screenshot` a `.png`); `url` must be http(s); each candidate needs a `dir` or a `url`; <= 12
`scores` entries; `tasks` <= 8 per candidate, each `task` (required) <= 200 characters, `steps` an integer 0-9999 or a string
<= 100 characters, `result` <= 300, optional `screenshot` a `.png` inside the project folder; file <= 256 KB. `dir` is the folder holding the built `index.html`: the mod serves it on
127.0.0.1 when the user presses Open in browser. Never put secrets in this file.

Then call `premium_web_present_candidates` (no arguments). It opens the pane (or toasts "run /candidates" in a narrow
terminal) and returns a reminder. **Stop. Do not edit or build anything until the next user message.** The user can
open each candidate, pick one, request changes on one, or send feedback on all; the mod also writes
`.premium-web/decision.json` (`round`, `picked`, `feedback[]`, timestamps).

## 6. Handle the reply

| Message starts with | Do |
|---|---|
| `I picked candidate X` | Take only candidate X through the full step-9 loop (all three gates, iterate to green, wow >= 4). Delete or archive the other build folders only if the user asks. Deliver. |
| `Feedback on candidate X` | Apply it to X only, re-run its critic round, bump `round`, refresh its screenshot, rewrite `candidates.json`, present again, stop. |
| `Feedback on all candidates` | Apply to every candidate, keep them distinct (re-run the gate), bump `round`, present again, stop. |
| anything else | Treat as normal conversation; the candidates stay as they are. |

Feedback never lowers the bar: a requested change that breaks the rubric is applied and flagged, not silently refused.

## 7. Chat fallback (no mod)

Use it when `premium_web_present_candidates` does not exist, errors, or the session is non-interactive (Claude Code
< 2.1.287, mods disabled by policy, `claude -p`). Still write `candidates.json` (it is a useful record). Then in chat:
for each candidate print label, the one-line direction, scores, the preview URL or `node scripts/serve.mjs <dir>` command,
and the screenshot path; in `app` mode also each task with its step count and end-state shot path; then ask exactly: "Pick one (A/B/C), or tell me what to change on which candidate." and STOP.
Handle the answer as in section 6.

## 8. Mod notes

Mods are unsandboxed code running with the user's permissions; this one is small on purpose (see plugin README).
The pane reads/writes only `.premium-web/` files, serves candidate folders on 127.0.0.1 via `python3 -m http.server`,
and sends the user's pick/feedback back to you as a message. If the user has not installed the mod, the skill still
works through the chat fallback.
