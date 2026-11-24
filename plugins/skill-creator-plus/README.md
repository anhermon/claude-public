# skill-creator-plus

Anthropic's `skill-creator` skill (create, improve and evaluate skills) packaged as a plugin, plus a repeatable way to keep it in sync with the version claude.ai ships. Local extensions live on top of the pristine upstream copy.

The skill keeps its upstream name, `skill-creator`. This plugin is named `skill-creator-plus` to avoid colliding with the official `skill-creator` plugin.

## Install

```bash
claude plugin marketplace add https://github.com/anhermon/claude-public
claude plugin install skill-creator-plus@claude-public
```

## NOTICE

The skill in this plugin is derived from Anthropic's `skill-creator`, licensed under the Apache License 2.0 (see `skills/skill-creator/LICENSE.txt`). Copyright Anthropic. `upstream/skill-creator/` is an unmodified copy. `skills/skill-creator/` is modified by this repo's maintainer: local changes are applied on top of upstream and merged with each resync.

## Why the claude.ai copy is the source

The public GitHub copy (`anthropics/skills`, `skills/skill-creator`) is frozen at an older version (March 2026). The copy that claude.ai ships is newer, so that is the source of truth.

claude.ai account skills sync into `~/.claude/skills/synced/<id>/skill-creator`. If you have no synced copy, pass any directory that contains a `SKILL.md` as the source.

## Layout

| Path | Purpose |
|---|---|
| `upstream/skill-creator/` | Pristine, byte-exact copy of the source. Never hand-edited. |
| `upstream/UPSTREAM.md` | Source path, sync date, sha256 manifest. Rewritten by the sync script. |
| `skills/skill-creator/` | The shipped skill. Upstream plus local changes. |
| `scripts/sync-upstream.sh` | Resync tool. |
| `skills/skill-creator/scripts/stage_timing.py` | Local addition: per-stage timing and waterfall chart (not in upstream). |
| `tests/` | Tests for the sync script and for stage timing. |

## Local extension: stage timing

Evals measure duration per stage as well as pass rate, and the improve loop uses both (score first, duration second).

1. The skill's stages are listed once per iteration in `iteration-N/stages.json`.
2. Timing is read from each executor's transcript (timestamps on every line). The executor declares its stage for free with a `# stage: <name>` first line in a Bash command, or a `stage: <name>` text line before other tools; only names from `stages.json` (plus `other`) are allowed, and any other name is still shown, flagged. Model time and tool time are split per stage, and stages + startup + handback + unattributed reconcile with the transcript's wall time. `timing.json` carries `agent_id` / `transcript_path`. Without a transcript (claude.ai) `<run>/stages.jsonl` shell marks are the fallback and the chart says so. Missing input is reported as gaps, never as errors.
3. `python -m scripts.aggregate_benchmark <iteration-dir>` (or `python -m scripts.stage_timing <iteration-dir>` alone, run from `skills/skill-creator/`) writes `stage_timing.json` per run and per iteration, a stage table in `benchmark.md`, and `waterfall.svg`.
4. The viewer's Benchmark tab shows the waterfall: one panel per configuration plus the previous iteration. Without a browser, open `waterfall.svg`.

Edits to upstream files are small inserted sections so `sync-upstream.sh` still merges cleanly; the logic is in the new `stage_timing.py`.

## Rule

Make local changes only in `skills/`. Never edit `upstream/`: the next sync replaces it.

## Resync from upstream

1. Start from a clean working tree, so `git diff` shows only the sync.
2. Preview the delta (writes nothing):

   ```bash
   plugins/skill-creator-plus/scripts/sync-upstream.sh --dry-run [SOURCE_DIR]
   ```

   If the shell reports "permission denied" (exit 126), run it as `bash plugins/skill-creator-plus/scripts/sync-upstream.sh ...` instead.

   Without `SOURCE_DIR` the script uses `~/.claude/skills/synced/*/skill-creator` and fails if there are zero or more than one match.
3. Run it:

   ```bash
   plugins/skill-creator-plus/scripts/sync-upstream.sh [SOURCE_DIR]
   ```

   The script replaces `upstream/skill-creator`, applies the same old-to-new delta to `skills/skill-creator` with a per-file 3-way merge (base: old upstream), and rewrites `upstream/UPSTREAM.md`. It does nothing if upstream is unchanged. It never commits.
4. Review `git diff`, run `python3 -m unittest discover -s plugins/skill-creator-plus/tests -v`, then commit.

## Resolving conflicts

The script exits 1 and lists the affected files when a local change overlaps an upstream change.

- Text files: conflict markers (`<<<<<<< local`, `=======`, `>>>>>>> new-upstream`) are left in `skills/skill-creator/<file>`. Edit the file to the intended result and remove the markers.
- Deleted upstream but modified locally: the local file is kept. Delete it if you no longer want it.
- Modified upstream but deleted locally: the file is not restored. Copy it from `upstream/skill-creator/` if you want it back.
- Added upstream but a different local file already exists: the local file is kept. Merge by hand.

`upstream/` is already updated when conflicts are reported, so a second run is a no-op. Resolve the conflicts by hand.
