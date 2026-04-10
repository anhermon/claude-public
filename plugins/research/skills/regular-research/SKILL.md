---
name: regular-research
description: Regular Claude research — fast structured brief using Claude's knowledge + web search. Best for known/popular topics where AutoResearchClaw's Semantic Scholar won't have better sources.
---

# Regular Claude Research

Fast structured brief from Claude training knowledge + web search. Use this when:
- The topic is well-known and well-indexed on the web
- You need results in minutes, not hours
- Academic paper depth isn't required

Use AutoResearchClaw (`/researchclaw`) instead when: the topic is niche, you need real citations, or you need a full paper with experiments.

---

## Process

Run these steps in order.

### 1. Web Search (if WebSearch available)

Run 3-5 targeted queries covering:
- Current state of the art / latest developments
- Key frameworks, tools, or players
- Benchmark numbers or concrete data points
- Known tradeoffs or controversies

### 2. Synthesize

Combine search results with training knowledge. Flag anything uncertain or potentially stale.

### 3. Output: Structured Technical Brief

Always produce output in this exact format:

```markdown
# Research Brief: [Topic]
*Mode: Regular Claude Research | [date]*

## TL;DR
[2-3 sentence executive summary with the single most actionable takeaway]

## Key Findings
[5-8 bullet points, each with a concrete fact, number, or claim. Cite source inline if from web search.]

## Landscape / Options
[Table or list comparing main options/approaches with tradeoffs. Include concrete metrics where available.]

## Recommendation
[Direct recommendation for the most likely use case. No hedging — state the best option and why.]

## Limitations & Caveats
[What this brief doesn't cover. Where to go deeper. Known gaps in available information.]

## Sources
[List URLs from web search, or note "Claude training knowledge (cutoff Aug 2025)" for parametric claims]
```

---

## Quality Bar

- Every section must have substance — no placeholder text
- Numbers > adjectives ("60-80 tok/s" > "fast")
- When uncertain, say so explicitly rather than hedging quietly
- If web search returned nothing useful, say so and rely on training knowledge with explicit caveat
