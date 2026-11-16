# Changelog

## [Unreleased] - 2026-11-16

### Removed

- Plugins `commit`, `code-review`, `review-agents`, `search`, `memory`, `pm`, `dev-guidelines`, `setup-telemetry`, `image-gen`, `observability`, and the stale root `.plugin` zips. See the README "Removed" table for replacements.

### Changed

- Catalog reduced to `premium-web`, `llm-wiki`, `research`, `agent-repo-search`, `context-os`; every entry has a `category`; README rewritten with a quality bar.
- `context-os` version aligned to 2.2.0 across marketplace.json, plugin.json and README; cc-lens default URL is now a named constant.
- `research` gains a README and plugin.json `version`; personal path and Paperclip references removed.
- `agent-repo-search` pins `rendergit` to a commit SHA instead of fetching `main`.
- marketplace.json description made accurate.

### Added

- **skill-creator-plus 0.3.0**: stage timing now comes from the executor's transcript, so the waterfall shows where wall time really goes. Model time (thinking and writing tool input) and tool time are split per stage and shown as stacked bars with output tokens; startup, handback and unattributed time are explicit and reconcile with the transcript's wall time (checked in code). Executors declare stages for free with a `# stage: <name>` first line in a Bash command (or a `stage: <name>` text line before other tools) instead of running `python3 -c` marks, which added about 3s each and ignored model time. `timing.json` records `agent_id` / `transcript_path`; `stages.jsonl` remains a fallback labelled "shell-only marks: model time not attributed".
- `scripts/validate.sh`: validates the marketplace and all plugins.
- **skill-creator-plus 0.2.0**: Anthropic's `skill-creator` skill (claude.ai-synced copy) as a pristine `upstream/` copy plus a locally extensible `skills/` copy, resynced with `scripts/sync-upstream.sh`. Evals measure duration per stage of the tested skill: `iteration-N/stages.json`, per-run `stages.jsonl` marks, `scripts/stage_timing.py`, a stage table in the benchmark, a waterfall chart in the viewer (with the previous iteration) and a standalone `waterfall.svg`. The improve loop and analyzer use stage timings, score first, duration second. Apache-2.0, credited to Anthropic.

## [0.2.3] — 2026-04-07

### Fixed

- **Claude Desktop marketplace validation** — each catalog entry now includes a top-level `author` object. The desktop app’s `listAvailablePlugins` check requires this field; missing it can surface as an empty “No plugins available.” list.
- Removed the `$schema` URL from `marketplace.json` (that URL currently 404s; some clients treat an invalid schema pointer as a hard validation failure).

## [0.2.2] — 2026-04-07

### Fixed

- **Marketplace catalog empty in UI** — plugin entries now use `git-subdir` sources pointing at `plugins/<name>/` in this repo. Relative paths only resolve when the marketplace is added as a full Git checkout; URL-only installs only fetch `marketplace.json`, so listings showed no plugins.

## [0.2.1] — 2026-04-07

### Added

- **Claude Code marketplace** — [`.claude-plugin/marketplace.json`](./.claude-plugin/marketplace.json) so the repository URL `https://github.com/anhermon/claude-public` registers as a marketplace (lists `commit`, `code-review`, and `image-gen`).

### Changed

- Canonical plugin sources live under [`plugins/<name>/`](./plugins/); root `<name>.plugin` zips are generated from those trees. Removed the duplicate top-level `skills/` copy and the old root-only `.claude-plugin/plugin.json` (which only described `image-gen`).

## [0.2.0] — 2026-04-04

### Added — image-gen plugin

- **Prompt Engineering Engine** — detects image type (`app-icon`, `logo`, `avatar`, `character`,
  `scene`, `product`, `photo`, `illustration`) and builds rich, model-specific prompts
  automatically from brief descriptions
- **Higgsfield Nano Banana Pro browser path** — navigates higgsfield.ai, selects the model,
  submits prompt, waits for generation, downloads result
- **Google Gemini browser path** — fallback when no API keys and/or Higgsfield login unavailable;
  navigates gemini.google.com, submits engineered prompt, downloads result
- **API provider support** — fal.ai (FLUX schnell), Together AI (FLUX Free), Replicate,
  OpenAI DALL-E 3, Stability AI Core; auto-detected from `.env`
- **Provider memory** — caches detected providers so detection only runs once
- **Smart path selection** — checks explicit model mention in prompt → API keys → browser
  (Higgsfield first, Gemini fallback)

### Model-specific prompt modifiers

- **Nano Banana Pro** — reframes icon/logo requests as stylized product renders
  (cinematic model, not flat-design native)
- **Gemini** — keeps prompts clear and conceptual; handles flat design well
- **FLUX / DALL-E / Stability** — appended quality boosters per provider

### Tested

- Anvil app icon (`app-icon` type) via Gemini: charcoal + iron-grey + ember orange,
  3D metallic depth, forge-heat glow line across top face ✓
