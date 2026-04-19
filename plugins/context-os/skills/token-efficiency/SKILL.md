---
name: token-efficiency
description: >
  Industry-standard knowledge base for token efficiency optimization in LLM agent harness
  engineering. Covers context window cost model, tool use patterns, waste taxonomy, caching
  architecture, prompt engineering, and actionable optimization playbook.

  Trigger on: "why is this expensive?", "optimize token usage", "context bloat", "cache hit rate",
  "CLAUDE.md too large", "MCP overhead", "tool hammering", "reduce session cost",
  "session forensics", "token waste analysis", "agent loop efficiency",
  "how to reduce [cost|tokens]", called automatically by /cc-lens for recommendation generation.
license: private
compatibility: claude-sonnet-4-5+
metadata:
  sources: [anthropic-docs, academic-papers, industry-blogs]
  last_updated: 2026-04-18
  operations: [DIAGNOSE, RECOMMEND, AUDIT, BENCHMARK]
---

# Token Efficiency Engineering

Industry knowledge base for token efficiency in LLM agent systems, grounded in Anthropic
documentation, academic research (2024–2025), and production engineering patterns.

---

## Context Window Cost Model

### How tokens accumulate per turn

Every agentic turn has this structure:
```
Turn_N_tokens = System_Prompt + Tool_Schemas + Conversation_History + User_Query + Tool_Results + Reasoning
```

**Growth per turn (measured):**
- Simple tool-calling agents: +2,000–5,000 tokens/turn
- Complex multi-tool agents: +5,000–20,000 tokens/turn
- Input:output ratio in agentic coding: **20–25:1** — the input bill dominates

**Critical math:**
- System prompt 2,000 tokens × 200 turns = 400,000 tokens just for the repeated prompt
- Tool schemas 10,000 tokens × 50 calls = 500,000 tokens for schema injection
- A 50-turn coding session: ~1M input tokens total, ~40K output

### Context pollution patterns (what contaminates the window)

| Pattern | Typical Cost | Detection | Threshold |
|---------|-------------|-----------|-----------|
| Tool results not truncated | 60–80% of agent tokens | result > 4K chars | > 8,000 chars = truncate |
| MCP server schemas | 15,000–20,000 tokens/msg | tool schemas > 30% of context | > 5K tokens for schemas |
| Conversation history unmanaged | +5K/turn after turn 15 | history > 40% of context | > 40% = prune |
| Large file reads in context | 5K–100K tokens per file | file read > 500 lines | flag at > 1K lines |
| System prompt re-injected every turn | 10K–40K/session (bug) | same prompt in each turn | architectural fix needed |
| Instruction duplication | 500–2,000 tokens | same rule in 2+ places | dedup savings > 100 tokens |

### The "lost in the middle" effect
LLMs attend strongly to beginning and end of context, weakly to the middle:
- Info at start: ~90% retrieval accuracy
- Info at middle: ~60% accuracy (**−30%**)
- Info at end: ~85% accuracy

Implication: stuffing 100K tokens into context doesn't give uniform access. Middle context is effectively semi-invisible.

### Context rot (Chroma 2025 research)
All 18 frontier models show measurable degradation as input grows:
- 10K tokens: baseline
- 50K tokens: 10–20% accuracy drop
- 100K tokens: 20–50% drop
- 200K tokens: 40–70% drop

**Signal:** model starts forgetting earlier instructions, error rate increases, coherence drops.

---

## Tool Use Cost Patterns

### Exact cost per tool call
```
Total = 346 (system overhead) + schemas (150–500/tool) + invocation (50–200) + result (500–10K) + reasoning (2K–5K)
Example: ~3,646 tokens for a single moderately-sized tool call
```

### Tool categories ranked by waste potential

| Category | Overhead | Waste Potential | Fix |
|----------|---------|-----------------|-----|
| MCP servers | 3–5K tokens/msg | 90%+ | Load only needed servers |
| Browser/computer use | 10–50K/call | 85%+ | Aggressively truncate DOM |
| Bash with large output | 2–20K/call | 80%+ | Set max_chars=8000 |
| API/search calls | 1–3K/call | 50%+ | Truncate at 4K chars, batch |
| File operations | 1–5K/call | 60%+ | Set file size limits |
| Deterministic tools | 200–500/call | 10–20% | Batch when possible |

### MCP server schema bloat (critical)
- Each MCP server injects its full tool schema on every API call
- Typical: 4 servers × 2–5K each = **10,000–20,000 tokens per message**
- In a 50-call session: 500K–1M tokens just for schemas

**Fixes:**
- Cloudflare Code Mode: reduced schema from 1.17M → 1K tokens (99.9% reduction)
- Dynamic toolsets: load only tools needed for current task
- `RAG-MCP`: retrieval-based tool selection (arXiv 2025)
- Explicitly list only tools relevant to the agent role

### Batching vs sequential calls
```
Sequential 5 calls:  5 × 3,646 = 18,230 tokens
One batched call:    346 + 200 + 100 + 2,000 + 2,000 = 4,646 tokens
Savings: 75%
```
Design tools to accept arrays: `get_users(ids: list)` not `get_user(id: str)`.

### Tool result truncation guidelines
- Default truncation: 8,000 characters (~2K tokens)
- Line limit: 2,000 lines
- Preserve beginning AND end (not just middle)
- Append: `[Output truncated: N chars omitted]`
- Tool result > 8K chars repeatedly = redesign the tool, add filtering params

---

## Waste Category Taxonomy

### Canonical waste categories (industry standard)

**1. Context Bloat**
Large total context relative to useful output; long sessions without compaction.
- Detection: cache_creation + input > 500K AND output/context < 5%
- Red flag: session > 60 min with no compaction boundary
- Impact: 20–50% wasted tokens
- Fix: `/compact` periodically, break sessions, prune CLAUDE.md

**2. Context Churn**
Same content added/removed repeatedly without retaining value.
- Detection: same tool called 3+ times with identical params; same file read multiple times
- Red flag: revisiting same code section 3+ times
- Impact: 10–30% waste
- Fix: cache tool results within session, track completed sub-tasks

**3. Context Pollution**
Irrelevant, redundant, or conflicting content in context window.
- Detection: tool result >> useful data; search returns sprawling payloads
- Red flag: tool results > 8K chars consistently
- Impact: 15–40% waste
- Fix: truncation, improved search relevance, filter results pre-injection

**4. Tool Overhead Waste**
Schema re-injection cost exceeds actual tool utility.
- Detection: tool schemas > 20% of context; tools called < 2× per session
- Red flag: MCP servers with 50+ tools all loaded
- Impact: 20–60% of agent call cost
- Fix: dynamic tool loading, schema dedup, disable unused servers

**5. Retry & Failure Amplification**
Failed calls trigger cascading retries with full context re-read.
- Detection: same tool called 3+ times in succession; token spike after error
- Red flag: multi-agent feedback loops (A asks B, B asks A)
- Impact: 5–10× multiplier on single operation cost
- Real incident: $127/week → $47,000/week from undetected loop
- Fix: circuit breaker, max 3 retries, exponential backoff, dead-letter queue

**6. Observation Bloat**
Tool outputs carry verbose headers, footers, boilerplate past the point of utility.
- Detection: tool result > 4K chars; includes test names, line numbers, syntax highlighting
- Impact: 35–80% of agent trajectory tokens
- Fix: observation masking (mask results > 3 turns old), result post-processing

**7. System Prompt Redundancy**
Same instructions appear in multiple locations.
- Detection: same "always/never" rule in system prompt AND tool description AND examples
- Impact: 10–30% bloat
- Fix: consolidate to system prompt only

**8. Cold-Start Overhead (Subagent Waste)**
Subagent spawning re-injects full context; overhead exceeds actual work.
- Detection: subagent costs > 20K tokens but does < 10K tokens of work
- Break-even: subagent only worthwhile if actual work > 10K tokens
- N parallel subagents = N × context cost multiplication
- Fix: consolidate into single agent unless work > break-even threshold

**9. Cache Miss Cascades**
Cache TTL expires just before next use, forcing expensive re-writes.
- Detection: cache hit rate < 30%; alternating hit/miss pattern
- Impact: 20–40% cost inflation
- Fix: extend TTL to 1-hour for shared content, batch calls to stay warm

---

## Caching Architecture

### Cache TTL decision tree
```
Use 5-minute (ephemeral):
  - Single user, single session
  - Content changes frequently
  - Development/testing

Use 1-hour (persistent):
  - Shared system prompt across users
  - Content used every 5+ minutes
  - Production multi-user platforms
  - Cache write cost: 2× base; read cost: 0.1× base
  - Cost payoff: positive after 2nd read
```

### Cache hit rate benchmarks
- Poor: < 30%
- Fair: 30–60%
- Good: 60–80% (target for well-optimized agentic system)
- Excellent: 80%+ (production with 1-hour persistent cache)

**Measured rates:** Explicit breakpoint caching achieves up to 84% hit rate.
**Minimum checkpoint:** 1,024 tokens per cache checkpoint (Anthropic requirement).

### Cache reuse ratio (cc-lens metric)
`cache_reuse_ratio = cache_read_tokens / cache_creation_tokens`
- Real-world distribution (from 748 sessions): median=16×, p10=6×, p25=9×
- **Below p10 (<6×):** poor reuse — context created but rarely revisited
- **Below p25 (<9×):** below average
- **Above median (>16×):** healthy reuse

---

## Prompt Engineering for Efficiency

### CLAUDE.md sizing guidelines
```
Optimal: < 200 lines / < 1,500 tokens
Good: 200–350 lines / 1,500–2,500 tokens
Wasteful: > 350 lines / > 2,500 tokens

Include: current task state, critical patterns, non-obvious conventions
Exclude: aspirational goals, verbose explanations, generic guidance (Claude knows it)
```
**Impact:** Teams reduced session tokens by 40% keeping CLAUDE.md under 200 lines.
**Math:** 2,000-token CLAUDE.md × 200 sessions = 400K tokens/month in overhead.

### Memory file patterns
- Read per turn: 500-token memory × 30 reads in session = 15K tokens of overhead
- Update sparingly: consolidate updates every 5 turns, not every turn
- Keep surgical: current state + last 3 decisions + next steps only

### Instruction deduplication
1. Extract all "Always/Never/Make sure" rules from system prompt
2. Cross-reference against tool descriptions, examples, feedback templates
3. Consolidate duplicates to system prompt only
4. Savings: 10–30% reduction in system prompt tokens

### Skill/hook overhead
- Skills load full SKILL.md content on first invocation (500–1,500 tokens)
- 2nd+ invocations amortized to ~2–3 tokens
- Break-even: paid back by 2nd use in same session
- 63 installed skills → only ~21 visible (system prompt capacity limit)

---

## Agent Loop Patterns

### Subagent spawning cost
```
Cold-start overhead per spawn:
  System prompt re-tokenization: 300–500 tokens
  CLAUDE.md reload: 100–300 tokens
  Tool schemas re-injected: 2,000–5,000 tokens
  Total cold-start: 2,400–5,800 tokens per spawn

Break-even: subagent work > 10,000 input tokens to be worthwhile
```

### Parallel vs sequential tradeoffs

| Pattern | Token Cost | Latency | Use When |
|---------|-----------|---------|----------|
| Single agent | 1× | 1× | Well-scoped tasks |
| Sequential subagents | 2–3× | 2–3× | Strict dependencies |
| Parallel (2–3) | 2–4× | 1–1.5× | Independent tasks, time-sensitive |
| Parallel (4+) | 4–8× | 1.5× | Only if latency critical |

**Danger:** Nested spawning 3 levels deep = combinatorial explosion. Production incident: agent ran for 11 days recursively.

### Task tracking (TodoWrite) cost
- 10-item task list, read every turn for 20 turns = 100K tokens of task overhead
- Optimization: only read task list when status changes are needed

### Retry amplification
- Multi-agent loop: amplification up to 17.2×
- Real incident: $127/week → $47,000/week in one week
- Safeguards: max 3 retries, circuit breaker, dead-letter queue, spawn depth limit = 2

---

## Optimization Playbook (Ranked by ROI)

### Tier 1: High ROI, Low Effort (do first)

**1. Enable prompt caching (1-hour TTL)**
- Effort: 30 min
- Savings: 50–70% on repeated content
- ROI: 200× per hour

**2. Implement tool result truncation**
- Effort: 1 hour
- Savings: 20–40% (observation bloat)
- Action: `max_chars=8000` on all tool outputs

**3. Audit & consolidate system prompt / CLAUDE.md**
- Effort: 2 hours
- Savings: 10–30%
- Action: find duplicate instructions, dedup, keep under 200 lines

**4. Disable unused MCP servers and skills**
- Effort: 30 min
- Savings: 5–15%
- Action: audit installed plugins, disable >80% unused

### Tier 2: Medium ROI, Medium Effort

**5. Implement observation masking**
- Effort: 4 hours
- Savings: 35–50% on observation tokens
- Action: mask observations > 3 turns old

**6. Implement tool batching**
- Effort: 2–4 hours per tool set
- Savings: 70–80% on multi-item operations
- Action: redesign tools to accept arrays

**7. Cache-aware session flow**
- Effort: 3 hours
- Savings: 10–20%
- Action: pin system prompt to 1-hour cache, keep warm (access every 4 min)

### Tier 3: High ROI, High Effort

**8. Context compaction (semantic summarization)**
- Effort: 6–8 hours
- Savings: 20–30% history compression
- Action: summarize every 10 turns; replace raw history with summary

**9. Multi-agent architecture (only if justified)**
- Effort: 8–16 hours
- Pre-req: single agent has > 50% waste
- Warning: can increase costs 2–4× if not designed carefully

---

## Benchmarks & Baselines

### What "good" looks like

**Cache hit rate:** Good = 60–80%, Excellent = 80%+

**Tokens per session by task type:**

| Task | Poor | Good | Excellent |
|------|------|------|-----------|
| Simple code review | > 150K | 50–100K | < 50K |
| Bug fix (1 file) | > 250K | 75–150K | < 75K |
| Feature implementation | > 500K | 150–300K | < 150K |
| Multi-file refactor | > 1M | 300–600K | < 300K |

**Tokens per turn:** Good < 15K/turn, Excellent < 10K/turn

**System prompt:** Good < 1,500 tokens, Excellent < 800 tokens

**Cost per productive task:** Coding $0.50–2.00 (good: < $0.50)

---

## Session Forensics Signals

### Metric → waste category mapping

| Metric | Threshold | Waste Category |
|--------|-----------|----------------|
| `cache_reuse_ratio` < 6× | Bottom 10th percentile | Cache Inefficiency + Context Bloat |
| `max_single_tool` > p95 (143×) | Top 5% | Tool Hammering |
| `max_single_tool` > p75 (54×) | Top 25% | Tool Hammering (moderate) |
| `duration_minutes` > 45 AND no compaction | — | Compaction Absence |
| `user_interruptions` > 5 | — | Interruption Loops |
| `has_thinking` AND low output/turn | output_per_turn < 50 | Thinking Waste |
| `cache_creation` > p75 AND low reuse | cache_creation > 404K AND ratio < 9 | Context Bloat |
| multiple sessions same project within 30 min | ≥ 3 concurrent | Parallel Sprawl |

---

## Operation: DIAGNOSE

**Triggered by:** "why is session X expensive?", "what's wasteful about this session?"

### Steps
1. Load session metadata (from cc-lens spec or API)
2. Compute all waste metrics against dataset percentiles
3. For each waste category with score > 30:
   - State the specific finding with numbers: "Bash called 316× — dataset p95 is 143, you are in top 2%"
   - Explain WHY this is wasteful (token cost model from this skill)
   - Give a concrete, actionable fix from the optimization playbook

---

## Operation: RECOMMEND

**Triggered by:** "how do I reduce token usage?", "optimize my sessions"

### Steps
1. Identify which waste categories score highest across the user's projects
2. Map each to the optimization playbook tier
3. Rank recommendations by estimated ROI for this user's specific patterns
4. For each recommendation:
   - Estimated current cost impact ($)
   - Implementation time
   - Concrete steps (not vague "be more efficient")

---

## Operation: AUDIT

**Triggered by:** "audit my CLAUDE.md", "check my system prompt", "review my skills"

### Steps
1. Read CLAUDE.md and count tokens
2. Identify duplicate instructions across CLAUDE.md, memory files, tool descriptions
3. Flag instructions that are generic (Claude already knows these)
4. Estimate savings from consolidation
5. Output specific lines to remove/consolidate

---

## Operation: BENCHMARK

**Triggered by:** "how do my sessions compare?", "is my cache hit rate good?"

### Steps
1. Pull user's actual metrics from cc-lens spec
2. Compare against the benchmarks table in this skill
3. Report percentile rank for each metric
4. Highlight which metrics are outliers (good or bad)
