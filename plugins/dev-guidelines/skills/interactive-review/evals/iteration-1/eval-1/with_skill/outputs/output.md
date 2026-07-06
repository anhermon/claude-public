# Cognitive Eval: interactive-review skill
## Task: "I just finished drafting a migration plan for the auth service. Show it to the user and get their feedback before we proceed with implementation."

---

## What I would do, step by step

### Step 1 — Write the content to a temp file

I already have the drafted migration plan. I would save it to:

```
/tmp/auth-migration-review.md
```

The content would be whatever was drafted — for example:

```markdown
# Auth Service Migration Plan

## Overview
Migrate auth service from legacy session-based auth to JWT-based auth with refresh tokens.

## Phases

### Phase 1 — Audit current auth surface
- Identify all endpoints that rely on session middleware
- Catalog session store usage (Redis keys, TTLs)
- Map token issuance and validation flows

### Phase 2 — Introduce JWT layer alongside sessions
- Add JWT issuance endpoint (`POST /auth/token`)
- Run both session and JWT auth in parallel (feature flag: `USE_JWT_AUTH`)
- No client-side changes required in this phase

### Phase 3 — Migrate clients
- Update web client to use JWT flow
- Update mobile clients
- Update service-to-service calls

### Phase 4 — Remove session auth
- Remove session middleware
- Clean up Redis session store
- Remove feature flag

## Rollback Plan
- Phase 1: No rollback needed (read-only audit)
- Phase 2: Disable feature flag to fall back to sessions
- Phase 3: Re-enable session auth path per client
- Phase 4: Revert via git; restore Redis session store from backup

## Risks
- Session/JWT clock skew during parallel phase
- Token expiry UX changes for long-lived sessions
```

I would write this to `/tmp/auth-migration-review.md` using the Write tool.

---

### Step 2 — Start the interactive viewer

I would run this exact command:

```bash
python3 ~/.claude/skills/interactive-review/server.py \
  /tmp/auth-migration-review.md \
  --workspace /tmp/auth-migration-workspace \
  --title "Auth Service Migration Plan"
```

The server starts on **port 3118** and opens the browser automatically. Feedback will be saved to `/tmp/auth-migration-workspace/feedback.json`.

---

### Step 3 — Tell the user and wait

I would say exactly:

> "Rendered → http://localhost:3118 — review and submit feedback in the browser."

Then I would **stop and wait**. I would not continue implementing anything until the user says they submitted feedback or explicitly tells me to proceed.

---

### Step 4 — Read feedback (after user signals they submitted)

Once the user indicates they've submitted feedback, I would run:

```bash
cat /tmp/auth-migration-workspace/feedback.json
```

Then evaluate the stopping condition:
- If `feedback` is empty string → user approved, plan is final, proceed to implementation
- If feedback contains "looks good", "approved", or "done" → stop iterating, plan is final
- Otherwise → revise the markdown, tell the user "Updated — refresh the page", loop back to Step 3

---

### Step 5 — Revise if needed

If the user's feedback requires changes (e.g., "Add more detail to the rollback steps for Phase 4"), I would:

1. Edit `/tmp/auth-migration-review.md` in place with the requested changes
2. Tell the user: "Updated — refresh the page to see the changes."
3. Wait again for another round of feedback

No server restart needed for content edits — the browser refresh picks up the updated file automatically.

For significant structural changes (e.g., complete reorganization), I would restart the server:

```bash
kill $(lsof -ti :3118) 2>/dev/null
python3 ~/.claude/skills/interactive-review/server.py \
  /tmp/auth-migration-review.md \
  --workspace /tmp/auth-migration-workspace \
  --title "Auth Service Migration Plan"
```

---

### Final state

Once the user approves (empty feedback or explicit approval), I would say:

> "Approved. Migration plan is final — proceeding with implementation."

Then continue with the implementation phase.
