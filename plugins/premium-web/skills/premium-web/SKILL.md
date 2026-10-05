---
name: premium-web
description: Build premium, studio-quality web pages (landing, product, portfolio, marketing, concept pages) for any subject, and redesign existing ones. Use when asked to "build a premium page", "landing page", "portfolio page", "marketing site", "redesign the site", "make it look less AI-generated / less templaty", or "add a wow factor"; also application and tool UIs: "redesign / upgrade / modernise a dashboard, admin screen, internal tool, app screen, table view, run or trace view". Encodes measured type rules, section-level craft standards, a mandatory signature-moment ("wow") ideation with acceptance test, genre-escape rules, imagery via an image-generation MCP, and a mandatory screenshot + calibrated-critic loop that fails templaty pages even when Lighthouse is 100.
---

# Premium web pages

The bar: **every section** has a designed visual that explains it, the page has **one signature moment** a
visitor would screenshot and share, and nothing on it could belong to 20 other products. Metrics (Lighthouse 100,
fonts loaded) are necessary and prove nothing about premium: ember had all of them and was rejected as "generic AI
templaty". A calibrated critic, not the builder, decides when a page is done.

Paths below are relative to this skill dir (`~/.claude/skills/premium-web`).

## Hard rules (read before step 1)

**Read every file in `references/` before step 1. Never run a reduced workflow. If a step does not fit the task,
stop and ask; do not drop it, shorten it or call it a "poor fit".** (A run that read only this file and compressed the
mandatory signature-moment step to one line is the failure this prevents.)

**Pre-flight, written into the project's NOTES.md before step 3 (an empty line means you are not ready):**
- References read: list every `references/*.md` filename you opened.
- Mode: marketing page or tool mode (below).
- Genre named: "left alone this page becomes ___" (genre-escape.md section 1).
- Wow candidates: >= 5, scored on distinctiveness / truth / scale, one picked, and its acceptance test (wow.md).

**No result is shown or reported until the gate 2 and gate 3 outputs (tells.js + saturation.py, then critic.py) are
pasted into NOTES.md and the reply.** "It renders, the clicks work" is gate 1 only and is never reported as verification.

**A gate that cannot run** (no Chrome/CDP for chrome-shot or tells.js; no `claude`/`codex` session, quota or network
for critic.py, exit code 3) is reported as `UNVERIFIED: <gate>: <reason>`. Never write "pass", never say the page is
premium, never substitute functional checks or your own opinion for it. Fix the cause or hand the gate to the user.

## Application and tool UIs (tool mode)

Applies when the subject is a product screen, not a page that sells one: dashboard, admin, internal tool, table or
record view, run/trace/log view, settings. Same bar, same three gates, all of steps 1-9; the bar is not lowered for
density. What changes:
- Intake adds: **the product's data object** (the run, the record, the trace, the order) and its real shape (fields,
  states, counts, a worst case). Sample data is allowed only when labelled "sample data"; never invent metrics a
  real system would not produce.
- The wow is the product's own data object drawn at scale (wow.md "Tool mode"), not a hero card, KPI row or chart.
  The marketing-page numbers in this file do not apply to it; wow.md owns the tool-mode thresholds.
- Step 3 style: use the tool-UI recipes in styles.md. Step 4 genre: use the dashboard/run-view attractors in
  genre-escape.md. Density is a design material, not an excuse for panels.
- The skeleton (`assets/skeleton/`) is a marketing page: for tool mode take only tokens.css, reveal.js and the font;
  build the app shell yourself. Sections become views or regions; each still needs an explanatory visual, and the
  gates still run on the real screens (shoot each main view; `SECTIONS=1` where regions are `<section>`).
- Anchors: `references/gallery/` and wow.md "Measured exemplars" list what is measured for tools; the older anchors
  are marketing pages, so state in NOTES.md when no anchor fits your screen. If a gate fails because of the tool's
  structure, stop and ask; do not drop it.

## Workflow

### 1. Intake (write it in the project's NOTES.md; checkpoint there as you go)
- Audience: who arrives, from where, knowing what.
- The page's **one job** (one primary action) and its **one claim** in a sentence.
- **Proof inventory**: only real, checkable things (repos, releases, dated numbers, named people who agreed).
  Everything else is labelled sample data or cut. Never fabricate stats, logos, testimonials (trust.md).
- Constraints: brand, fonts already owned elsewhere, deadline, hosting, analytics.

### 2. Measure references first (type-systems.md)
Pick 6-12 real sites for the chosen direction. Run `scripts/measure-site.js` on each
(`EVAL=scripts/measure-site.js SHOTS=0 node scripts/chrome-shot.mjs <url> <out> 1440,390`, or paste into
claude-in-chrome) and tabulate h1/h2/body/header/button/section padding/motion. Decide the scale from the table.

### 3. Direction and type (styles.md, type-systems.md)
- Choose ONE style recipe from the subject: Swiss/data, terminal-native, tactile consumer, cinematic, editorial
  dark product, blueprint. Follow its "material by style" row: which sections get generated images, which get
  code-drawn figures, whether WebGL is in play.
- One family carries the page; a second face only as a deliberate voice; mono for code/data only; sentence case.
- **Palette = restraint** (rubric.md "Saturation and restraint"): large fields neutral or low-chroma (paper, stone,
  near-black), at most one or two saturated colours at small area. Playful primaries at full saturation across big
  areas read as a toy / game (ember v3, rejected). Write the palette as tokens in NOTES.md with the hot-pixel budget
  and pass them to imagery (`gen-image.sh art --colours ground=#..,accent=#..`; the presets default to dark blue, and so does the skeleton's `tokens.css`: both are placeholders, always override them).
- **Wrapper / showcase pages** (portfolio, gallery, directory) get a neutral identity of their own and must not
  inherit the author's site styling (hc-folio rejected for wearing anhermon.dev's look); the shown sites are the content.
- Banned faces for new concepts: Inter, Geist, Bricolage, Space Grotesk, Poppins, DM Sans, Plus Jakarta.
  `scripts/get-font.sh <fontsource-id> fonts` self-hosts an open-licence subset.
  The skeleton ships Hanken Grotesk (OFL) only as a placeholder face; swap it for the chosen one.

### 4. Concept, genre escape, one aesthetic risk
Write the idea ("the page is a trace") and the risk (a scale, a material, a colour block). Then write **"left alone this
page becomes ___ (genre template)"** and 4 concrete changes that escape it (genre-escape.md). If the idea would fit a
competitor's page, it is not the idea yet.

### 5. Signature moment (wow.md v2), MANDATORY, before building sections
Write the product's verb, **>= 5 candidates** across families, scored on distinctiveness / truth / scale (feasibility last),
reject any panel/chart/table/card row (that is the "nice" 3), pick one, and write its **acceptance test** ("a stranger
screenshotting this would say ___" + numeric checks). It must be the product itself at >= 50% viewport width above the
fold or the page's centrepiece. Poster/reduced-motion frame first. Recipes: `assets/skeleton/hero-strands.js` (WebGL),
`assets/recipes/scroll-scene.js`, `assets/recipes/particles.js`. Section-craft numbers (<= 3 consecutive panels, >= 2 scale
changes, type contrast, one real data visual, meaningful motion) are in genre-escape.md and gated by tells.js. Do a
reference-gap check against 3-5 live best-in-class sites (genre-escape.md section 3). Wow < 4/5 fails the page whatever else scores.

### 6. Section plan (rubric.md)
Up front, because the critic scores it in EVERY section including the hero close-up, the CTA and the access/config
sections (ember v3 round 1 scored 2-3 across the board for omitting it): each section has a **drawn explanatory visual**
(a figure that teaches the claim alone). A decorated list (timeline, bulleted config, step rows) is not one.
For every section write: the question it answers, its claim, and its **explanatory visual** (real UI in code with
believable data / annotated diagram with real labels and state / vetted generated image with a data overlay /
live micro-demo). Sections must change shape; none may be heading + hairlines + grey text, heading + 3-4 equal
cards, decorative 01/02/03, or empty space passed off as minimalism. Minimal styles get richness from precision
(annotation, real values, tabular numerals, texture), not from absence.

### 7. Imagery (imagery.md)
- Use the premium-web-imagegen MCP tools: `list_providers` -> `art_direct(brief, slot, style_preset)` ->
  `generate_image(prompt, aspect, out_dir, name, variants=2)` -> `compare(paths)` -> `record_review(path, verdict,
  note)` for every image -> `optimise(path)` (AVIF + WebP 640/1024/1536). Shell equivalent: `scripts/gen-image.sh`.
- Codex image generation (`codex exec --skip-git-repo-check`, ChatGPT login; the `codex` provider above, or the delegate-to-codex skill directly) is an available source alongside the MCP. Use it for hero/section imagery, textures and atmosphere that serve the wow concept; label illustrations as illustrations, never fake product screenshots or data; ship webp, sized, perf >= 90, content-hashed URLs.
- Presets: cinematic-film, tactile-clay, dark-studio, terminal-world, paper-editorial, neutral-product, material-texture.
- Pick images by what they say in their section. Technical claims get code-drawn figures (steel-slab lesson).
  Never generate diagrams or text. If generation is unavailable (Codex quota), draw in code and say so.
- Local fallback: provider `local` (`~/dev/local-imagegen/localgen`, MLX, offline, no quota) sits after `codex` in
  auto order, and auto mode falls through to the next usable provider when one fails (e.g. Codex usage limit).
  `IMAGEGEN_LOCAL_QUALITY=draft` (FLUX.2-klein-4B, ~1 min) or `final` (Z-Image-Turbo, ~2 min, default). Local output
  is below Codex for cinematic hero scenes (measured: hero 5-7 vs Codex 9), best for photoreal/product/texture
  plates, 1.5K max (1536px). Prefer Codex for the hero; use local for plates, or heroes when Codex is out.

### 8. Build
Start from `assets/skeleton/` (tokens.css dark default + light, site.css, reveal.js, form.css/js, index.html with
OG/JSON-LD, poster + canvas hero) and restyle it to the direction; do not ship its look unchanged.
The skeleton's h1 tops out at 72px (5vw at 1440), below genre-escape.md's >= 7vw rule, and its hero is a poster, not
your wow: adding the display-type moment and the signature object is your job, not the skeleton's.
- Motion (motion.md): UI .15-.2s, reveals .6s cubic-bezier(.2,0,0,1) via IntersectionObserver; WebGL/scenes with
  poster fallbacks for reduced motion, Save-Data, no WebGL, context lost, slow-frame watchdog; 60fps.
- Forms (forms.md): honeypot fully hidden (off-screen + clip + inert + aria-hidden), ~20px custom checkbox with a
  24px+ label hit area, inline errors, sending/success/error states. Never style `input` globally.
- Trust (trust.md): proof with sources and dates, limits stated plainly, who replies; no dark patterns.
- Theming: pick dark default, light default, or a deliberate single theme; tokens on `:root`, light/dark via
  `prefers-color-scheme` guarded by `:root:not([data-theme=...])` plus `[data-theme]` overrides; explicit `body`
  background; a dark-baked visual keeps a `.theme-dark` island in light mode. Check both schemes in screenshots.
- a11y/SEO/OG: verification.md last section.

### 9. Verify: three gates (verification.md). Do not report done before all three pass, with their output pasted.
An unrunnable gate is `UNVERIFIED` (Hard rules), not a pass.
1. **Works**: `scripts/serve.mjs` -> `scripts/shoot.sh` (Chrome 1440 + 390 and real Mobile Safari on a private
   Simulator) -> `scripts/lighthouse.sh`. No horizontal scroll, fonts rendered, no console errors, trackers blocked.
2. **Not templaty**: `EVAL=scripts/tells.js SECTIONS=1 WOW=<sel> node scripts/chrome-shot.mjs ...` (+ `RM=1` for
   the fallback frames; `WOW_ACT=<js>` to start an interaction). WOW frames are mid-animation (7 time / 6 scroll
   positions). 4+ structural tells = fail. Then `python3 scripts/saturation.py <out>/*.png`: mean hot-pixel share
   > 0.12 = toy palette = fail (approved pages 0.00-0.01, rejected ember v3 0.19).
3. **Premium at section level**: `python3 scripts/critic.py --calibrate` once, then
   `python3 scripts/critic.py <out>/sections --wow wow --wow-test "<acceptance test>"` (`--wow` is required; `tells.js` `craft_fail` also fails the page). Fresh critic per section with gallery anchors; scores,
   ban hits, wow and the distinctiveness test; exit 0 only when everything passes. Iterate: fix, re-shoot, re-run,
   log each round in NOTES.md. Three failed rounds on one section = replace that section's visual idea.
   Scale: the critic scores 1-5 and 4 = 7/10; a brief's "7/10 and above" means every relevant score >= 4.

Then Read every screenshot yourself. A passing transcript is not a passing render.

### 10. Redesign Lab demo (optional step)
Only when the page is a redesign pitched to a business. Kit: `~/dev/freemium-demo-kit` (README.md; reference it, do
not copy it). Turns the finished static site into a private noindex demo: top ~20% live, rest a blurred poster, real
locked markup only in Cloudflare KV. After the screenshot loop passes:
1. Write `demo.json` beside the built site (name, business, contact, buyUrl, accent; `freePercent` default 20;
   `scriptVariants` `{"app.js": "app.free.js"}` when needed).
2. `node bin/demo.mjs build <site-dir> --config demo.json` (fails if locked text/asset names leak into public files).
3. `node bin/demo.mjs deploy <slug>`, then `node tests/verify.mjs <slug>`.
4. `node bin/demo.mjs link <slug>` and send that URL to the business. Unlock after payment: `demo unlock <slug>`.
Authoring rules (build the page so the kit can split it):
- Each section is a direct child of `<main>`; the footer/disclaimer sits outside `<main>`.
- Per-section behaviour in separate scripts, or supply `app.free.js` (a free-only variant); a shared script is public.
- Single-page sites only. 20% free by default. Exclusive assets must not share file names with free ones.

### 11. Sites with sound (optional step)
Audio is a procedural WebAudio layer (oscillators, filtered noise, stochastic transients), started behind a user
gesture ("enter"/sound toggle) with a visible mute. Verify by listening with `~/dev/audio-judge`:
`node capture-page-audio.mjs <url> --action "#enter" --action wait:2 --seconds 20 --out rain.wav`, then
`./audio-judge match rain.wav --expect <concept>` (rain ocean wind fire thunder birds bell drone pad fog dusk).
PASS = gate; WEAK = needs a human ear; FAIL = fix the sound. Use clips >= 10 s (AST windows).
- Rain targets: per-drop HF transients > ~2/s and spectral flatness well below .79 (steady noise reads as
  Static/White noise); band-limit and vary level. Wind and procedural ocean are not reliably judged (WEAK at best).
- Limits: it judges recognisability and signal facts only. It cannot judge taste, mix balance, loudness against
  the rest of the site, or whether a loop is boring; a human listens before shipping.
- The ElevenLabs sound layer needs a key with the `sound_generation` scope; the current key returns 401, so use
  procedural audio until that is fixed.

## Anti-patterns (each one got real work rejected; anchors in references/gallery/)

- Stick-figure schematics and thin line art: hairlines and boxes standing in for a concept (Meridian method).
- Bare hairline-and-text sections; empty whitespace as "minimalism".
- Identical card grids; headline-then-3/4-cards section after section; sections that could swap places.
- Uppercase tracked mono eyebrows / micro-labels on everything; mono body copy; `[bracket]` nav.
- Dev-tool cliches: `curl | sh` hero box, "no daemon / no telemetry" principle cards, blinking-cursor-only hero.
- One-note palette (mono ground + one accent) with no material, depth or imagery.
- Bricolage tight/condensed with mono labels (v3); serif + mono eyebrows + italic accent word (03364e9).
- Warm-beige + serif as a default rather than a decision.
- Stock fibre-optic / glowing-brain / circuit imagery; literal-metaphor photos (steel-slab guard).
- Fabricated stats, logos, testimonials; unverified claims.
- A "nice" interactive panel as the only idea (Meridian: "nice, but it's missing a wow factor").
- A timeline list beside a mono command panel; bordered mono panels as every section's container (ember r2:
  "looks bad", "mid"). Required instead: at least one full-bleed typographic or drawn section per page.
- Oversaturated / toy / game look: full-strength primaries as grounds, rainbow overprint, pill-and-sticker UI (ember v3).
  Premium palettes are quiet; see rubric.md "Saturation and restraint" and `scripts/saturation.py`.
- A wrapper site wearing its author's own styling (hc-folio).
- A signature animation judged only at rest (ember r2: "the animation needs a bit more polish"): run motion.md's
  polish checklist on the mid-animation frames.

## Files

| path | what |
|---|---|
| references/rubric.md | the standard: section bar, ban list, templaty tells, distinctiveness test, scores, wow, anhermon per-section table, approved/rejected gallery |
| references/gallery/ | 17 anchor screenshots (approved / shipped / rejected / nice-not-wow) the critic compares against |
| references/genre-escape.md | genre-template escape, section-craft numbers (panel runs, scale changes, type scale), reference-gap check |
| references/wow.md | signature-moment procedure, starter candidates per style, recipes, performance and fallback rules |
| references/styles.md | style recipes incl. terminal-native without the cliche; material-by-style table |
| references/imagery.md | MCP tools, providers, prompt template, recipes per style, steel-slab and line-art lessons, budgets, ToS note |
| references/type-systems.md, motion.md, forms.md, trust.md, verification.md | rules and the measured reference table |
| scripts/serve.mjs, chrome-shot.mjs, shoot.sh, lighthouse.sh | serve, screenshot (viewport steps, SECTIONS, WOW), Simulator, Lighthouse |
| scripts/measure-site.js, tells.js, saturation.py | computed-style measurement (SUMMARY=1 for the short form); templaty-tells DOM scan (`data-tell-ok` marks deliberate repeats); hot-pixel saturation meter |
| scripts/critic.py | calibrated section/wow/page critic, pass/fail JSON |
| scripts/gen-image.sh, optimize-images.sh, get-font.sh | image generation and AVIF/WebP; self-hosted fonts |
| mcp/imagegen/ | the premium-web-imagegen MCP server (server.py, core.py, api_call.py, test_core.py); providers incl. local fallback |
| ~/dev/freemium-demo-kit, ~/dev/audio-judge, ~/dev/local-imagegen | external tools for steps 10, 11 and the local image fallback (referenced, not copied) |
| assets/skeleton/ | generic starting site; assets/recipes/ scroll-scene.js, particles.js |
| examples/ | not shipped in this plugin (README.md "Acceptance test" describes them) |

Register the image MCP (Angel runs it; never edit his config):
`claude mcp add premium-web-imagegen -- uv run --with mcp==1.29.0 --with pillow==12.3.0 python ~/.claude/skills/premium-web/mcp/imagegen/server.py`

## What was tested (2026-10-01) and what was not

See README.md "Tested" for the full list. Untested: live API image providers (no keys; mocked), real Codex image
generation end to end (quota hit; the quota path is tested), Gemini-web/Higgsfield handoffs, audio-reactive and
physics recipes, real-device fps.
