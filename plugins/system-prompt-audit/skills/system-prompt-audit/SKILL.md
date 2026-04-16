# System Prompt Audit Skill

Audits and refines agent system prompts (AGENTS.md, HEARTBEAT.md, or any instruction file) against context engineering best practices. Triggered by phrases like "audit system prompt", "audit agent instructions", "refine my system prompt", "context engineering audit", or "/system-prompt-audit".

## Purpose

Poor prompts waste tokens, produce inconsistent outputs, and fail silently. This skill runs a structured nine-point audit and produces a prioritized findings table with concrete fixes. Based on context engineering best practices and informed by prompt testing methodology (ref: Prompt-Engineering-Toolkit).

## Trigger Phrases

- `audit system prompt`
- `audit agent instructions`
- `audit my AGENTS.md`
- `refine system prompt`
- `context engineering audit`
- `optimize system prompt`
- `/system-prompt-audit`

---

## Audit Dimensions

### Part A — Context Efficiency (Heartbeat / Agent-Loop Prompts)

#### 1. Wake Payload Usage
**Check:** Does the prompt use inline wake data before API calls?
**Pass:** Explicit rule to read wake payload fields and skip API round-trips when payload is sufficient.
**Fail:** No mention, or fetches unconditionally.
**Fix:** Add "Wake Payload Fast Path" rule: when payload names the issue and `fallbackFetchNeeded: false`, skip inbox fetch and go straight to checkout.

#### 2. Incremental Comment Fetching
**Check:** Does the prompt use `?after={commentId}` instead of full thread replays?
**Pass:** Explicit use of `heartbeat-context` first, check `totalComments`, fetch incrementally.
**Fail:** Full thread on every heartbeat or no mention.
**Fix:** Call `heartbeat-context` first; if `totalComments == 0`, stop; otherwise use `?after={latestCommentId}`.

#### 3. Skill Loading Discipline
**Check:** Does the prompt load full skill docs for standard workflows where direct API calls suffice?
**Pass:** Direct API calls for known endpoints; skill invocations reserved for non-standard workflows.
**Fail:** Skill loaded on every heartbeat regardless of task type.
**Fix:** Standard CRUD heartbeats → direct API; invoke skill only for unknown/non-standard procedures.

#### 4. Tool Priority
**Check:** Does the prompt enforce the correct tool hierarchy for file operations?
**Pass:** Explicit hierarchy: `Read` > `Grep` > `Glob` > `Bash`. Bash for system commands/API only.
**Fail:** Bash used for `cat`/`grep`/`find`/`ls`.
**Fix:** Add rule: never use Bash for file reads when Read/Grep/Glob are available.

#### 5. Response Verbosity
**Check:** Are comments and status updates capped?
**Pass:** Explicit limit: 1 status line + max 5 bullets. No prose paragraphs in task updates.
**Fail:** Prose comments, repeated context, no verbosity constraint.
**Fix:** Add rule: comments = status line + max 5 bullets; bold key takeaway; assume skimming reader.

---

### Part B — General Prompt Quality

#### 6. Role and Scope Clarity
**Check:** Is the agent's role, authority, and out-of-scope behavior explicitly defined?
**Pass:** Clear role statement; explicit list of what the agent does and does NOT do; escalation rules named.
**Fail:** Role is vague ("you are a helpful assistant"); no explicit scope boundaries; no escalation path.
**Fix:** Add a role statement with: who you are, what you own, what you delegate, and who you escalate to.

#### 7. Instruction Specificity
**Check:** Are instructions concrete and actionable, or abstract and aspirational?
**Pass:** Instructions use imperative verbs with measurable criteria ("always include X-Run-Id header on mutating calls").
**Fail:** Instructions use vague language ("be helpful", "do good work", "use best judgment").
**Fix:** Rewrite vague rules as specific imperatives. Replace "be concise" with "comments = 1 status line + max 5 bullets."

#### 8. Safety and Guardrails
**Check:** Does the prompt explicitly define what the agent must NOT do?
**Pass:** Explicit prohibitions: no destructive commands, no secrets exfiltration, no unassigned work, no force-pushing.
**Fail:** Only positive rules; negative constraints implied or absent.
**Fix:** Add a "Never" or "Safety" section with explicit prohibitions relevant to the agent's tools and access.

#### 9. Output Format Consistency
**Check:** Does the prompt specify expected output structure for recurring outputs?
**Pass:** Named formats for comments, plans, status updates (e.g., "comments: status line + bullets + ticket links").
**Fail:** Output format unspecified or described only in prose.
**Fix:** Add an "Output Format" or "Comment Style" section with concrete templates.

---

## Workflow

1. **Identify target file.** Ask for the path if not given. Common targets: `AGENTS.md`, `HEARTBEAT.md`, `SOUL.md`.

2. **Read the file.** Use the `Read` tool (not Bash/cat).

3. **Run the nine-point audit.** For each dimension, determine: PASS / FAIL / PARTIAL / N/A.

4. **Produce findings report.** Use this format:

   ```
   ## System Prompt Audit: <filename>

   ### Part A — Context Efficiency
   | Dimension              | Status  | Evidence / Notes                     |
   |------------------------|---------|--------------------------------------|
   | Wake Payload Usage     | PASS    | Line 12: explicit fast path rule     |
   | Incremental Comments   | FAIL    | No mention of ?after= fetching       |
   | Skill Loading          | PARTIAL | Rule exists but scope unclear        |
   | Tool Priority          | PASS    | Read > Grep > Glob hierarchy present |
   | Response Verbosity     | FAIL    | No verbosity constraint found        |

   ### Part B — General Prompt Quality
   | Dimension              | Status  | Evidence / Notes                     |
   |------------------------|---------|--------------------------------------|
   | Role and Scope Clarity | PASS    | Clear CEO role + delegation rules    |
   | Instruction Specificity| PARTIAL | Mix of concrete and vague rules      |
   | Safety / Guardrails    | PASS    | Explicit "never" list present        |
   | Output Format          | FAIL    | No comment format template           |

   ### Recommended Changes (priority order)
   1. ...
   2. ...
   ```

5. **Apply fixes.** If the user confirms, apply each recommended change using the `Edit` tool. One edit per finding.

6. **Test (optional).** After applying fixes, suggest 2–3 representative task scenarios to validate the revised prompt behaves correctly. This mirrors the comparative testing approach used in prompt engineering toolkits: before/after comparison against the same inputs.

7. **Confirm.** Report which fixes were applied and which were skipped.

---

## Output Budget

Keep the findings report under 500 tokens. Use tables — no prose per-dimension summaries. Recommendations = numbered bullets, not paragraphs.

## Error Handling

- File not found: report and ask for correct path.
- Non-instruction file: report not auditable, exit.
- All nine pass: report "All checks pass — no changes recommended."
