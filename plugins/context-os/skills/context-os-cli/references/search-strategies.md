# Search strategies (context-os CLI)

Use these when orientation needs more than one command. All examples use **`context-os`** as shipped today (`graph`, `sessions`, `heat`, `ingest`, `audit`, `cc-lens`).

---

## Strategy 1 — Breadth then depth

**When:** “What’s active lately?” or onboarding to a repo.

1. Sweep activity:

   ```bash
   context-os heat --days 30 --path-contains "YOUR_ROOT" --format json --limit 40
   ```

2. Pick a cluster from paths (e.g. `knowledge_base/technical/`).

3. Graph health for structure:

   ```bash
   context-os graph health --graph knowledge_base --format json
   ```

4. Drill into one node:

   ```bash
   context-os graph query --graph knowledge_base "keyword"
   context-os graph show --graph knowledge_base node-name
   ```

---

## Strategy 2 — Anchor file

**When:** You have one important file and want related work.

1. Heat around its directory:

   ```bash
   context-os heat --days 14 --path-contains "path/fragment" --format json
   ```

2. Sessions that touched that path:

   ```bash
   context-os sessions list --path-contains "path/fragment"
   ```

3. Replay an interesting session:

   ```bash
   context-os sessions replay <session_id>
   ```

---

## Strategy 3 — Time bracketing

**When:** “What did I touch this week?” (approximate via heat window + session list.)

1. Short window heat:

   ```bash
   context-os heat --days 7 --path-contains "project" --format json
   ```

2. Sessions since a date (if your build supports `--since`):

   ```bash
   context-os sessions list --since "2026-04-01" --path-contains "project"
   ```

3. Replay sessions that stand out.

---

## Strategy 4 — Token / waste (cc-lens)

**When:** Optimizing cost, tool noise, or cache behavior.

1. Run analysis (API must be up; set `CC_LENS_BASE_URL` if needed):

   ```bash
   export CC_LENS_BASE_URL=http://localhost:3001
   context-os cc-lens analyze
   ```

2. Inspect `/tmp/cc-lens-spec.json` or run **`/cc-lens`** in Claude Code for actionable remediation.

---

**Last updated:** 2026-04-19  
(Replaced legacy `tastematter query flex` / `co-access` examples — not present in current `context-os`.)
