# Without-Skill Response: "Show migration plan and get feedback before proceeding"

## What I Would Do (No Special Skill Loaded)

### Step 1: Locate the migration plan

I would first try to find the migration plan document. I'd say something like:

> "Let me find the migration plan you drafted."

Then I'd run a search:

```bash
find . -type f -name "*.md" | xargs grep -l -i "migration" 2>/dev/null
```

Or I'd look in common locations:

```bash
ls docs/ plans/ .claude/ 2>/dev/null
```

If I couldn't find a file automatically, I'd ask the user:

> "I don't see the migration plan as a file in the workspace. Could you point me to where it's saved, or paste the content here?"

---

### Step 2: Display the content

Once located (say it's at `docs/auth-migration-plan.md`), I'd read and display it:

```
Read docs/auth-migration-plan.md
```

Then I'd present the content directly in my response, perhaps with a brief framing:

> "Here's the auth service migration plan you drafted:
>
> ---
> [content of the file]
> ---
>
> Please review this and let me know your thoughts before we proceed with implementation."

---

### Step 3: Wait for feedback

I would end my message with an open-ended prompt to the user:

> "Does this plan look good to you? Any changes, concerns, or approvals before I start on implementation?"

---

### What I Would NOT Do

- I would not proactively open a browser, render HTML, or create a formatted review document.
- I would not use any structured feedback-collection mechanism — I'd just wait for the user to type a reply.
- I would not ask follow-up questions beyond a simple "does this look good?" — I have no protocol for structured approval vs. rejection vs. partial approval.
- I would not create a feedback file, track approval state, or gate the next step programmatically.

---

### Key Limitations Without a Skill

- No structured approval/rejection flow — the user types free-form text and I interpret it ad hoc.
- No rendered preview — the plan is shown as raw markdown in the chat window.
- No feedback capture — there's no file written, no record of what the user approved or flagged.
- No clear "proceed" gate — I would likely just start implementation whenever the user says something like "looks good" without a formal checkpoint.
- If the plan is long, it may be truncated or hard to read inline in the conversation.
