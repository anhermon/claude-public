---
name: context-os-cli
description: >
  Use when users ask about work context, file activity, knowledge graph health,
  session history, or token/waste analysis. Uses the context-os CLI (graph,
  sessions, heat, ingest, audit, cc-lens, ccusage). Combine with grep/glob/read
  for content. Cite /tmp/cc-lens-spec.json or CLI output paths for verification.
---

# Context OS CLI Skill

The **`context-os`** binary exposes structural queries and analysis. **It does not include** `context`, `query flex`, `graph-exec`, `daemon`, `intel`, or `verify` — those belong to other tooling or older docs.

**Core pairing:** CLI finds *which* paths matter; **Read** / **Grep** find *what* is in them.

---

## Command surface (installed CLI)

| Top-level | Subcommands / usage |
|-----------|---------------------|
| `graph` | `health`, `query <term>`, `show <name>` |
| `sessions` | `list`, `replay <session_id>` |
| `heat` | `--days`, `--path-contains`, `--limit`, `--format json\|table` |
| `ingest` | `session`, `file`, `source` |
| `audit` | `--graph` |
| `cc-lens` | Optional `analyze`; flags `--top-n`, `--sort-by`, `--sessions-per-project`, `--project`, `--session` |
| `ccusage` | Passthrough `rest` |

### `graph`

```bash
context-os graph health [--graph DIR] [--stale-days N] [--format json|text]
context-os graph query [--graph DIR] <term>    # search term in graph
context-os graph show [--graph DIR] <name>     # one node by name
```

### `sessions`

```bash
context-os sessions list [--since SINCE] [--path-contains PATTERN]
context-os sessions replay <session_id>
```

### `heat`

```bash
context-os heat [--days DAYS] [--path-contains PATTERN] [--limit N] [--format json|table]
```

### `ingest`

```bash
context-os ingest session [--graph DIR] [--summary-only] [--file FILE] <session_id>
context-os ingest file [--graph DIR] <path>
context-os ingest source [--graph DIR] <source>
```

### `audit`

```bash
context-os audit [--graph GRAPH]
```

### `cc-lens`

Analysis talks to the cc-lens API (often `http://localhost:3001`; set `CC_LENS_BASE_URL` if needed). Writes **`/tmp/cc-lens-spec.json`** and a report under **`/tmp/`** when using `analyze`.

```bash
export CC_LENS_BASE_URL=http://localhost:3001   # if needed
context-os cc-lens analyze
context-os cc-lens analyze --project <slug>
```

**Actionable follow-up:** Run **`/cc-lens`** in this plugin — paste-prompt for another agent (A1/A2) or per-project remediation with approvals (Mode B).

---

## Recipes (real commands only)

1. **Graph health (orphans, hubs, counts):**  
   `context-os graph health --graph knowledge_base --format json`

2. **Search graph by term:**  
   `context-os graph query --graph knowledge_base "positioning"`

3. **Show one node:**  
   `context-os graph show --graph knowledge_base my-concept`

4. **List recent sessions (filter path):**  
   `context-os sessions list --path-contains "myproject"`

5. **Replay a session:**  
   `context-os sessions replay <session_id>`

6. **File heat in a window:**  
   `context-os heat --days 14 --path-contains "knowledge_base" --format json --limit 30`

7. **Ingest a file into the graph:**  
   `context-os ingest file --graph knowledge_base path/to/node.md`

8. **Token/waste analysis + spec artifact:**  
   `context-os cc-lens analyze` then read `/tmp/cc-lens-spec.json` or use **`/cc-lens`**.

---

## Interactive analysis

- **`/cc-lens`** — Turns cc-lens output into: (A) a copy-paste prompt for another agent, or (B) per-project plans with explicit approval before edits.
- The same *pattern* (analyze → artifact → act) can apply to **`audit`** and **`graph health`** later; cc-lens is the first fully scripted slash command.

---

## Citation / receipts

- For **cc-lens** claims, cite **`/tmp/cc-lens-spec.json`** and relevant `project_slug` / `session_id`.
- For **graph/heat/sessions**, cite the command you ran and key fields from JSON output.

---

## Common mistakes

- **Semantic search:** `graph query <term>` matches content/search in the graph, not arbitrary “concepts” in unrelated paths — pair with **Grep** for full-repo text search.
- **Heat vs content:** `heat` ranks activity; it does not explain *why* a file changed — **Read** the file.
- **Stale docs:** Ignore any external doc that references `context-os query`, `tastematter`, or `graph-exec` unless your installed `context-os --help` lists them.

---

## References

- [heat-metrics-model.md](references/heat-metrics-model.md) — Conceptual interpretation of “heat”-style metrics (use with `heat --format json` fields).
- [query-patterns.md](references/query-patterns.md) — Path patterns and workflows using **this** CLI.
- [search-strategies.md](references/search-strategies.md) — Breadth-first and anchor strategies with `heat`, `sessions`, `graph`.

**Last updated:** 2026-04-19
