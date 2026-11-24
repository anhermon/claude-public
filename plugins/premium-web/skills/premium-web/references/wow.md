# The signature moment ("wow")

> **Marketing mode (step 0 READ).** Apps (step 0 WORK) have no wow: they are judged on signature clarity, see "App mode" below. Everything above that section is marketing only.

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
5. **Placement**: above the fold or the page's centrepiece. Pages for tool/data products: >= 50% viewport width (Stripe, Linear; the marketing gate is 25% x 30%; an app has no wow gate, see App mode); object
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

## App mode

Use when step 0 classified the deliverable WORK (an ops console, release board, trace viewer, deployment-history or test-run UI, admin). **This section replaces the wow for apps.**
Marketing mode and its thresholds are unchanged; do not use app mode for a landing page, and never size-gate or spectacle-gate a work screen.
(History: the first "tool mode" kept a wow gate for apps: a data object >= 50% x 40% of the first viewport, a 4vw display numeral and an edge-to-edge band. Real runs then
padded tools with page structure or wrapped a hero in `data-wow` to satisfy it, and nothing measured whether the task got faster. All three size gates are gone for apps; `tool` is now an alias of `app`.)

### Signature clarity (replaces the wow; judged by the critic, validated by the walk-through)

One distinctive, **truthful** way of making the product's own data legible: all N items on one field, a timeline that is also the filter, a diff drawn as the thing itself, a run as lanes of
spans. It may be small, quiet or a single well-made column; it must **shorten a primary task**. Procedure (write it in NOTES.md before building):
1. **The table baseline.** What would a plain sortable table of this data give, and how many steps does each primary task take with it? (Count it; app-mode.md section 1 walk-through format.)
2. **The sentence.** "This shows ___ as ___, which a ___ would show as a table." Concrete, about the product, not about style.
3. **Truth.** Every mark is a real record (id, state, timestamp); sample data is labelled "sample data"; counts are honest; no invented metrics.
4. **Validation by recorded numbers.** After the build, re-run each primary task and record steps, keystrokes and time-to-first-result. The signature earns its score only if at least one task is
   shorter or clearer than the baseline. A pretty field that does not shorten a task is decoration (3 at best).
5. **Do not game gates.** No `data-wow`, no hero band, no oversized numeral to satisfy a detector (`data_wow_in_app` fails the screen). If a gate asks for one, stop and report it as mismatched.
Judged by `critic.py --mode app --signature <screen> --signature-test "<sentence>"`: signature clarity >= 4, truthful, and every flow passes. A competent sidebar + table + detail panel is the 3 "nice" ceiling.

### tells.js app profile: thresholds (machine copy: `TH.app` in tells.js; the line below is asserted equal by test_tells.js)

All five new checks are hard fails (they go into `craft_fail`, which fails chrome-shot with exit 1 and the critic page). The first two columns are measured at 1440x900 on a revealed page.

| check | measured | threshold (hit = fail) | notes |
|---|---|---|---|
| `density` | rows (table rows, list items, role=row/listitem/option/treeitem, `[data-row]`, groups of >= 3 siblings) visible in the first viewport | rows < `density_target` from step 0. No target = hit with `UNVERIFIED` | screens with no list set `data-screen="form\|detail\|editor\|settings"` on `<main>` and need >= `fields` (24) visible data points instead; desktop only |
| `interactive_affordance` | pointer-cursor or role=button/link/tab/... elements that are not natively focusable and have no `tabindex` (`unfocusable`); controls with no accessible name (`nameless`); controls under `tap` (24) px (`under_min`) | unfocusable > 0, or nameless > 0, or under_min > max(2, `small_frac` (10%) of controls) | inline text links and labelled checkboxes are exempt from the size test; any width |
| `state_coverage` | distinct states among empty / loading / error / partial present as `data-state` hooks, `aria-busy="true"` or `[data-skeleton]` (loading) | fewer than `states` (3) of 4; each hook needs >= `state_chars` (8) characters of real message (loading may be a skeleton) | hidden hooks count (they are the designed states); the walk-through must make them reachable |
| `page_shaped_mismatch` | signals: `hero` (h1 >= `hero_px` 56px or a `hero` element >= 40% of the viewport), `scroll_sections` (>= 3 sections >= `tall_sec` 60% viewport tall on a page >= `scroll_vh` 3 viewports), `no_shell` (no nav/tablist/toolbar/aside with >= 2 controls that is fixed/sticky, or on a page <= `shell_vh` 1.15 viewports), `closing_cta` ("get started", "book a demo", ... in the last sections, or a footer with >= 3 link columns) | >= 2 signals, or `no_shell` on a page taller than `bleed_vh` 2 viewports | message says the gate flags WRONG-MODE STRUCTURE; desktop only |
| `data_wow_in_app` | elements (and `<html>`) carrying `data-wow` | any | `data-wow` only feeds the marketing wow gate; on an app it is detector nudging |

Kept as hard fails in app mode: `equal_card_grids`, `caps_micro_labels`, `palette` (each hit goes to `craft_fail`). `material` stays a counted tell (a table-only tool has no drawn field; the critic judges distinctiveness).
Not gated in app mode (still measured, reported with `hit:false`, `measured_hit` and `gated:false`): `type_scale`, `wow_visible`, `scale_change`, `panel_run`, and the page-rhythm tells `empty_spacing`,
`no_fullbleed`, `mono_panels` (they score the sections of a scrolling page). Mode-aware exemptions (app only; marketing unchanged, test_tells.js asserts both): `equal_card_grids` skips >= 6 equal cells or cells
<= 72px tall, `timeline_code_split` skips lists of >= 6 items, `palette` is one-note only with zero chromatic hues and no media.

<!-- app-mode-numbers (test_tells.js asserts these equal tells.js TH.app): fields=24 tap=24 small_frac=0.1 states=3 state_chars=8 hero_px=56 scroll_vh=3 tall_sec=0.6 shell_vh=1.15 bleed_vh=2 -->

## Original procedure (still valid as the family list)

Every page ships ONE moment a visitor would screenshot and send to someone. Not two: two compete, and the second
one is usually a "nice" component promoted beyond its station. A competent interactive panel (filters + chart +
table) is the **"nice" ceiling** (Meridian, gallery/nice-not-wow-meridian-logpanel): every product in the category
has one. The critic scores this with `critic.py <dir> --wow wow --wow-test "<sentence>"` and it must reach 4/5.

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
with `RM=1` for the fallback frames. Add `WOW_DELAY=<ms>` (shifts all frames; ~900 for a scroll-reveal) so the first frame is after the reveal has finished. Then `python3 scripts/critic.py <out>/sections --wow wow --wow-test "<acceptance test>"`. The critic is
asked "would someone screenshot this and send it to a colleague?" and must cite evidence. A 3 means "nice": go
back to step 2 of the ideation, do not polish the 3.

The payoff transition must be the best frame, not the quietest. sealref r7 scored 3: the key-becomes-redacted idea
was "screenshot-worthy" but the captured frames showed only settled states and a generic particle swoosh between
them. Make the payoff beat's mid-frame its own composition (the old state and the new state visible at once, e.g.
half the glyphs still the red key, half already the token, meeting at the boundary).

Plumb r5 lesson: a data-is-brand scene whose payoff is "dots become a histogram" scored 3 ("a familiar pattern
in observability products"). The familiar chart is the floor; the wow is the step only this product can take
(the scene ends on the one culprit line, readable, pulled out of the 2,400). Make the last beat that specific.
