---
name: premium-web
description: Build or redesign premium, studio-quality web pages (landing, product, portfolio, marketing, storefront, concept pages) that do not look AI-generated. Use when asked to "build a premium page", "landing page", "marketing site", "portfolio site", "redesign the site", "make it look less AI-generated / less templaty / less generic", "add a wow factor", or to write a prompt/brief that lets another coding agent reproduce a site. Forces written design decisions before code, a persistent hero subject, motion and finish specs, and a render-and-look loop with an independent critic. Do NOT use for app UI or dashboards (operate-mode screens), backend or non-visual work, a single component fix, charts or data visualisation, or animated characters and mascots (use animated-objects).
---

# Premium web pages (v2)

A capable model asked for "a premium landing page" returns the average landing page. The cause is not missing
skill; it is missing decisions, missing time and light, and no one looking at the render. This skill forces the
decisions, names the failure modes, and closes the loop with a render and an independent critic.

## Thesis

1. Under-specified prompts collapse to the genre average. Decide first, in writing, before any code.
2. One persistent hero subject (3D, shader, generated image, drawn figure) carries the page and changes state per chapter.
3. Pages are choreographed in time: entrance, text reveals, scroll timeline, hand-offs, pointer response.
4. Light, material and grain are decisions; flat fills and default shadows read as generated.
5. Type and palette are restrained and measured: scale contrast, one family, neutral fields, one small hot colour.
6. Copy and proof are true, specific and labelled; nothing is invented.
7. The builder never grades its own work: render, LOOK (mid-animation frames, a true 390 viewport), independent critic.
8. Metrics are gates, not goals. Premium is judged on the render. No examples ship in this skill.

## Process (8 steps; keep a SPEC.md and tick it off)

1. **Spec before code.** Fill `references/spec-before-code.md` into SPEC.md: brief, truth inventory, genre test
   ("left alone this becomes ___"), subject and chapters, palette, type, motion grammar, finishing layer, asset plan,
   390 composition, acceptance tests. No code until every field has a concrete answer.
2. **Direction.** Choose style, type and palette by procedure (`references/direction.md`): measure 6-12 references,
   decide the scale, apply the banned-defaults list, close the reference gap.
3. **Hero subject and asset plan.** Run the wow procedure (`references/wow.md`): the product's verb, 5 or more
   candidates, an acceptance test. Classify each element as code, procedural or generated media. Detect image
   generation first (`premium-web-imagery`); if it is missing, draw the subject in code and say so.
4. **Section craft.** One message and one focal moment per section; rhythm numbers and the ban list in
   `references/section-craft.md`. Forms and trust in `references/forms.md`, `references/trust.md`.
5. **Build with the sub-skills.** Scroll choreography and text grammar: `premium-web-motion`. 3D and shaders:
   `premium-web-webgl`. Code-drawn figures, icons, filters: `premium-web-svg`. Generated imagery and scrub media:
   `premium-web-imagery`. Fetch fonts at build time (`scripts/get-font.sh`); never bundle them.
6. **Render and look.** `node scripts/verify-piece.mjs <dir>` (serves, captures, runs every mechanical gate), then LOOK at what it names;
   or by hand `scripts/serve.mjs` and `scripts/chrome-shot.mjs`: 1440 and a true 390, section shots, wow
   frames mid-animation, reduced-motion frames. Read every image and state what you saw (`references/qa-loop.md`).
7. **Independent critic.** `scripts/tells.js` and `scripts/saturation.py` first, then `scripts/critic-batch.mjs` / `critic.py` (flagged sections only; fresh
   critic per section, wow judged separately). At most 3 rounds per section; then replace the concept. Calibrate
   the bar against external references (`--pass-refs`, `--fail-refs`, `--calibrate DIR`).
8. **Ship.** Gates: no horizontal scroll at 390, zero console errors, fonts rendered, Lighthouse and a real mobile
   browser on the FINAL round. Report what passed, what was looked at, and what is untested.

## Load this reference or sub-skill when

| when | load |
|---|---|
| a page "works but looks generic", or you need the why behind a rule | `references/failure-modes.md` |
| starting any build (always, step 1) | `references/spec-before-code.md` |
| choosing style, genre, fonts, palette, scale | `references/direction.md` |
| planning or reviewing sections, rhythm, ban list, scores | `references/section-craft.md` |
| choosing the signature moment | `references/wow.md` |
| writing copy, proof, concept labels, storefront claims | `references/trust.md` |
| a form or lead capture is on the page | `references/forms.md` |
| rendering, gates, the critic, calibration, release hygiene | `references/qa-loop.md` |
| building several pieces, a token or wall-clock budget, batching and caching | `references/factory-efficiency.md` |
| the result must be reproducible by another agent or a client brief | `references/spec-prompts.md` |
| scroll choreography, text reveals, loader, transitions, pointer coupling | skill `premium-web-motion` |
| 3D scenes, point-morph, glass, shader backgrounds | skill `premium-web-webgl` (characters and mascots: `animated-objects`) |
| drawn figures, diagrams, animated SVG, icon systems, filters | skill `premium-web-svg` |
| generated imagery, image or video MCPs, consistent sets, scrub media | skill `premium-web-imagery` |
| many pieces fast: JSON to morph-subject (four hero layouts, morph/orbit/static) or code-only pinned rail panels; shared commerce and mobile compositions | skill `premium-web-factory` (`node skills/premium-web-factory/scripts/new-piece.mjs <spec> <out>`; choose via `references/grammars.md`) |

## Scripts (run from the skill directory)

| script | what |
|---|---|
| `verify-piece.mjs` | ONE command, all mechanical gates, <= 40-line summary + `.verify/report.json` (use first, every round) |
| `package-piece.mjs` | poster, size-budgeted loops, og, 8 section stills, piece.json entries (idempotent) |
| `critic-batch.mjs` | critic only on flagged sections, round-capped (wraps `critic.py`) |
| `asset-cache.mjs` | shared cache for generated imagery (`get` / `put`), outside the plugin |
| `serve.mjs` | static server: no-store, trackers stubbed, scroll probe |
| `chrome-shot.mjs` | Chrome capture over raw CDP: viewport shots, `SECTIONS`, `WOW`, `RM`, `EVAL`, overflow and font checks |
| `shoot.sh` | Chrome plus real Mobile Safari in a private iOS Simulator (macOS, Xcode) |
| `lighthouse.sh` | Lighthouse mobile and desktop, trackers blocked |
| `measure-site.js`, `tells.js` | computed-style measurement of references; structural-tell and craft-gate scan |
| `saturation.py` | hot-pixel share of screenshots (toy-palette meter) |
| `critic.py`, `test_critic_parse.py` | independent critic and its offline self-test (`python3 scripts/test_critic_parse.py`) |
| `get-font.sh`, `optimize-images.sh` | self-hosted open-licence font subset; responsive AVIF and WebP set |

## Hard rules

- No page ships without SPEC.md, a LOOK at the rendered frames, and a critic run (or a stated reason it could not run).
- Banned defaults (`references/direction.md`) need an external reference to unlock; a justification sentence does not.
- No invented logos, statistics or testimonials. Concepts carry a visible concept tag in the nav.
- No examples, screenshots, generated images or fonts are stored in this skill. Examples and anchors are inputs at run time.
- Code files stay under 800 lines; design values are named constants; no runtime CDN in templates (vendored, pinned).
