---
name: context-os-basics
description: Foundation patterns for building context operating systems
model: inherit
---

# Context OS Basics

## What is a Context OS?

A context operating system is a structured knowledge system where:
- AI compounds intelligence over time (never re-teach)
- Knowledge persists across sessions
- Concepts link to each other (graph, not files)
- Two layers separate reusable knowledge from operational docs

## The Two-Layer Architecture

### Layer 1: Atomic Knowledge Graph (`knowledge_base/`)

Individual reusable concepts:
- Technical knowledge
- Business insights
- Methodologies and patterns

Each node:
- Has structured frontmatter (metadata)
- Links to related concepts via `[[wiki-links]]`
- Follows lifecycle: **emergent** → **validated** (typically 2+ citations) → **canonical**

### Layer 2: Operational Documents (`00_foundation/`)

Strategic artifacts that COMPOSE Layer 1:
- Positioning documents
- Messaging frameworks
- Process documentation

Key principle: Operational docs **reference** atomic concepts; they do not redefine them.

## Tags and structure (emergent, not ceremony)

**Do not** maintain separate governance files (`taxonomy.yaml`, `ontology.yaml`) unless you have a proven need — agents rarely read them. Instead:

- Reuse **tags and domains** that already appear in your graph.
- Add new tags only after **3+ nodes** demonstrate a pattern.
- Prefer **wiki-links** and short frontmatter over heavy ontology rules.

## Evidence-Based Attribution

Every claim needs a source:

- `[VERIFIED: file:line]` — Direct evidence
- `[INFERRED: logic]` — Deduced from evidence
- `[UNVERIFIABLE]` — Cannot confirm (be honest)

Quality standard: If you cannot cite a source, do not claim it.

## The SENSE → ORIENT → ACT → DEPOSIT Loop

1. **SENSE** — Check what exists (`context-os graph health`, heat from sessions)
2. **ORIENT** — Find hub nodes, read coordination surfaces
3. **ACT** — Create or update content
4. **DEPOSIT** — Link to existing nodes; reinforce the graph through use

## Key Anti-Patterns

### 1. One Continuous Thread
**Problem:** Single long conversation without writing to files  
**Fix:** Write intermediate results to files, preserve attribution chains

### 2. Context Explosion
**Problem:** "Need to read all files to answer this"  
**Fix:** Use synthesis docs in `00_foundation/` that point into the graph

### 3. Vague Attribution
**Problem:** "Many customers want this" (no source)  
**Fix:** Quantify: "14 of 166 (8.4%)" not "many"

## The 3–5 Sample Rule

Never automate without sampling first:
1. Run broad search
2. Sample 3–5 results with context
3. Validate patterns are accurate
4. Refine and scale

## Advanced Patterns (Not Covered Here)

For complex implementations:
- Chief of Staff orchestration
- Forcing functions and calibration
- Team governance patterns
- Multi-agent coordination

Learn more: https://taste.systems
