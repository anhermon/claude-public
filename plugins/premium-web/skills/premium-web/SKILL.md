---
name: premium-web
description: Build and redesign premium web interfaces in one of two modes chosen by a mandatory step 0 classification: marketing pages people READ (landing, product, portfolio, marketing, concept pages) or apps and tools people WORK in (dashboards, admin screens, internal tools, operations consoles, deployment-history and test-run UIs, run/trace/log views, table views, "redesign the UI of our app"). Use when asked to "build a premium page", "landing page", "portfolio page", "redesign the site", "make it look less AI-generated / less templaty", "add a wow factor", or to design, redesign, upgrade or modernise any dashboard, admin, internal tool, operations console or app screen. Marketing mode is the WRONG mode for anything users operate: those get app mode (task walk-throughs, density, state and interaction gates, signature clarity instead of a wow hero). By default builds several materially different candidates (3, configurable) and lets the user pick in a Claude Code mod pane. Encodes measured type rules, genre-escape rules, imagery via an image-generation MCP, and a mandatory screenshot + calibrated-critic loop; a gate that cannot run is reported UNVERIFIED: <reason>, never as premium.
---

# Premium web: marketing pages and work apps

Two bars, one discipline. A **marketing page** (people read it once) is premium when every section has a designed
visual that explains it, it has one signature moment a visitor would screenshot, and nothing on it could belong to 20
other products. An **app** (people work in it) is premium when the primary tasks are fast and clear, the data is dense
and legible, every state is designed and one distinctive, truthful way of drawing the product's own data shortens a
task. Metrics (Lighthouse 100, fonts loaded) prove neither: ember had all of them and was rejected as "generic AI
templaty". A calibrated critic, not the builder, decides when it is done. **Using the wrong bar is the commonest
failure**: marketing structure on a work tool, or a generic dashboard where a premium page was asked.

Paths below are relative to this skill dir (`~/.claude/skills/premium-web`).

## Step 0: classify the request (mandatory, written, before step 1)

Who uses the thing, how often, and what do they DO with it? Decide the primary mode from that, not from the words
"page" or "premium" in the request.

| class | the person ... | typical requests | mode |
|---|---|---|---|
| **READ** | arrives, reads, decides, leaves (once or rarely) | landing page, product page, portfolio, pricing, campaign or concept page, "make our marketing site premium" | `marketing` |
| **WORK** | comes back and operates it: find, compare, trigger, approve, edit, triage, monitor | dashboard, admin, internal tool, operations console, deployment-history viewer, test-run UI, run/trace/log view, queue, settings, "redesign the UI of our app", "upgrade these two ops tools" | `app` |
| **MIXED** | one product with both | a SaaS (public site + signed-in console), docs site with a live playground | **split** into two scoped deliverables, each its own mode, own folder and own NOTES.md |

1. **Evidence, not vibes.** Write: who uses it (role), how often (a number: opens per day or week; if unknown say "unknown,
   asked" or ask), the task verbs in the request or the product (find / compare / trigger / approve / edit / triage), and whether
   an existing UI is being redesigned (an existing app is WORK).
2. **Never default to marketing when the request mentions users operating the thing** ("our engineers use it", "internal",
   "ops", "on-call", "the team clicks"). "Make it a premium page" about a tool is still WORK.
3. **Ambiguous? Ask exactly ONE question, then stop**: "Do people come back to this and do things in it (find, compare, trigger, approve,
   edit), or do they read it once and decide?" Do not start building on a guess.
4. **Write it into the project's NOTES.md in this exact, parseable form** (a MIXED deliverable carries `classification: MIXED` plus `scope:`):
```
## Step 0 classification
mode: app                         # marketing | app   (tool is accepted as an alias of app)
classification: WORK              # READ | WORK | MIXED
scope: <MIXED only: the deliverable this mode covers>
users: on-call engineers on the platform team
frequency: daily, about 30 opens per engineer
evidence: request says engineers triage failed deploys; verbs find, compare, trigger a rollback  (>= 20 characters)
density_target: 20 rows at 1440x900        # app only: items visible at 1440x900
primary_tasks:                              # app only: 1-8 verb phrases, the daily jobs
- find last night's deploy
- compare two runs
```
   **The scripts enforce this**: `chrome-shot.mjs` (any run except `EVAL=measure-site.js`) and `critic.py` exit **4** with nothing run
   when the section is missing, invalid, or its `mode:` differs from the run's mode (`scripts/classify.py`; find NOTES.md via `PW_NOTES=<path>`
   or an ancestor of the output dir). tells.js refuses without it. A READ classification whose `users:` names operators is refused.
5. App mode needs `primary_tasks` and `density_target`; marketing needs neither (its one job is intake step 1).

## Hard rules (read before step 1)

**Read every file in `references/` before step 1. Never run a reduced workflow. If a step does not fit the task,
stop and ask; do not drop it, shorten it or call it a "poor fit".** (A run that read only this file and compressed the
mandatory signature-moment step to one line is the failure this prevents; so is a run that skipped the skill and
shipped a generic dashboard.) The step 0 gate above applies to both modes.

**Pre-flight, written into the project's NOTES.md before step 3 (an empty line means you are not ready):**
- Classification + evidence: the `## Step 0 classification` block above, complete.
- Primary tasks: app = the `primary_tasks` list with start state and recorded step counts (app-mode.md section 1); marketing = the page's one job and one claim (step 1).
- References read: list every `references/*.md` filename you opened.
- Genre named: "left alone this page / app becomes ___" (genre-escape.md section 1).
- Marketing: wow candidates >= 5, scored on distinctiveness / truth / scale, one picked, with its acceptance test (wow.md). App: the signature-clarity sentence and the walk-through plan (wow.md "App mode").

**No result is shown or reported until the gate 2 and gate 3 outputs (tells.js + saturation.py, then critic.py) are
pasted into NOTES.md and the reply.** "It renders, the clicks work" is gate 1 only and is never reported as verification.

**A gate that cannot run is `UNVERIFIED`, never a pass.** Cases: no Chrome/CDP (chrome-shot, tells.js: exit 1/2), no `claude`/`codex` session, quota
or network (critic.py exit 3), no Simulator or Lighthouse, a missing walk-through or tells scan (critic exit 3). The path, in order:
1. Write `UNVERIFIED: <gate>: <reason>` (e.g. `UNVERIFIED: critic.py: claude quota until 18:00`) in NOTES.md AND at the top of the reply, next to the gates that did run, with their pasted output.
2. Never write "pass", "premium" or "done"; never substitute functional checks, a manual read or your own score for the gate. State the status as `NOT VERIFIED`.
3. Fix the cause (start Chrome, wait for the quota reset, `CRITIC=codex`, run where a session exists) and re-run, or hand that gate to the user by name.
Exit codes: 0 clean, 1 failed, 2 usage/Chrome would not start, 3 UNVERIFIED (unknown, not failed), 4 classification missing/invalid (step 0).

**Time box and what to do when it runs out.** A full run (read all references, 5+ wow candidates, build, 3 gates, several critic
rounds) does not fit 60 minutes; critic.py alone is 5-20 min per round (its docstring). If the user gives a box:
- Plan the gates first: gate 3 is required, so reserve its rounds before polishing. Run critic.py in the background and tail stderr.
- Steps that need the network or the Simulator (`shoot.sh` real Mobile Safari, `lighthouse.sh`, image providers, font downloads) and
  cannot run: write `UNVERIFIED: <step>: <reason>` (e.g. `UNVERIFIED: shoot.sh: Simulator unavailable / out of time box`) in NOTES.md and
  the reply. Chrome-shot at 1440 + 390 is gate 1 evidence for what ran; it does not replace Safari, and the work is not "premium" or "done".
- If the critic's fix list is larger than the time left, STOP and report `NOT DONE` with critic.json's failing sections and fixes. Never
  claim done, never self-score, never skip the failing section.
- **Gate precedence**: gates are independent and ALL required. Critic fails while tells passes: the critic wins (gate 3 fails the page
  and exit is 1 regardless of tells; tells.js only adds failures, it never clears one). A clean tells scan means "no structural tells", not premium.
- **A gate that demands the wrong structure** (marketing gate on an app, `page_shaped_mismatch` on a real marketing page): do not pad the product with
  sections, do not wrap things in `data-wow`, do not weaken a threshold. Re-check step 0; if the classification is right and the gate still cannot be met by the honest product, stop and report the gate as mismatched.

## Candidates first (default since 2.0)

A premium page is a taste decision, and one build gives the user nothing to choose between. So by default this
skill builds **N materially different candidates**, shows them in the **Premium candidates** pane of the
`premium-web` mod, and finishes only the one the user picks. Full protocol, file schema and fallback:
`references/candidates.md`. In short:

1. **Decide N.** The user's explicit number in the request wins ("5 options", "just one"); otherwise call the
   `premium_web_get_settings` tool (mod) and use its `candidateCount`; otherwise 3. Cap 6 (say so if they asked for more).
   N = 1 skips this flow: run steps 1-9 below once, no pane.
2. **Intake and references once** (steps 1-2), shared by all candidates.
3. **Write N directions** (steps 3-5 in short form) that pass the distinctness gate in `references/candidates.md`
   section 2: different style recipe, palette family, type voice, layout shape AND a different signature wow family
   each (wow.md; genre-escape.md applies to every candidate). Near-duplicates are the failure mode, not a spare.
4. **Build the N candidates in parallel**, one agent each, in its own folder `.premium-web/build/<id>/` (or a
   worktree), each in a bounded time box, checkpointing to `<folder>/NOTES.md` as it goes. Never fork; give each
   agent its direction, the tokens, the proof inventory and the acceptance test for its wow.
5. **One critic pass per candidate** (step 9 gates 1-3, a single round, not the full iterate-to-green loop).
   Record the scores; do not spend the iteration budget on candidates the user may discard.
6. **Write `.premium-web/candidates.json` and screenshots**, then call `premium_web_present_candidates` (or tell the user
   to run `/candidates`) and **STOP**. Wait for the user's pick or feedback, which arrives as their next message.
7. **Feedback** ("Feedback on candidate B: ...") -> iterate that candidate only; ("Feedback on all candidates: ...") ->
   iterate all. Bump `round`, refresh screenshots, present again. **Pick** ("I picked candidate C") -> take only that
   candidate through the full step-9 loop (all three gates, iterate to green), then deliver. Drop the others.
8. **Mod unavailable** (Claude Code < 2.1.287, mods disabled, non-interactive, the tools are missing or return an
   error): use the chat fallback in `references/candidates.md` section 6 and still STOP for the user's pick.

## App mode (mode `app`: WORK; `tool` is an alias)

Applies when step 0 says WORK: a dashboard, admin, internal tool, console, run/trace/log view, editor, queue. Same discipline (read all references,
all steps, three gates, calibrated critic, candidates), different bar: **task speed and clarity**. Read `references/app-mode.md` (the standard),
`references/rubric-app.md` (what the critic scores), `references/app-exemplars.md` (measured work UIs) and wow.md "App mode" before step 1. What changes:
- **Intake = tasks.** `primary_tasks` and `density_target` come from step 0; add the product's real data object (the run, record, trace, order) with its fields,
  states, counts and a worst case. Sample data only when labelled "sample data"; never invent metrics a real system would not produce.
- **No page structure**: persistent shell + nav, the work surface in the first viewport, no hero, no scroll chapters, no closing CTA or footer columns, no section
  eyebrows. Regions are panes and views, not sections. If you catch yourself planning "sections", you are in the wrong mode.
- **No wow hero. Signature clarity instead** (wow.md "App mode"): one distinctive, truthful way of making the product's own data legible, validated by the walk-through
  (it shortens a task against the table baseline). It is judged by the critic, not sized by a detector.
- **Walk-throughs are the evidence**: perform each primary task in the real UI (Playwright), record steps, keystrokes and time-to-first-result, and write
  `walkthrough.json` (`{"tasks":[{"task","steps","result","shot","screens":[...]}]}`, the same fields as candidates.json `tasks[]`). Gate 3 reads it.
- **Starting point**: `assets/skeleton/app-shell.html` + `tokens-app.css` (light, state-only colour, 12-14px data, tabular numerals). The marketing skeleton is not a base for apps.
- **Styles**: the app recipes in styles.md; **genre**: the dashboard / run-view attractor in genre-escape.md; type rules in styles.md "App type".
- **Gates** (verification.md; the three gates still run on the real screens, one `data-screen` per view):
  `MODE=app EVAL=scripts/tells.js SECTIONS="[data-screen]" SHOTS=1 node scripts/chrome-shot.mjs <url> <out> 1440,390` then `python3 scripts/saturation.py <out>/*.png`, then
  `python3 scripts/critic.py <out>/sections --mode app --signature <screen-id> --signature-test "<sentence>" --walkthrough walkthrough.json`.
  tells.js app profile hard fails: `density`, `interactive_affordance`, `state_coverage`, `page_shaped_mismatch`, `data_wow_in_app` (any `data-wow`), `equal_card_grids`,
  `caps_micro_labels`, `palette`; `type_scale`, `wow_visible`, `scale_change`, `panel_run` are measured but not gated. Thresholds: wow.md "App mode".
- **Marketing thresholds are unchanged** and no app rule loosens them. `page_shaped_mismatch` flags WRONG-MODE STRUCTURE: rebuild as shell + work surface, or fix step 0 if nobody operates it.
- **MIXED**: two deliverables, two folders, two NOTES.md, each with its own classification and its own full run. Do not blend them into one page.

## Workflow

### 1. Intake (write it in the project's NOTES.md; checkpoint there as you go)
Marketing mode. (App mode: intake is step 0's users, tasks and density target plus the data object, see "App mode"; steps 3-9 below apply with the app substitutions stated in each.)
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
- Faces: styles.md "Faces" is the one status table (banned: Inter, Geist, Bricolage, Space Grotesk, Poppins, DM Sans, Plus Jakarta; reserved by earlier concepts; the
  Hanken Grotesk placeholder; free). `scripts/get-font.sh <fontsource-id> fonts` self-hosts an open-licence subset. Both skeletons ship Hanken Grotesk (OFL) only as a placeholder; swap it for the chosen one.

### 4. Concept, genre escape, one aesthetic risk
Write the idea ("the page is a trace") and the risk (a scale, a material, a colour block). Then write **"left alone this
page becomes ___ (genre template)"** and 4 concrete changes that escape it (genre-escape.md). If the idea would fit a
competitor's page, it is not the idea yet.

### 5. Signature moment (marketing mode; wow.md v2), MANDATORY, before building sections
App mode: replace this step with wow.md "App mode" (signature clarity sentence + walk-through plan, no size gate, no `data-wow`); the numbers below are marketing only.
Write the product's verb, **>= 5 candidates** across families, scored on distinctiveness / truth / scale (feasibility last),
reject any panel/chart/table/card row (that is the "nice" 3), pick one, and write its **acceptance test** ("a stranger
screenshotting this would say ___" + numeric checks). It must be the product itself above the fold or the page's centrepiece; the enforced size
(marketing 25% x 30%) and the 50% guidance are in wow.md "Placement". Poster/reduced-motion frame first. Recipes: `assets/skeleton/hero-strands.js` (WebGL),
`assets/recipes/scroll-scene.js`, `assets/recipes/particles.js`. Section-craft numbers (<= 3 consecutive panels, >= 2 scale
changes, type contrast, one real data visual, meaningful motion) are in genre-escape.md and gated by tells.js. Do a
reference-gap check against 3-5 live best-in-class sites (genre-escape.md section 3). Wow < 4/5 fails the page whatever else scores.

### 6. Section plan (marketing mode; rubric.md)
App mode: plan screens and flows instead (one flow per primary task, one `data-screen` per view; app-mode.md sections 1-2), never "sections".
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
Marketing: start from `assets/skeleton/` (app mode: `app-shell.html` + `tokens-app.css`, see "App mode"; tokens.css dark default + light, site.css, reveal.js, form.css/js, index.html with
OG/JSON-LD, poster + canvas hero) and restyle it to the direction; do not ship its look unchanged.
The skeleton's h1 tops out at 72px (5vw at 1440), below genre-escape.md's 7vw guidance, and its hero is a poster, not
your wow: adding the display-type moment and the signature object is your job, not the skeleton's.
- Motion (motion.md): UI .15-.2s, reveals .6s cubic-bezier(.2,0,0,1) via IntersectionObserver; WebGL/scenes with
  poster fallbacks for reduced motion, Save-Data, no WebGL, context lost, slow-frame watchdog; 60fps.
- Hiding: anything that must not be read or scored (marking slips, ghost marks, off-canvas copies, a faded duplicate layer) needs `inert`,
  not just `aria-hidden`: Lighthouse color-contrast still measures `aria-hidden` text (`inert` removes it from the tree). Applies to dim/low-opacity slips.
- Forms (forms.md): honeypot fully hidden (off-screen + clip + inert + aria-hidden), ~20px custom checkbox with a
  24px+ label hit area, inline errors, sending/success/error states. Never style `input` globally.
- Trust (trust.md): proof with sources and dates, limits stated plainly, who replies; no dark patterns.
- Theming: pick dark default, light default, or a deliberate single theme; tokens on `:root`, light/dark via
  `prefers-color-scheme` guarded by `:root:not([data-theme=...])` plus `[data-theme]` overrides; explicit `body`
  background; a dark-baked visual keeps a `.theme-dark` island in light mode. Check both schemes in screenshots.
- a11y/SEO/OG: verification.md last section.

### 9. Verify: three gates (verification.md). Do not report done before all three pass, with their output pasted.
An unrunnable gate is `UNVERIFIED` (Hard rules), not a pass.
In candidates mode this runs once per candidate during a round (record, do not iterate to green), and to green for the picked candidate only.
1. **Works**: `scripts/serve.mjs` -> `scripts/shoot.sh` (Chrome 1440 + 390 and real Mobile Safari on a private
   Simulator) -> `scripts/lighthouse.sh`. No horizontal scroll, fonts rendered, no console errors, trackers blocked.
2. **Not templaty**: `EVAL=scripts/tells.js SECTIONS=1 WOW=<sel> node scripts/chrome-shot.mjs ...` (app mode: `MODE=app`, `SECTIONS="[data-screen]"`, no `WOW`; see "App mode"), then the
   fallback frames with a SECOND run `RM=1 WOW=<sel> SHOTS=0 node scripts/chrome-shot.mjs ...` into the SAME out dir (adds `*-rm-tN.png`;
   with RM=1 the report goes to `report-rm.json`, so the gate-2 `report.json` and its eval are never overwritten and no EVAL is needed).
   `WOW_ACT=<js>` starts an interaction. WOW frames are mid-animation (7 time / 6 scroll positions) clocked from the scroll to the
   wow; for a wow that reveals on scroll add `WOW_DELAY=900` so frame t1 is after the reveal (.6s + stagger) completes. 4+ structural tells = fail. Then `python3 scripts/saturation.py <out>/*.png`: mean hot-pixel share
   > 0.12 = toy palette = fail (approved pages 0.00-0.01, rejected ember v3 0.19).
3. **Premium at section level**: `python3 scripts/critic.py --calibrate` once, then
   `python3 scripts/critic.py <out>/sections --wow wow --wow-test "<acceptance test>"` (marketing; canonical form everywhere; `--wow` is required. App mode: `--mode app --signature <screen> --signature-test "..." --walkthrough walkthrough.json`; `tells.js` `craft_fail` also fails the page). Fresh critic per section with gallery anchors; scores,
   ban hits, wow and the distinctiveness test; exit 0 only when everything passes. Iterate: fix, re-shoot, re-run,
   log each round in NOTES.md. Three failed rounds on one section = replace that section's visual idea.
   Scale: the critic scores 1-5 and 4 = 7/10; a brief's "7/10 and above" is applied as the pass rule: explanatory_visual >= 4, nothing below 3, at most two 3s, no ban hits (critic.py `verdict`, rubric.md).

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

Marketing pages: the list below. Apps (mode `app`) additionally: marketing structure on a work screen (hero, scroll chapters, closing CTA, footer columns, eyebrows);
adding sections or `data-wow` to satisfy a gate; the generic dashboard (greeting, KPI tile row with deltas, chart cards, 3-row table); controls that look clickable and are not
focusable; happy-path-only screens; invented metrics; "could be 20 other products" as a goal for a tool (distinctiveness there means the product's own data, drawn truthfully).

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
| references/app-mode.md, rubric-app.md, app-exemplars.md | app mode: the standard (tasks, walk-throughs, structure, gates), the screen/flow rubric the critic pastes, measured work UIs |
| references/rubric.md | marketing mode: the standard: section bar, ban list, templaty tells, distinctiveness test, scores, wow, anhermon per-section table, approved/rejected gallery |
| references/gallery/ | 23 anchor screenshots (approved / shipped / rejected / nice-not-wow, incl. tool-UI anchors) the critic compares against; README.md indexes them |
| references/gallery/README.md | gallery index: verdict and source of every anchor, incl. the tool-UI set |
| references/genre-escape.md | genre-template escape (marketing and dashboard attractors), marketing section-craft numbers (panel runs, scale changes, type scale), reference-gap check |
| references/wow.md | marketing signature-moment procedure, starter candidates per style, recipes, performance and fallback rules; "App mode": signature clarity and the app tells thresholds table |
| references/styles.md | style recipes incl. terminal-native without the cliche; material-by-style table; "Faces" status table; "App type" rules |
| references/imagery.md | MCP tools, providers, prompt template, recipes per style, steel-slab and line-art lessons, budgets, ToS note |
| references/type-systems.md, motion.md, forms.md, trust.md, verification.md | rules and the measured reference table |
| scripts/classify.py | the step 0 gate: parses the NOTES.md classification block; chrome-shot.mjs and critic.py call it (exit 4 when missing/invalid) |
| scripts/serve.mjs, chrome-shot.mjs, shoot.sh, lighthouse.sh | serve, screenshot (viewport steps, SECTIONS, WOW; MODE=app, step 0 gate), Simulator, Lighthouse |
| scripts/measure-site.js, tells.js, saturation.py | computed-style measurement (SUMMARY=1 for the short form); templaty-tells DOM scan (`data-tell-ok` marks deliberate repeats); hot-pixel saturation meter |
| scripts/critic.py | calibrated critic, pass/fail JSON: marketing = sections + wow + page; `--mode app` (alias tool) = screens + flows + signature clarity + generic-template verdict |
| scripts/test_critic_parse.py, test_tells.js, test_classify.py, test_app_live.sh | offline self-checks: critic verdicts/parse/app flows, tells.js gate maths and wow.md numbers, the classification gate (exit 4), live app/marketing DOM checks (needs Chrome; fixtures/) |
| scripts/gen-image.sh, optimize-images.sh, get-font.sh | image generation and AVIF/WebP; self-hosted fonts |
| references/candidates.md | the candidates protocol: N rules, distinctness gate, folder layout, `candidates.json` schema, feedback loop, chat fallback |
| hooks/register.ts, hooks/lib.ts (plugin root, not this dir) | the `premium-web` mod: `/candidates` pane, `premium_web_present_candidates`, `premium_web_get_settings` tools |
| mcp/imagegen/ | the premium-web-imagegen MCP server (server.py, core.py, api_call.py, test_core.py); providers incl. local fallback |
| ~/dev/freemium-demo-kit, ~/dev/audio-judge, ~/dev/local-imagegen | external tools for steps 10, 11 and the local image fallback (referenced, not copied) |
| assets/skeleton/ | marketing starting site (tokens.css dark default); app starting point (app-shell.html + tokens-app.css, light, state-only colour); assets/recipes/ scroll-scene.js, particles.js |
| examples/ | not shipped in this plugin (README.md "Acceptance test" describes them) |

Register the image MCP (Angel runs it; never edit his config):
`claude mcp add premium-web-imagegen -- uv run --with mcp==1.29.0 --with pillow==12.3.0 python ~/.claude/skills/premium-web/mcp/imagegen/server.py`

## What was tested (2026-10-01) and what was not

See README.md "Tested" for the full list. Untested: live API image providers (no keys; mocked), real Codex image
generation end to end (quota hit; the quota path is tested), Gemini-web/Higgsfield handoffs, audio-reactive and
physics recipes, real-device fps.
