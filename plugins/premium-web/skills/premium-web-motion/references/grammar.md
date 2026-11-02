# The motion grammar (measured)

Contents: how to read the tables, entrance chapter, headline and text reveals, the pinned stage, hand-offs, section transitions, rails and steppers, chrome.

Provenance for every number below: measured from 16 public cinematic reference sites, 2026-11; 6-17 s recordings at 10 fps with 30 fps spot frames,
so timings are +-0.3 s unless a row says otherwise. "Practice" marks defaults that were not measured. The template module that implements each row is named in
the last column; its `DEFAULTS` carries the same numbers.

Finding that shapes everything: 85-95 % of the "premium" read is procedural DOM/CSS choreography, not assets. Pages that feel directed share one grammar:
a designed entrance (chapter 0), reveals that resolve text out of blur, ONE persistent stage driven by a scroll timeline, palette hand-offs per chapter,
glass and grain finishing. Pages that feel flat lack the grammar, not the assets.

## 1. Entrance chapter (pick one variant, design it as chapter 0)

| Variant | Behaviour | Numbers | Module |
|---|---|---|---|
| curtain + progress | solid curtain, tracked wordmark, 1 px progress line; curtain lifts, wordmark FLIPs into the header slot | line 0->100 % in 0.8-1.2 s; lift `translateY(-100%)` 0.7 s expo.in-out; hero text starts at 30 % of the lift | `loader/curtain-progress` |
| hole expand | dark screen, small aperture, % counter; aperture scales to reveal the page | scale 1->15 in 0.25-0.5 s, ease-in (accelerating); counter fades as it opens | `loader/hole-expand` |
| slab to node | full-bleed accent slab shrinks to a squircle, then docks onto a UI element and becomes it | 0.55 s expo.in-out, radius 0->28 %; hero text 0.3-0.7 s | `loader/slab-to-node` |
| debris assemble | shards/points stream in and converge on the hero object | 1.6 s expo.out, random per-shard delay 0-0.4 s | WebGL: `premium-web-webgl` |
| rain / counter | streaks plus a 100 % counter | counter 0->100 in ~1 s | practice: reuse `hole-expand` counter |

Rules: the loader waits on real asset promises (`waitFor`) plus its minimum duration; the headline reveal starts while the curtain is still leaving
(`onReveal` at ~30 % of the lift) so entrance and hero overlap; lock scroll during the entrance only; a `role=status` "Loading" for assistive tech.
Card-to-fullbleed hero (after or instead of a loader): inset card (8 vh / 8 vw, radius 28 px) expands to full bleed in 0.9 s expo.out (0.25 s was
observed; slower reads better), nav island drops in at +0.1 s. Module `fullbleed`.

## 2. Text reveals

| Name | Effect | Numbers | Use for | Module |
|---|---|---|---|---|
| blur-line | each line blurs in and rises | blur 10-12 px->0, y 16-24 px->0, 0.5-0.7 s expo.out, line stagger 100-150 ms (60-150 seen), IO threshold 0.5; exit 0.3 s | the default headline reveal (4 of 4 groups) | `text/blur-line-reveal` |
| mask-line-rise | overflow-clipped line, text rises from below | y 105 %->0, 0.8 s expo.out, 60 ms line stagger; caps 56-110 px | big caps headlines, editorial | `text/mask-line-rise` |
| word-blur | per-word blur/fade, optional scroll scrub (grey->ink) | blur 10->0, opacity 0.2->1, y 12->0, 0.6 s power3.out, 40 ms stagger | paragraphs, manifestos | `text/word-blur-reveal` |
| stagger-grid | cards/list items blur-rise | blur 14->0, y 40->0, 0.8 s, 100-120 ms stagger | card grids, stats, lists | `text/stagger-grid` |
| scramble | glyph noise locks left to right | charset `$&#@0-9A-Z`, 28 ms per char lock, tick 30-60 ms, 150 ms line stagger, block 0.7-1.0 s (random-order variant 0.5 s) | HUD labels, one signature heading per page | `text/scramble-resolve` |
| count-up | number counts up while leaving blur | 0.9 s ease-out, blur 4 px->0 | stats | `text/count-up-blur` |
| typewriter | mono type-on, block caret | 35 ms per char | nav labels, addresses, terminal-native pages | `text/typewriter` |
| word swap | rotating headline word rolls | 0.6 s expo.in-out | hero verb cycling | not in template (practice: translateY mask) |

Rules: blur only on <= 60 units per page at once; keep the original text readable for assistive tech (`aria-label` on the parent, split spans `aria-hidden`);
reserve final width (no reflow when a counter ends); keep `<br>` as a forced line break; re-split on width change. Triggers: `load` for the entrance, IO 0.5
for the rest; never both on one element.

## 3. One pinned stage + scroll timeline

The entrance and reveal effects above are time-driven. The stage is the opposite: ONE full-viewport pinned scene whose continuous state is a function of
scroll. Module `timeline` (`pinStage`): tall section (300-500 vh) with a sticky pin; damped progress 0..1 (lerp 0.08-0.1 per 60 Hz frame) written to `--stage-p`.

- Scrub with progress: object/camera keys (yaw, pitch, position, tint mix), morph amount, rail translate, shader uniform, scrubbed paragraph ink.
- Time-drive on events: palette hand-off on chapter change, text reveals on entering a chapter, stepper crossfades, hover.
- Camera keys: `[{p, yaw, pitch, pos, tintMix}]` lerped between neighbours; the same for shader palette stops. Keep 3-5 chapters.

## 4. Chapter colour hand-off

One palette world per chapter (bg, fg, accent, plus env intensity for 3D). On a chapter change the palette tweens over 0.6-0.8 s (power3.out), not per
scroll pixel; a pinned card carousel tweens the page background to each card's dominant colour in ~0.4 s. Alternate dark and light chapters through overlap
transitions (below). One global colour/camera system beats per-section backgrounds. Module `timeline` (`chapters`, `handoff`).

## 5. Section transitions

| Name | Behaviour | Numbers | Module |
|---|---|---|---|
| curtain overlap | next section slides over a sticky previous one; previous scales, dims, drifts | radius 16-28 px (top of covering panel), previous scale 0.96, shade dim 0.55 (tuned by eye), parallax 0.08 vh, soft shadow | `transition/curtain-overlap` |
| shared-element expand (FLIP) | one tile flies out and inflates to full bleed | 0.7 s power3.in-out, overshoot rotate ~8 deg, radius to 0 | practice: FLIP via WAAPI, see `loader/slab-to-node` for the pattern |
| cloud / noise wipe | blurred cloud or noise scales over the seam, doubles as a colour reset | 0.6 s, scale 1->2.4, blur 0->30 px | practice: scaled blurred layer at the chapter boundary |
| scale-to-card | hero scales into a rounded rect as the light page rises | scale ~0.9, radius 24-28 px, scrubbed | `transition/curtain-overlap` (`scaleTo`) |

## 6. Rails and steppers

- Pinned rail: section pinned; track `translateX` from 0 to `-(trackWidth - viewport)` scrubbed (~1 s smoothing); cards radius 24 px; ~1400 px of travel per 0.9 s of recorded scroll (recordings were fast; budget at least 100 vh of pin per 100 vw of travel). Template: `pinStage` `rail`.
- Pinned stepper: n steps (typically 4), title and photo crossfade 0.3 s with a brief blur, scroll-snapped slices; pagination dots. Template: `pinStage` `steps` + `[data-step]` css.
- Portfolio carousel: pinned heading, cards slide up in turn, page background tweens to each card's dominant colour (~0.4 s), counter "01/08".
- Perspective card fan (3D tilt): rotateY +-58 deg, perspective 1400 px, 0.45 s per step; use sparingly.

## 7. Chrome and finishing

| Element | Numbers | Where |
|---|---|---|
| glass card / nav island | backdrop-filter blur 24-36 px (light variant white 0.82 + blur 20), tint 15-20 %, radius 16-24 px, 1 px ring `rgba(255,255,255,.10)`; nav drops in, persists, active pill follows the section | `motion.css` `.glass`, `.nav-island` |
| cursor | ring 28-36 px, dot 6 px, follow lerp 0.1-0.2 (0.14), hover scale 1.5-2x on links and text, optional velocity squish; fine pointers only | `cursor` |
| grain | 3-10 % overlay, 6 % on dark, 3 % on paper; static tile, never animated at full screen | `motion.css` `.finish` |
| vignette, scanline, hairline guides | 6 % white hairlines, radial vignette | `motion.css` |
| HUD | small-caps mono: counters, clocks, scene index, ticks (4 of 4 in one group) | practice: `.mono` class |
| pointer coupling | lerp 0.05, tilt <= 0.3 rad, hover emissive | WebGL: `premium-web-webgl` |

Glass needs something behind it (image, shader, gradient). On a flat ground it reads as a grey box: tint from the foreground colour (`color-mix`) so it works on dark and light chapters.
