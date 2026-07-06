---
name: para-memory-files
description: >
  PARA-based working memory for long-lived agents. Use for compact memory:
  preferences, project facts, current state, and weekly synthesis. Pair with
  MemPalace for deep verbatim recall.
license: MIT
metadata:
  audience: developers
  workflow: memory-persistence
---

# PARA Memory Files (Working Memory)

PARA is the compact, curated memory layer:

- `Projects`: active deliverables with deadlines
- `Areas`: ongoing responsibilities
- `Resources`: reference knowledge
- `Archives`: inactive material

Use PARA for low-token context and fast day-to-day recall.

Benchmark-guided expectation:

- PARA-style retrieval is usually more token-efficient than deep verbatim retrieval.
- Deep verbatim retrieval is usually more accurate for exact historical recall.

## File Model

Each entity lives under a PARA folder and has:

1. `summary.md` for quick load
2. `items.yaml` for atomic durable facts

Daily notes keep the timeline. Tacit memory stores user operating patterns.

## Operations

### Remember

- Add durable facts to `items.yaml`.
- Keep facts atomic and deduplicated.
- If a fact changes, mark old one as superseded; do not delete history.

### Recall

- Load `summary.md` first.
- Load matching `items.yaml` facts only when needed.
- Keep responses concise and specific.

### Synthesize

- Weekly: rewrite `summary.md` from active facts.
- Prioritize hot/warm facts using recency and access frequency.
- Keep cold facts in `items.yaml` for on-demand retrieval.

## Routing with MemPalace

PARA and MemPalace are complementary:

- Use PARA for quick context, preferences, defaults, and active state.
- Use MemPalace for exact quote/timeline/provenance questions.

### Default Router

1. Start in PARA.
2. If answer lacks evidence (date/source/clear attribution), escalate to MemPalace.
3. After MemPalace resolves facts, write back compact updates to PARA.

### Use PARA Only When

- Request is routine and current-state oriented.
- A concise answer is enough.
- No need for exact wording from old sessions.

### Use Both When

- User asks for recommendations that depend on long history.
- Prior decisions may conflict.
- You need high accuracy and low token overhead.

## Guardrails

- Never store secrets or credentials.
- If facts conflict, show both and ask for resolution.
- Keep write operations explicit and auditable.
