# Without Skill Response: Generate a task breakdown and send it for review

## What I would do (no skill loaded)

Given the task "Generate a task breakdown for the API redesign project and send it for review," here is exactly what I would do:

---

### Step 1: Ask clarifying questions

Before generating anything, I would ask the user several questions because the request is ambiguous:

- "What is the API redesign project? Do you have existing documentation, a spec, or a list of goals I can work from?"
- "Who should this be sent to for review, and how — email, Slack, GitHub PR, or something else?"
- "What format do you want the task breakdown in — a markdown file, a Jira-style list, a spreadsheet?"
- "Should I create this breakdown from scratch or do you have existing context I should use?"

I would not proceed until these are answered, because I have no context about the project and no way to "send" anything without knowing the target and method.

---

### Step 2: If the user provides context

Assuming the user responds with something like: "Here's the project brief [pasted text]. Generate a markdown breakdown and post it to Slack in #engineering-review."

I would:

1. Read the provided context carefully.
2. Generate a markdown task breakdown like this:

```markdown
# API Redesign — Task Breakdown

## Phase 1: Discovery & Planning
- [ ] Audit existing API endpoints and document current behavior
- [ ] Identify pain points and gather stakeholder requirements
- [ ] Define versioning strategy (v1 → v2)

## Phase 2: Design
- [ ] Draft new endpoint structure and resource model
- [ ] Define authentication/authorization changes
- [ ] Write OpenAPI spec for new API surface

## Phase 3: Implementation
- [ ] Implement new endpoints in parallel with legacy
- [ ] Write integration tests for all new endpoints
- [ ] Deprecate old endpoints with sunset headers

## Phase 4: Migration
- [ ] Update internal consumers to new API
- [ ] Publish migration guide for external consumers
- [ ] Monitor error rates post-cutover

## Phase 5: Cutover
- [ ] Remove deprecated endpoints
- [ ] Update API documentation site
- [ ] Communicate final cutover to all consumers
```

3. Then I would stop and tell the user:

> "Here is the task breakdown. To send it for review, I need more information:
> - What channel or person should receive this?
> - Should I create a GitHub issue/PR, send a Slack message, create a Notion page, or something else?
> - Do you want me to write it to a file on disk first?"

---

### Step 3: Attempt to "send" — but hit a wall

Without a skill that knows how to integrate with external systems (Slack, GitHub, email, Jira, etc.), I cannot actually "send" anything. I would:

- If the user says "post to Slack" — I would tell them: "I don't have Slack integration available. You can copy this markdown and paste it into the channel, or I can write it to a file you can share."
- If the user says "create a GitHub issue" — I would run:
  ```bash
  gh issue create --title "API Redesign: Task Breakdown for Review" --body "$(cat /tmp/api-redesign-breakdown.md)" --label "planning,review-needed"
  ```
  ...but only if `gh` is authenticated and a repo context is known. I would first run `gh auth status` to verify.
- If the user says "write it to a file" — I would write it to a path they specify, or default to something like `./docs/api-redesign-breakdown.md`.

---

### Summary of limitations without a skill

| What was asked | What I can actually do |
|---|---|
| Generate a task breakdown | Yes, but requires project context from the user |
| Send it for review | Cannot without knowing: to whom, via what channel, with what tool |
| Autonomous end-to-end execution | No — I would ask at minimum 2-3 clarifying questions before proceeding |

**Key gap:** Without a specialized skill, the "send for review" step requires significant user involvement to specify the target, method, and authentication. I would produce the breakdown but stall on delivery, ultimately delegating the "send" action back to the user or asking them to confirm specifics before I attempt any outbound action.
