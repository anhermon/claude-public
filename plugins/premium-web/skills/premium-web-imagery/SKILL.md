---
name: premium-web-imagery
description: >
  Plans and produces the raster imagery and video/scroll-scrub media for a premium web page: capability detection first (the
  premium-web-imagegen MCP, any other image or video generation MCP, codex image generation, a local FLUX / Z-Image CLI, or none),
  art direction with one style sheet and seed so a set stays consistent, prompt templates, generate-vs-draw decisions,
  post-processing (trim, matte, grade, grain, AVIF/WebP, responsive sizes, budgets), generated video and scroll-scrubbed media
  (all-intra MP4 and image sequences via ffmpeg), licence and ToS notes, and a procedural fallback when nothing can generate.
  Use for "generate the hero image", "AI imagery for the site", "make the images consistent", "scroll-scrub video", "optimise
  images for the web", "what image tools do I have", "OG image", "texture or backdrop plate".
  Do NOT use for diagrams, data figures, icons or animated SVG (premium-web-svg), live 3D or shader scenes (premium-web-webgl),
  scroll/text/loader choreography (premium-web-motion), page strategy and layout (premium-web), or mascots and avatars
  (animated-objects:threejs / :raymarched).
metadata:
  version: "0.1.0"
---

# Imagery and scrub media

Generated pictures are one asset class among four (code, procedural, generated media, user-supplied). This skill decides when
generation earns its place, finds out what can generate, keeps a set consistent, finishes it for the web, and falls back to code
when nothing is available. `template/` is a working, config-driven pipeline: edit `imagery.config.json`, run the scripts.
Never write generated files into this skill or the plugin repo; outputs go to the user's project (`paths` in the config).

## Decision table

| Slot | Do | Where |
|---|---|---|
| Technical claim, mechanism, data, process | draw in code | `premium-web-svg` |
| Persistent hero object, depth, atmosphere that can be live | shader or 3D | `premium-web-webgl` |
| Mood, material, place, still life, texture, backdrop | generate (or procedural plate) | this skill |
| Footage that must follow scroll | image sequence / all-intra video | `references/scrub-media.md` |
| Real product, person, place, proof | the user supplies it | say so; never synthesise |
| Anything with text, numbers, UI | HTML/SVG overlay on a plate | never generate text |

## Workflow

1. **Detect capability first.** Read your tool list (MCP image/video tools) and run `python3 template/pipeline.py detect`.
   Pick one rung of the ladder (`references/capability-detection.md`) and record it in the asset plan. None available is normal: go to step 7.
2. **Asset plan.** One row per slot: purpose in its section, code vs generated, aspect, budget. Cut any image that needs a caption to make sense.
3. **Style sheet.** Fill `template/imagery.config.json` `style` from the page's own tokens (palette, one light direction, one material
   family, grain, mood, seed). One sheet for the whole set (`references/art-direction.md`).
4. **Prompts.** `python3 template/pipeline.py prompts` writes one prompt per asset (slot composition + style + negative list). With the MCP use
   `art_direct`. Subject = one concrete physical thing, never a literal metaphor.
5. **Generate**: 2 variants per slot, same seed, one session. Compare side by side, keep at most one, record accepted and rejected with reasons.
6. **Post-process**: `python3 template/pipeline.py post <id>` (trim for cut-outs, matte, grade, grain, resize 640/1024/1536, AVIF/WebP, budgets,
   srcset). Wire with `<picture>` (`references/post-processing.md`).
7. **Procedural fallback** when nothing generates: `python3 template/pipeline.py fallback <id>` gives a palette light-field plate; hand figures to
   `premium-web-svg` and live hero scenes to `premium-web-webgl`. State in the report what was drawn instead of generated.
8. **Scrub media** (only when scroll must drive footage): `template/scrub.sh in.mp4 out/` then `scrub-player.js` (`references/scrub-media.md`).
9. **Verify** (next section) and report which rung was used.

## Verification loop (mandatory)

- Unit checks: `python3 template/test_pipeline.py` and, after any change to the server, `python3 mcp/imagegen/test_core.py`.
- Scrub media: `node template/selftest.mjs` (needs ffmpeg, Chrome, Playwright; set `PLAYWRIGHT_NODE` to a node_modules dir). It encodes a test clip,
  asserts every packet is a keyframe, scrolls the demo to 0 / 50 / 100 %, asserts the frame index or `currentTime`, captures PNGs into `.selftest/`.
- LOOK at the PNGs and at the final images in the page: same light, grade and grain across the set, copy area empty and readable on a
  real 390 px viewport, no stray text or artefacts, poster = first scrub frame. A passing script is not a passing render.
- Check weight against the budgets; check `alt`, `width`/`height`, one `fetchpriority="high"` image.

## Rules

- Provenance: numbers in the references marked "measured" come from public reference sites, 2026-11; others are practice defaults and say so.
- No fonts, generated assets or screenshots inside the skill. No text inside generated images.
- Keys never enter prompts, logs or the page. Browser handoff to consumer UIs only with the owner's own session (`references/providers.md`).
- Code files <= 800 lines, constants named (see `pipeline.py` top).

## Pointers

| Need | Read |
|---|---|
| What can generate here; the ladder; procedural path | `references/capability-detection.md` |
| Style sheet, prompt template, generate vs draw, genre recipes, review | `references/art-direction.md` |
| Grade, grain, formats, budgets, `<picture>` | `references/post-processing.md` |
| Video and scroll-scrub media | `references/scrub-media.md` |
| MCP server, providers, quota, ToS, licences | `references/providers.md` |
| Characters and mascots | `animated-objects:threejs`, `animated-objects:raymarched` |
