# token-efficiency

Industry-standard knowledge base for LLM token efficiency, grounded in Anthropic documentation, academic research (2024–2025), and production engineering patterns. Covers the full optimization stack: context window cost model, waste taxonomy, caching architecture, prompt engineering guidelines, and an optimization playbook ranked by ROI.

## What this provides

- **Context window cost model** — how tokens accumulate per turn, input:output ratios in agentic coding (~20–25:1), and the math behind multi-turn session costs
- **Waste taxonomy (9 categories)** — tool hammering, context bloat, cache inefficiency, CLAUDE.md over-specification, MCP schema overhead, instruction duplication, large file reads, unmanaged conversation history, and system prompt re-injection
- **Caching architecture** — prompt cache mechanics, cache-friendly vs cache-hostile patterns, and how to maximize cache hit rates
- **Prompt engineering guidelines** — structural rules for CLAUDE.md, tool schema hygiene, and instruction deduplication
- **Optimization playbook** — concrete actions ranked by ROI, from quick wins (truncate tool results, deduplicate instructions) to architectural changes (cache-aware turn structure, selective tool loading)

## Operations

- **DIAGNOSE** — classify the dominant waste category in a session or project based on observed patterns
- **RECOMMEND** — generate ranked, actionable optimization steps for a given waste profile
- **AUDIT** — review a CLAUDE.md or system prompt for inefficiencies: over-specification, duplication, cache-hostile ordering
- **BENCHMARK** — define baseline metrics and thresholds for tracking improvement over time

## Trigger phrases

- "why is this expensive?"
- "optimize token usage"
- "context bloat"
- "cache hit rate"
- "CLAUDE.md too large"
- "tool hammering"
- "reduce session cost"
- "token waste analysis"
- "how to reduce [cost|tokens]"

Also loaded automatically by `/cc-lens` when generating recommendations.
