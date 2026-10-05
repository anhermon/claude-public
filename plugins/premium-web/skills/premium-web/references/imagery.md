# Imagery

Pick every image by **what it communicates in its section**, never by how impressive it looks alone. If a section
needs a caption to explain its image, the image is wrong. Which sections get generated images at all depends on
the style (styles.md, "Material by style"); technical claims get code-drawn figures.

## The two lessons that cost the most

- **Steel slab (gallery/reject-guard-steel-slab):** a generated "steel gate with one slot, one thread passing"
  was the best of 16 images for the Guard section and still read as "this image is weird". It was replaced by a
  code-drawn allowlist of the real 15 paths with a rejected POST hitting it (gallery/accept-anhermon-v4-guard-codedrawn).
  Rule: **code-drawn diagrams beat photos for technical claims.** A photo can set mood next to a claim; it cannot
  make one.
- **Thin line art (gallery/reject-thin-line-art):** "flat 2D technical illustration, hairline strokes" prompts
  produce sparse sketches that say nothing. The same disease, hand-drawn in SVG, sank the Meridian method section.
  Never generate diagrams; never draw a diagram without real labels, values and state.

## Tools: the premium-web-imagegen MCP server (or the same module from the shell)

| tool | what it does |
|---|---|
| `list_providers()` | which providers are usable now (codex login, vaultlet keys present, browser handoff) |
| `art_direct(brief, slot, style_preset)` | builds the full prompt: slot composition + style look + negative list, and a review checklist |
| `generate_image(prompt, aspect, out_dir, name, provider="auto", variants=2)` | generates; idempotent names `<slug>-<hash8>.png`; skips files that exist; appends MANIFEST.md; global rate limit |
| `compare(paths)` | contact sheet + dimensions, aspect, bytes, near-duplicates (dHash); no text detection (not reliable) |
| `optimise(path, widths, formats)` | AVIF + WebP at 640/1024/1536, never upscales |
| `record_review(path, verdict, note)` | writes your verdict into MANIFEST.md, so the next run knows what was rejected and why |
| `complete_browser_job(job_id, path)` | finishes a Gemini-web / Higgsfield browser handoff after a browser agent saved the file |

Shell: `scripts/gen-image.sh art|gen|compare|optimise|review|providers ...` calls the same `core.py`.
Register the server (Angel runs this; the skill never edits config):
`claude mcp add premium-web-imagegen -- uv run --with mcp==1.29.0 --with pillow==12.3.0 python ~/.claude/skills/premium-web/mcp/imagegen/server.py`

Providers, in `auto` order: codex (`codex exec --skip-git-repo-check`, ChatGPT login) -> OpenAI / Gemini API / fal /
Together / Replicate (only when a key exists in vaultlet; run as `vaultlet run --ref vaultlet://<your-group>/KEY=KEY --`,
the key never enters the prompt, log or this process) -> gemini-web browser handoff.
- **Codex quota:** on its usage limit codex still exits 0. The tool reads its own log, reports
  `failed: codex quota/usage limit (try again at ...)` and never adopts an image it did not name (another agent's
  images land in the same `~/.codex/generated_images`). When generation is unavailable, draw in code instead and
  say so in the report; do not wait.
- **Browser handoff (Gemini web, Higgsfield):** writes a job file with claude-in-chrome steps and returns
  `needs_browser_agent`. ToS grey area, stated plainly: automating a consumer web UI is not what those products
  intend. It is only acceptable as Angel-authorised use of his own logged-in session, at low volume, never solving
  CAPTCHAs, never entering credentials. Gemini's download button failed in testing; screenshots were the only
  reliable capture, so expect lower resolution.

## Prompt template (art_direct builds this)

`<aspect> image (<w>x<h>). <subject: one concrete physical thing, what it does>. <slot composition>. <style look>. <negative list>`

Negative list (always): no text, letters, numbers, captions, watermarks, logos, UI, screens, people, faces, hands;
no glowing brains, robots, circuit boards, binary rain, fibre-optic stock imagery, lens-flare cliches, isometric
icon clutter. Replace the default hex colours in the look with the page's tokens.

## Recipes by style (style_preset)

| style | preset | subject recipe | good subject example | avoid |
|---|---|---|---|---|
| cinematic / creative | `cinematic-film` | a real place or object at human scale, one light direction | "a calm sea at dusk under heavy cloud, a thin band of warm light on the horizon" (halcyon hero) | sci-fi, neon, "epic" |
| tactile / clay | `tactile-clay` | one chunky object per section doing the product's verb | "a stack of soft rounded pebbles in five pastel colours, the top one cream" (pebble) | emoji-style 3D, gradients blobs |
| editorial dark product | `dark-studio` | a material close-up with a physical analogue of the data | "a row of fine metal pins along a glowing blue line on dark wood" (anhermon observe, then overlaid with real span labels) | literal metaphors (gates, locks, shields) |
| terminal-native | `terminal-world` | the place the tool lives, not the tool | "a rack in a dark machine room lit by one amber status light" | a picture of a terminal, code on screens |
| Swiss / data | none: code-drawn | charts, annotated figures, tables | n/a | photos, 3D |
| light / human | `paper-editorial` | still life of the work's real objects | "a stack of printed invoices with a paperclip, window light" | stock office scenes |

Generate 2 variants per slot, `compare` them, keep at most one, `record_review` every image (accepted AND rejected,
with the reason). Overlay real data labels in HTML on top of plates: the label makes it specific (anhermon observe).

## Gallery of accepted / rejected images (gallery/)

- accepted: accept-anhermon-v4-observe-plate (plate + real span labels), accept-anhermon-v4-pin-diff0 (texture plate
  + one number), approved-pebble-hero (clay stack + phone UI in code), approved-halcyon-hero (film still)
- rejected: reject-guard-steel-slab (literal metaphor, "weird"), reject-thin-line-art (says nothing)

## Budgets

Hero poster <= 180KB AVIF at 1536w; plates <= 90KB at 1024w; total image weight <= 900KB on mobile. `<picture>`
with AVIF then WebP, explicit `width`/`height`, `fetchpriority="high"` on the LCP poster only, `loading="lazy"` on
the rest. OG cards: composite the text locally over a generated background (never generate text).
