# Changelog

## [Unreleased] - 2026-11-16

### Removed

- Plugins `commit`, `code-review`, `review-agents`, `search`, `memory`, `pm`, `dev-guidelines`, `setup-telemetry`, `image-gen`, `observability`, and the stale root `.plugin` zips. See the README "Removed" table for replacements.

### Changed

- **premium-web 2.0.0 — now a Claude Code mod.** The skill builds several materially different candidates (default 3, `candidateCount` setting 1-6, or a number in the request) in parallel, runs one critic pass on each, and presents them in a new "Premium candidates" pane (`/candidates`, or the `premium_web_present_candidates` tool). The user browses, opens each candidate in the browser, picks one or sends feedback; the choice is written to `.premium-web/decision.json` and sent back to Claude, which then finishes only the winner through the full critic loop. A chat fallback covers Claude Code < 2.1.287, disabled mods and non-interactive runs.
- Catalog reduced to `premium-web`, `llm-wiki`, `research`, `agent-repo-search`, `context-os`; every entry has a `category`; README rewritten with a quality bar.
- `context-os` version aligned to 2.2.0 across marketplace.json, plugin.json and README; cc-lens default URL is now a named constant.
- `research` gains a README and plugin.json `version`; personal path and Paperclip references removed.
- `agent-repo-search` pins `rendergit` to a commit SHA instead of fetching `main`.
- marketplace.json description made accurate.

### Added

- premium-web: `hooks/` (mod: `register.ts`, `lib.ts`), `tests/` (`claude plugin test`), `skills/premium-web/references/candidates.md`.
- **skill-creator-plus 0.3.0**: stage timing now comes from the executor's transcript, so the waterfall shows where wall time really goes. Model time (thinking and writing tool input) and tool time are split per stage and shown as stacked bars with output tokens; startup, handback and unattributed time are explicit and reconcile with the transcript's wall time (checked in code). Executors declare stages for free with a `# stage: <name>` first line in a Bash command (or a `stage: <name>` text line before other tools) instead of running `python3 -c` marks, which added about 3s each and ignored model time. `timing.json` records `agent_id` / `transcript_path`; `stages.jsonl` remains a fallback labelled "shell-only marks: model time not attributed".
- `scripts/validate.sh`: validates the marketplace and all plugins.
- **skill-creator-plus 0.2.0**: Anthropic's `skill-creator` skill (claude.ai-synced copy) as a pristine `upstream/` copy plus a locally extensible `skills/` copy, resynced with `scripts/sync-upstream.sh`. Evals measure duration per stage of the tested skill: `iteration-N/stages.json`, per-run `stages.jsonl` marks, `scripts/stage_timing.py`, a stage table in the benchmark, a waterfall chart in the viewer (with the previous iteration) and a standalone `waterfall.svg`. The improve loop and analyzer use stage timings, score first, duration second. Apache-2.0, credited to Anthropic.

### Security

- premium-web mod is unsandboxed. It reads/writes only `.premium-web/` in the project, serves candidate folders on 127.0.0.1 via `python3 -m http.server`, and makes no other network calls. See the plugin README.

## [premium-web 2.1.0] — 2026-10-06

### Added

- **Step 0: use-case classification.** READ (marketing), WORK (`app`) or MIXED (split into two scoped deliverables), written with evidence to NOTES.md; `scripts/classify.py` makes `chrome-shot.mjs` and `critic.py` refuse to run without it (exit 4). The skill description and triggers now cover dashboards, admin, internal tools and consoles and say marketing mode is wrong for them.
- **App mode** (`--mode app`, `tool` kept as an alias): success is task speed and clarity. Primary tasks and walk-through step counts, structure rules, a "signature clarity" idea in place of the wow, a `tells.js` app profile (adds `density`, `interactive_affordance`, `state_coverage`, `page_shaped_mismatch`; `type_scale`, `wow_visible`, `scale_change`, `panel_run` are not hard fails; `data-wow` is a violation) and a per-screen/per-flow critic rubric. New: `references/app-mode.md`, `rubric-app.md`, `app-exemplars.md` (measured; unmeasurable products listed as not measured), three gallery anchors, `assets/skeleton/app-shell.html`.
- Candidates in app mode are working prototypes; `candidates.json` gains `tasks` (`{task, steps, result, screenshot?}`) and `mode`, shown in the pane and chat fallback.

### Changed

- Faces reconciled in one table in `references/styles.md`; `tokens-tool.css` is now `tokens-app.css`. Marketing-mode thresholds and verdicts are unchanged (regression before/after identical).

## [premium-web 1.1.0] — 2026-10-05

### Added

- **Tool mode** — premium-web now covers application and tool UIs (dashboards, admin screens, run/trace views): the wow is the product's own data object drawn at scale (>= 50% x 40% of the viewport, >= 12 records), one display numeral (>= 4vw) and one edge-to-edge scale change. Gates: `MODE=tool` for `tells.js` (via `chrome-shot.mjs`) and `MODE=tool` / `--mode tool` for `critic.py`. Marketing-mode thresholds are unchanged.
- Measured tool-UI exemplars (`references/tool-ui-exemplars.md`) and six tool-UI gallery anchors; `scripts/test_tells.js` offline self-check.
- A gate that cannot run is reported `UNVERIFIED`, never pass; the skill states a mandatory pre-flight and forbids reduced workflows.

### Changed

- The skeleton face is Hanken Grotesk (OFL) instead of the now-banned Inter.
- Docs reconciled with the code: marketing wow gate is 25% x 30% (`wow_visible`), the enforced type-scale rule is the 4x ratio (the 7vw h1 is guidance), and the section pass rule is the one in `critic.py` (explanatory visual >= 4, nothing below 3, at most two 3s).

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
