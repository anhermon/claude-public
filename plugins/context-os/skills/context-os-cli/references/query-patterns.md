# Query patterns (context-os CLI)

Patterns below use **`context-os`** only. Pair with **Grep** / **Glob** for full-text or filename search outside the graph.

---

## Intent → commands

| Intent | Start here | Then |
|--------|------------|------|
| Graph structure (orphans, hubs) | `graph health --format json` | `graph show` on a name |
| Find nodes by keyword in graph | `graph query <term>` | `graph show <name>` |
| Busy files in a repo path | `heat --path-contains --days` | Read top paths |
| Recent sessions touching a path | `sessions list --path-contains` | `sessions replay <id>` |
| Bring raw content into graph | `ingest file` / `ingest session` | `graph health` again |

---

## Path substring patterns

When exact paths are unknown, filter with `--path-contains`:

| Looking for | Example |
|-------------|---------|
| One client or product | `--path-contains "pixee"` |
| Knowledge base only | `--path-contains "knowledge_base"` |
| Language | `--path-contains ".py"` or `"src/ts"` |

---

## Interpreting results

### Heat (`context-os heat`)

- High activity in the window → prioritize **Read** on those paths.
- Low activity on a file you “care about” in docs → possible orphan or stale doc (cross-check with `graph health`).

### Sessions (`sessions list`)

- Many sessions hitting the same path → sustained work or repeated reopening.
- Use `sessions replay` to reconstruct tool/file sequence for a specific session id.

### Graph (`graph health`, `graph query`, `graph show`)

- **health** — counts and structural issues (orphans, staleness flags depending on build).
- **query** — search term inside the indexed graph.
- **show** — one node by name (filename stem without `.md` if that is how your graph names nodes).

---

## Example workflow: “What’s hot in my knowledge base?”

```bash
context-os heat --days 14 --path-contains "knowledge_base" --format json --limit 20
```

Pick the top paths, then **Read** them and **Grep** for concepts you care about.

---

**Last updated:** 2026-04-19
