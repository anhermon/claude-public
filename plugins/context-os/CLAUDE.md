# Context OS Plugin (unified)

**Purpose:** Help users build a Context OS — a structured knowledge graph where AI compounds intelligence over time — and analyze sessions with bundled tooling.

---

## What This Plugin Does

Guided setup, ingestion, knowledge graph operations, token/session analytics (cc-lens, ccusage), and context audit. Uses **stigmergic** coordination: agents read and modify the shared environment.

### Commands

| Command | Purpose |
|---------|---------|
| `/quickstart` | Guided setup |
| `/ingest` | Raw content → knowledge nodes |
| `/audit` | Graph + token/session audit |
| `/ingest-history` | Sessions → knowledge graph |
| `/cc-lens` | Actionable follow-up after analysis (paste-prompt A1/A2 or per-project remediation with approvals) |

### Skills

| Skill | Purpose |
|-------|---------|
| `context-os-basics` | Two-layer architecture, lifecycle |
| `context-os-cli` | Bundled `context-os` CLI |
| `context-gap-analysis` | Gap analysis |
| `epistemic-context-grounding` | Grounding |
| `cc-lens` | cc-lens dashboard workflows |
| `token-efficiency` | Waste taxonomy & playbook |
| `context-audit` | Unified audit |
| `context-ingest` | AUTO / SOURCE / HISTORICAL ingest |
| `ccusage` | ccusage CLI wrapper |

---

## Quick Start

Run `/quickstart`. Use the **bundled** CLI: install with `uv tool install .` or `pip install -e .` from this plugin root (or `python3 -m context_os`). No external tastematter binary.

---

## Two-Layer Architecture

**Knowledge Graph** (`knowledge_base/`) — atomic concepts, `[[wiki-links]]`, lifecycle emergent → validated → canonical.

**Operational Docs** (`00_foundation/`) — compose from the graph; reference, don’t redefine.

### SENSE → ORIENT → ACT → DEPOSIT

- **SENSE** — `context-os graph health`, `context-os heat`
- **ORIENT** — hubs/orphans from health output
- **ACT** — create/update nodes
- **DEPOSIT** — `[[wiki-links]]`

### Bundled CLI (examples)

```bash
context-os graph health --graph knowledge_base
context-os graph query "topic" --graph knowledge_base
context-os heat --days 14
context-os sessions list --since 7d
context-os audit
context-os cc-lens analyze   # needs npx cc-lens on :3001
```

---

## Templates

| Template | Purpose |
|----------|---------|
| `templates/CLAUDE_MD_STARTER.md` | User project CLAUDE.md starter |
| `templates/node_template.md` | Knowledge node shape |

## Learn More

https://taste.systems
