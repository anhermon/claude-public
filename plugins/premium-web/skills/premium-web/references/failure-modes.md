# Why AI-built sites look AI-built (causal model, v2)

Read this first when a page "works but looks generic". Each failure below lists the symptom you can see, why a
capable model produces it, the instruction that prevents it, and a check that detects it. A check marked
"unautomated" has no script: a human or the critic must LOOK. Counts come from the evidence base for this
skill: 16 reference sites torn down from screen recordings with measured values, 3 full pilot builds that
followed an earlier version of this skill and were then critic-scored, and several earlier builds that a human
reviewer rejected. Counts are rounded and were taken in 2026-10 and 2026-11.

Contents: What the evidence changed - F1 Prior collapse - F2 The subject does not persist - F3 Layout without
time - F4 Flat rendering - F5 Type and spacing defaults - F6 Open-loop generation - F7 Averaged copy and fake
proof - F8 Responsive as an afterthought - F9 Metrics mistaken for proof - F10 Diagram compulsion - F11
Skill-borne imitation - Check map

## What the evidence changed

The first model was ten causes. Testing it against the evidence changed it in five places:
1. **"No visual subject" was wrong as stated.** All three pilots had a hero object (a WebGL cloud, a 3D vessel, an
   animated ledger) and still failed. What failed is that the subject stopped after the hero: in the worst pilot
   the lower half fell back to dark mono panels and 5 of 7 sections failed the critic. All 16 reference sites keep ONE subject alive across chapters and
   change its state per chapter. See F2.
2. **A new cause appeared: diagram compulsion (F10).** The earlier skill required a drawn, annotated figure in
   every section and scored "density". In 2 of 3 pilots that rule produced 3 critic rounds spent on label
   collisions, half-drawn captures and figures below the fold, while polish stayed at 2-3. None of the 16
   teardowns lists an annotated data diagram among its recurring techniques; they carry sections with subject,
   type, media and light.
3. **Imagery is not the universal gap.** Of 16 teardowns, 6 are procedural, 4 rely on ONE hero asset, 6 are media-led genres
   needing 8-14 consistent images. The need depends on genre (F2, F4).
4. **The critic can be wrong in both directions.** The builder grades itself leniently (F6), but a rubric-only critic scored
   too strictly (no section above 4 in the pilot corpus). Set bars from external references, not from prose alone.
5. **A banned default can be unlocked by a sentence.** Two pilots each wrote a paragraph justifying exactly the
   default the skill banned (warm paper plus a serif), and passed their own check. A default is unlocked only
   by an external reference that is not the category average (F1).

## F1 Prior collapse

- **Symptom:** centred hero, gradient or blurred blobs, three equal cards, logo strip, CTA band; or the genre's
  default dress (dark graphite plus hairline mono panels for developer tools, cream plus serif for "editorial").
- **Evidence:** 0 of 16 references look like this. 3 of 3 pilots named their genre attractor in their own intake;
  one still ended with a dark mono-panel lower half and one with the rationalised cream-and-serif default.
- **Why:** a short brief leaves most decisions open, and every open decision resolves to the highest-probability
  token sequence. The modal page is the average of all pages in the genre, which is what "AI-looking" means.
- **Prevent:** force written decisions before any code (spec-before-code.md): subject, chapters, palette world,
  type pair, motion grammar, asset plan. Write "left alone this page becomes ___" and four concrete escapes.
  A banned default may be used only if the spec names an external reference that uses it and is not the
  category average; a justification sentence alone does not unlock it (direction.md).
- **Check:** `tells.js` (equal_card_grids, mono_panels, panel_run, palette, cliches); critic page question "could
  this belong to 20 other products, name two"; spec has a non-empty genre-escape line (unautomated, read it).

## F2 The subject does not persist

- **Symptom:** a strong hero, then sections that could belong to another site; the hero object never returns.
- **Evidence:** 16 of 16 references hold one persistent subject (3D object, particle field, shader, photographed
  or rendered object, drawn world) across the scroll and change its state, camera or colour grade per chapter; about
  12 of 16 hand off a palette per chapter. In the worst pilot 5 of 7 sections failed after a hero that passed.
- **Why:** each section is generated as a separate unit. Nothing in the context says "the same object continues",
  so the model draws new local content and the effort budget is spent on the hero.
- **Prevent:** the spec names ONE hero subject and, per chapter, its state (position, form, colour, camera). The
  asset plan classifies every element as code, procedural or generated media and names the fallback. Pick the
  asset class by genre: procedural is enough for technology and abstract subjects; goods, places and people need
  consistent generated or photographic media (8-14 images from one style sheet); a single hero asset is the
  middle case. If image generation is unavailable, draw the subject in code and say so (premium-web-imagery,
  premium-web-svg, premium-web-webgl).
- **Check:** scroll-shot every chapter and ask "is the subject visible or evoked in each?"; the subject must not sit on copy, under
  the nav, or over a dense chart (`verify-piece.mjs` collision and nav-clip checks, given a subject box). `tells.js` material and
  no_fullbleed; critic `focal_visual`. A chrome that hides the subject at rest (a pill nav over it) is a defect, not a hand-off.

## F3 Layout without time

- **Symptom:** everything is there on load or fades up one uniform way; no entrance, hand-offs or pointer response.
- **Evidence:** blur or line-mask text reveals (0.5-0.7 s, 40-150 ms stagger) in about 15 of 16 references;
  scroll as the master timeline (one pinned or fixed stage driven by scroll progress) in at least 8 of 16; a
  designed loader or entrance as "chapter 0" in 8 of the 12 sites analysed for it; pointer coupling in 6 of the 8
  analysed for it. The pilots scored 3 on motion: no text choreography, no
  pinned sequencing, no easing signature.
- **Why:** models write layout, not choreography; a one-shot prompt never defines the time axis.
- **Prevent:** a motion grammar in the spec with numbers: entrance, text reveal (duration, stagger, easing), scroll
  timeline segments, chapter hand-offs, pointer coupling, reduced-motion state. One easing family, one stagger
  rule, transitions under 0.7 s (premium-web-motion).
- **Check:** unautomated: LOOK at mid-animation frames (qa-loop.md); critic `motion_polish` on those frames.

## F4 Flat rendering

- **Symptom:** flat fills, default shadows, additive points with no depth; nothing looks lit or made of a material.
- **Evidence:** 4 of 4 sites in one group put a single hot colour on a dark stage with a floor glow and grain; 3 of
  4 in another add grain, scanline or vignette overlays; two pilots were marked down for "flat additive points,
  no lighting" and for a "soft, airbrushed render".
- **Why:** CSS and canvas defaults are flat; light, material and grain are decisions nobody prompts for.
- **Prevent:** a finishing layer in the spec: light direction, one environment, grain amount (3-10 percent),
  vignette, glow and bloom limits, material per surface. Ban default shadows and flat panels as finish.
- **Check:** critic `finish` score per section; `saturation.py` for the colour side; grain and light presence are
  unautomated (LOOK at a 100 percent crop).

## F5 Type and spacing defaults

- **Symptom:** the default or most-chosen family, one size step between heading and body, equal gutters, every
  label in tracked uppercase mono, everything the same weight.
- **Evidence:** the largest text is 4.5-5.5 times body on UI-led references and a cropped giant wordmark (about
  38 percent of viewport height) on type-led ones; both regimes avoid the middle. One pilot was flagged for
  mono micro-labels in every critic round.
- **Why:** type is the highest-frequency default; one scale reads as consistency, so the model keeps it.
- **Prevent:** measure 6-12 references for the chosen direction and decide the scale from the table
  (direction.md): display-to-body ratio, weight contrast, tracking by size, one family plus one deliberate
  voice, mono for data only, sentence case. Density must vary: some sections are one sentence at display size.
- **Check:** `tells.js` type_scale (largest >= 4x median), caps_micro_labels, mono_body; the chrome-shot report
  shows which font actually rendered per selector ("(system)" means your font did not load).

## F6 Open-loop generation

- **Symptom:** the first render is the last; defects a human sees in seconds ship: clipped labels, overflow at 390.
- **Evidence:** in every pilot the defects that survived to the final round were ones a screenshot shows: a
  horizontal overflow introduced by a late CSS override (588 px wide at a 390 viewport), a badge covering content
  at 390, labels clipping, a figure captured mid-draw, a hero cloud missing on mobile. Headless captures of WebGL
  scenes came out blank or software-slow until a GPU flag was set. In a screen-recorded reproduction run, the agent said it
  verified only one desktop size.
- **Why:** the author believes its code; looking costs a browser and tokens, so it is skipped or graded leniently.
- **Prevent:** render, LOOK, fix, repeat, with a fresh critic that did not write the page, a true 390 device
  emulation, mid-animation frames, and a bounded round budget (qa-loop.md). Calibrate the critic against
  external references so it is neither lenient nor unreachable.
- **Check:** chrome-shot exits non-zero on horizontal scroll, failed fonts and console errors; `critic.py`
  (fresh critic per section); the figure for a section must sit inside its first 900 px because the critic
  only sees viewport shots.

## F7 Averaged copy and fake proof

- **Symptom:** "Unlock the power of...", "seamless", "blazing fast", invented logos, quotes, user counts,
  benchmarks and press, sample numbers presented as fact.
- **Evidence:** the pilots avoided fabricated proof only because the brief forced a truth inventory and a
  concept tag; the tag still had to move from a fixed overlay (it covered content at 390) into the nav.
- **Why:** true, specific claims need facts the model lacks; averaged claims are free. Live measured readouts count as proof: Chrome coarsens `performance.now()`, so print "<0.1 ms" or time N repeats, never "0.00 ms".
- **Prevent:** a truth inventory before copy (trust.md); every number has a source and a date or is labelled
  sample data; every headline passes a specificity test (swap the brand name: would it still be true of a
  competitor?).
- **Check:** `tells.js` cliches (2 or more); critic page question; grep the page for numerals and logos not in
  the inventory (unautomated).

## F8 Responsive as an afterthought

- **Symptom:** desktop squeezed into one column; the wow object missing on phones; overlays covering content.
- **Evidence:** in the pilots every mobile defect was a squashed desktop decision: hero taller than the viewport
  moving the scroll anchor, a nav CTA overlapping the h2, a legibility audit dropping to 40 percent because mono
  labels were under 12 px. A second class appears only on a real device: browser toolbars shorten the viewport.
- **Why:** one layout is written, breakpoints come after.
- **Prevent:** the spec defines a separate 390 composition per chapter (what leads, what is cut, where the
  subject sits). Test a true device-emulated viewport every round, and a real mobile browser on the final round.
- **Check:** chrome-shot overflow report at 390; `shoot.sh` (Simulator); Lighthouse font-size audit; critic
  receives the 390 shots.

## F9 Metrics mistaken for proof

- **Symptom:** the builder reports "Lighthouse 100" as the result.
- **Evidence:** a generic page and the best pilot both scored 100 in all four categories while 5 of 7 pilot
  sections failed the critic.
- **Why:** a number is easy to produce and report; taste is not.
- **Prevent:** metrics are gates (must pass), never goals or evidence of quality; premium is judged on the render.
  Poster-first LCP keeps a heavy hero from costing the score (premium-web-webgl).
- **Check:** `lighthouse.sh` as a gate; the report states the critic result and what was looked at.

## F10 Diagram compulsion

- **Symptom:** every section carries a labelled mini-chart; sections fail polish on overlapping annotations;
  the lower page reads as documentation.
- **Evidence:** "What the evidence changed", point 2. The earlier critic enforced a figure per section, so each
  round's fix (add a figure) ran into collisions and fold limits again.
- **Why:** scoring "explanatory visual >= 4" in every section rewards quantity of annotation; the references win
  on atmosphere, scale and a continuing subject.
- **Prevent:** a section needs one focal moment that carries its single message: the subject's chapter state, a
  type moment, a media band, real UI in code, or a live micro-demo. An annotated diagram is for sections whose
  job is to explain a mechanism, and every number in it comes from one array (section-craft.md).
- **Check:** critic `focal_visual` (not "diagram"); `tells.js` panel_run; max 2 annotated figures per page is a
  guideline, reviewed by LOOK.

## F11 Skill-borne imitation

- **Symptom:** pages that echo the examples a skill ships (same composition, same palette); stale thresholds;
  assets that reappear in unrelated pages; a ban list contradicted by a bundled file.
- **Evidence:** the earlier skill shipped screenshots, a generated hero image and a font it also banned; its
  critic calibrated on those screenshots and its scan thresholds were tuned on under ten pages (one approved page
  already met the failing hit count).
- **Why:** examples in context get copied; thresholds fit to a handful of pages overfit.
- **Prevent:** instructions and measurable criteria only. Examples and anchors are supplied at run time from
  outside the skill. Every numeric threshold names its provenance and is a named constant.
- **Check:** before release, grep the whole plugin for project names, image binaries and bundled fonts (see
  qa-loop.md, "Release hygiene").

## Check map

| check | covers | automated by |
|---|---|---|
| genre-escape line, truth inventory, asset plan | F1 F2 F7 | spec review (unautomated) |
| equal cards, mono panels, panel run, caps labels, palette, cliches | F1 F5 F7 F10 | `scripts/tells.js` |
| type ratio, scale changes, wow above the fold | F5 F2 | `tells.js` craft gates |
| hot-pixel share | F4 | `scripts/saturation.py` |
| overflow, fonts, console | F6 F8 | `scripts/chrome-shot.mjs` |
| mid-animation frames | F3 | chrome-shot WOW frames, then LOOK |
| fresh critic, wow, page | F1 F4 F6 F10 | `scripts/critic.py` |
| real mobile browser | F8 | `scripts/shoot.sh` |
| metrics gate | F9 | `scripts/lighthouse.sh` |
| all mechanical gates in one run | F6 F8 F9 | `scripts/verify-piece.mjs` |
