---
name: align-to-intent
description: >
  Iteratively align a tool, plugin, or system to its declared intent. Clarify the intent
  (interviewing the user if vague), exercise the tool as its target persona, write evidence-based
  feedback against intent, refine, and loop until aligned. Use whenever the user asks to
  "audit", "align", "dogfood", or "refine" a tool against a stated goal.

  Trigger on: "audit X against its intent", "is X doing what it's supposed to do",
  "dogfood X", "refine until aligned", "alignment loop", "/align".
---

# Align to Intent — iterative refinement protocol

A repeatable loop for validating that a tool (plugin, skill, agent, product) actually satisfies
its declared purpose. Produces a living **FEEDBACK_REPORT.md** at the tool root and a queue of
concrete changes implemented over successive iterations.

## When to use

- User asks to audit a plugin/tool against a goal.
- A tool has grown complex and drifted from its original purpose.
- After shipping a tool, to close the "does it actually work for the stated user?" loop.

## The loop

### Step 0 — Clarify intent (blocking)

Read any stated goal verbatim. Then decide if it is **operationally clear**:

- WHO is the target persona? (human? agent? both?)
- WHAT surfaces must exist? (CLI / dashboard / skill / agent / one-shot command?)
- WHAT is the out-of-box success criterion? (single command? zero-config? <5 min?)
- WHAT improvements count as "done"? (classified + prioritized? user-selectable? auto-applied?)

If **any** of these is ambiguous, use `AskUserQuestion` to interview the user before proceeding.
Do not guess. Save the clarified intent as the first section of `FEEDBACK_REPORT.md`.

### Step 1 — Inventory

Enumerate what the tool currently exposes: commands, agents, skills, CLI verbs, dashboards, hooks.
This is the factual baseline; no judgement yet.

### Step 2 — Exercise the tool

Use the tool as the target persona would. If the intent targets "an AI agent", *be* the agent —
invoke the commands, follow the skills, consume the outputs. If it targets a human, describe
the human's path and where friction appears.

Capture raw observations: what worked, what blocked, what was missing, what was redundant.

### Step 3 — Score gaps vs intent

For each element of the declared intent, produce a row:

| # | Gap | Severity | Evidence |

Severity: HIGH if it breaks a load-bearing intent claim; MEDIUM if it degrades the promise;
LOW if cosmetic. Evidence must cite a file, command, or observation — never intuition alone.

Also record **wins** — things already aligned. A plugin in iteration N+1 can regress, so the
wins list is the guardrail.

### Step 4 — Prioritize + act

Pick the top 1–3 HIGH gaps for this iteration. Act on them. Defer the rest to a **queued**
section of the report so they're visible but not lost. Explicit feedback from the user is
treated as top priority regardless of the audit's own ranking.

### Step 5 — Write/update FEEDBACK_REPORT.md

One new section per iteration, dated. Keep prior iterations — this is a diary, not a snapshot.
Each iteration has: actions taken, what was not addressed and why, and queued items.

### Step 6 — Loop or exit

Re-enter Step 2 and exercise the tool again. Stop when:

- No HIGH gaps remain,
- User confirms alignment, or
- Marginal cost of next iteration exceeds expected gain.

## Conventions

- **Living doc:** `FEEDBACK_REPORT.md` lives at the tool's repo root, always appended to, never overwritten.
- **Evidence > opinion:** every gap row cites a file path, command output, or user quote.
- **User feedback is sovereign:** explicit user guidance jumps the queue.
- **Minimal surface changes:** prefer one new command + docs over large rewrites unless the audit shows structural drift.
- **Dogfood:** if the plugin being aligned has its own audit/analysis tooling, run it against itself.

## Output artifacts

- `FEEDBACK_REPORT.md` at tool root (living)
- Concrete code/docs changes per iteration
- Optional: `.claude/memory` entry naming the tool and its alignment status so future sessions resume the loop
