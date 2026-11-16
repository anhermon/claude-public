# The signature moment ("wow")

> **v2 (2026-10-04) supersedes "Ideation procedure" below.** Why: the fixmap redesign had a real data-is-brand
> idea (parse ELF, draw segments) and still read "basic, no wow", because (1) the idea was picked from only 3
> candidates scored on *feasibility*, so it settled on the cheapest competent panel; (2) nothing forced it to be the
> page's biggest, first-viewport object; (3) it had no written acceptance test, so "nice" passed as done; (4) the
> critic's `--wow` was optional. All four are fixed below and in `scripts/critic.py` (wow required, < 4 fails the page).

## Mandatory WOW ideation (write all of it in NOTES.md before any section is built)

1. **The product's verb.** One sentence: what does this product DO to its input? (fixmap: takes a build, finds which
   native libs sit off a memory-page grid.) The wow must be that verb performed visibly, not a picture of its output.
2. **Enumerate >= 5 candidates**, at least one per family: *data-is-brand*, *handled object*, *scroll-told scene*,
   *one giant physical metaphor drawn from the product's own material*, *the input transformed live* (visitor's own
   file/URL/text/number becomes the hero). Each: one line of what the stranger sees, the real data it uses, the
   1440 and 390 composition.
3. **Score** each 1-5: distinctiveness (name 3 competitors; could they have it?), truth (only real data), scale (can it
   own >= 50% of the first viewport at 1440 and be the first thing at 390?), feasibility last. Discard anything that is a
   panel, chart, table, or card row: that is the "nice" ceiling by definition. Pick by distinctiveness + scale.
4. **Acceptance test (measurable, written before building)**: "A stranger screenshotting this would say: ___" (one
   concrete sentence about the product, not about style) plus 2 numeric checks (e.g. occupies >= 55% of the 1440 first
   viewport; first interaction produces a visible result in < 1.5 s with no click-through). Pass it to the critic:
   `critic.py <dir> --wow wow --wow-test "<sentence>"`.
5. **Placement**: above the fold or the page's centrepiece. Tool/data products: >= 50% viewport width (Stripe, Linear); object
   heroes may be smaller (approved pebble's clay stack is 26% wide) but never < 25% wide x 30% tall (tells.js `wow_visible`). It is the product itself (Stripe: the live checkout; Linear: the real app at full width), never a
   neighbour of a headline in a 400px box.
6. **Poster first** (unchanged): reduced-motion frame states the claim alone.
7. If after two critic rounds wow < 4, **replace the idea**, do not polish it.

Measured exemplars (2026-10-04; `measure-site.js` SUMMARY=1 at 1440 plus screenshots; Stripe's reported 32px h1 is a hidden
element, its visible hero h1 is ~58px by screenshot): **linear.app** h1 64px/510 vs body 14px = 4.6x, display 48px h2, section
padding 128px, the real app UI is a 1320px (92%) frame bleeding below the fold; **resend.com** h1 96px serif (domaine) vs body
18px = 5.3x, black ground, one rendered 3D object ~35% wide, section padding 96px; **stripe.com/payments** live believable
checkout UI on the right 50% of the first viewport plus a full-bleed gradient wedge crossing the fold, section heights 289-703px
(rhythm varies); clickhouse.com giant centred type, one yellow accent, then a full-width proof wall. Common: ONE object (the
product itself or one rendered thing) in the first viewport, display type 4.5-5.5x body, ground changes or a bleed every
1-2 screens, no row of equal panels above the fold.

## Original procedure (still valid as the family list)

Every page ships ONE moment a visitor would screenshot and send to someone. Not two: two compete, and the second
one is usually a "nice" component promoted beyond its station. A competent interactive panel (filters + chart +
table) is the **"nice" ceiling** (Meridian, gallery/nice-not-wow-meridian-logpanel): every product in the category
has one. The critic scores this with `critic.py <dir> --wow wow` and it must reach 4/5.

## Ideation procedure (do it in writing, log it in NOTES.md)

1. Write the page's one claim in a sentence. The wow must **demonstrate that claim**, not decorate the page.
2. Generate **3 candidates**, each from a different family:
   - **the data is the brand**: the product's real data shape, rendered so it becomes the identity (anhermon: an
     8-span agent run drawn as light strands, frame hash shown);
   - **a physical or simulated object** the visitor handles (halcyon: a brass dial that changes the music; pebble:
     an invoice slider that fills the tax jar with the real arithmetic);
   - **a scroll-choreographed scene** that plays the product's story in 3-5 beats (a request travelling through
     the system, a line of log becoming a fact, a secret becoming a reference).
3. Score each 1-5 on **distinctiveness** (could a competitor's page have it? search your memory of 5 competitors),
   **truth** (does it show something the product really does?), **feasibility** (one day, 60fps on a phone,
   a static fallback that still says the claim). Pick the highest total; ties go to distinctiveness.
4. Write the **fallback frame first**: the reduced-motion / no-WebGL poster must state the claim on its own
   (critic scores it; >= 3).

### Starter candidates by style (do not copy; use them to calibrate ambition)

| style | candidate A (data = brand) | candidate B (object) | candidate C (scene) |
|---|---|---|---|
| Swiss / data | thousands of real-shaped log lines falling into place as the query narrows, the spike resolving into the one culprit line | a precision instrument (a ruler/loupe) dragged over a chart to read exact values | a request crossing the grid, each service a column, latency drawn as distance |
| terminal-native | a real recorded session replayed with true timing, with the brand world reacting outside the window | a physical keyboard/key you press that runs the command | a secret travelling from keychain to process with the value scrubbed on the way out |
| tactile consumer | money as soft-body objects that pile, split, settle (physics) | the app's phone UI you can operate | a month of invoices raining into jars |
| cinematic / creative | full-bleed shader landscape driven by the product's own output (audio, weather, motion) | a rendered device whose controls work | a slow scroll film in 4 shots |
| blueprint / engineering | exploded isometric of the pipeline that reassembles on scroll | a scrubbable flight-recorder timeline | a ticket travelling router -> runner -> gate -> PR |

## Implementation recipes

| recipe | file | use for | tested |
|---|---|---|---|
| WebGL line strands (raw WebGL1, no lib, ~4KB) | `assets/skeleton/hero-strands.js` | flows, traces, light, fibres | yes: Chrome 1440/390, Simulator, all 5 fallbacks |
| Scroll scene (sticky stage + IntersectionObserver steps + rAF progress) | `assets/recipes/scroll-scene.js` | 3-5 beat stories; works on iOS Safari < 26 | yes (acceptance concepts) |
| Canvas 2D particle field (thousands of points, typed arrays, eased targets) | `assets/recipes/particles.js` | "the data is the brand" | yes (Swiss acceptance concept) |
| SVG path draw / morph | inline: `stroke-dasharray: L; stroke-dashoffset: calc(L * (1 - var(--p)))` driven by scroll-scene's `--p` | diagrams that build | yes (acceptance concepts) |
| Audio-reactive | WebAudio `AnalyserNode` -> canvas; AudioContext created ONLY inside a click handler; visible "Sound off" toggle | music, voice, creative tools | no (halcyon did it; not in this skill's tests) |
| Physics object | hand-written verlet (positions + previous positions, constraints, 3-4 iterations) | tactile consumer | no |

Choose libraries only when the hand-written version would exceed ~300 lines: OGL (~25KB) for multi-pass shaders,
Matter.js for real rigid bodies. Load from cdnjs/jsdelivr only if self-hosting is impossible.

## Performance and fallback rules (hard)

- 60fps target on a mid phone. Cap DPR (1.5 touch, 2 desktop). Pause on `IntersectionObserver` exit and
  `visibilitychange`. Typed arrays, no per-frame allocation.
- Slow-frame watchdog: if > 60 of the first 90 frames take > 24ms, stop and show the poster (Low Power Mode).
- Static fallback paths, each testable with a URL flag: `?rm` (reduced motion), `?nogl`, `?savedata`, `?slow`.
  Set `html[data-wow="live|poster"]` and `data-wow-why` so `chrome-shot` reports which path ran.
- Respect `prefers-reduced-motion`: show the final, fully-labelled state, not a blank stage.
- iOS Safari: scroll-driven CSS (`animation-timeline`) only exists from iOS 26; drive scenes with
  IntersectionObserver + a passive scroll listener writing one CSS variable per frame (scroll-scene.js does this).
- The wow must not cost the LCP: the poster is the LCP element; the live layer fades in after its first frame.
- Lighthouse mobile performance >= 90 with the wow on.

## Proving it

`WOW=<selector> node scripts/chrome-shot.mjs <url> <out> 1440,390` captures mid-animation frames: 7 time-spaced
(250ms to 4.5s) for a hero that animates on load or after `WOW_ACT=<js>` (a click, a replay); for a `[data-scene]`,
beat 1 at rest, every beat boundary at 250ms and 700ms into its transition, then the end (8 frames for 4 beats); the critic scores motion polish from them (motion.md
checklist) and fails a wow whose middle frames are messy; run it again
with `RM=1` for the fallback frames. Then `python3 scripts/critic.py <out>/sections --wow wow`. The critic is
asked "would someone screenshot this and send it to a colleague?" and must cite evidence. A 3 means "nice": go
back to step 2 of the ideation, do not polish the 3.

The payoff transition must be the best frame, not the quietest. sealref r7 scored 3: the key-becomes-redacted idea
was "screenshot-worthy" but the captured frames showed only settled states and a generic particle swoosh between
them. Make the payoff beat's mid-frame its own composition (the old state and the new state visible at once, e.g.
half the glyphs still the red key, half already the token, meeting at the boundary).

Plumb r5 lesson: a data-is-brand scene whose payoff is "dots become a histogram" scored 3 ("a familiar pattern
in observability products"). The familiar chart is the floor; the wow is the step only this product can take
(the scene ends on the one culprit line, readable, pulled out of the 2,400). Make the last beat that specific.
