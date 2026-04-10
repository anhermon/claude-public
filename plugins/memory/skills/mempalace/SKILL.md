---
name: mempalace
description: >
  Long-term memory management using the Memory Palace pattern. Trigger on: "remember this",
  "recall from memory", "what do you know about me/this project", "manage my preferences",
  "persist this session state", "load my memory".
license: MIT
metadata:
  audience: developers
  workflow: memory-persistence
---

# Memory Palace (MemPalace)

Persistent, structured session memory. Unlike the short-term context, MemPalace stores 
long-term facts, preferences, and project states in a hierarchical directory.

## Storage Hierarchy

MemPalace uses a hidden `.memory/` directory in the current project root or a global
`~/.memory/` directory.

```
.memory/
  project.json      # Project-specific facts, tech stack, conventions
  preferences.json  # User-specific coding styles, tool preferences
  sessions/         # Snapshot of key milestones from previous sessions
  pm-state.json     # Orchestrator state (e.g., BMAD / Project Manager)
```

---

## Operation: REMEMBER

**Trigger:** "remember this", "save this preference", "log this project fact".

1. **Classify the fact:**
   - **Preference:** "I prefer Bun over Node", "Use arrow functions", "No semicolons"
   - **Project Fact:** "This repo uses Hono", "DB is Postgres", "Main entry is src/index.ts"
   - **State:** Progress on a specific goal or task

2. **Update the relevant JSON file:**
   - Read the existing file
   - Merge the new fact (prevent duplicates)
   - Write back to `.memory/<file>.json`

3. **Confirm:** Report exactly what was committed to memory.

---

## Operation: RECALL

**Trigger:** "recall", "what do we know", "load context", or proactively at session start.

1. **Load memory files:** Read `.memory/project.json` and `.memory/preferences.json`.
2. **Inject context:** Surface the most relevant facts to the current session.
3. **Format:**
   ```
   [Memory Palace: <Scope>]
   - Fact 1...
   - Fact 2...
   ```

---

## Operation: SNAPSHOT

**Trigger:** End of session or significant milestone.

1. **Capture session summary:** High-level overview of what was built and why.
2. **Save to sessions/**: Create a timestamped markdown file in `.memory/sessions/`.
3. **Link:** Reference the session in `project.json` history.

---

## Best Practices

- **Atomic Facts:** Keep each memory entry small and specific.
- **De-duplication:** Check if a fact already exists before adding it.
- **Conflict Resolution:** If a new fact contradicts an old one, ask the user.
- **Privacy:** Never store secrets, API keys, or credentials in MemPalace.
