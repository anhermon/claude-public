# The signature moment ("wow")

Every page ships ONE moment a visitor would screenshot and send to someone. Not two: two compete, and the second
is usually a "nice" component promoted beyond its station. A competent interactive panel (filters, chart, table) is
the "nice" ceiling by definition: every product in the category has one. Write all of the following in SPEC.md
before any section is built. Implementation lives in the sub-skills (premium-web-webgl, premium-web-motion,
premium-web-svg, premium-web-imagery).

Contents: 1 Ideation - 2 Candidate families - 3 Acceptance test - 4 Placement - 5 Fallback and performance -
6 Proving it - 7 When it scores 3

## 1. Ideation procedure

1. **The product's verb.** One sentence: what does the product DO to its input? The wow is that verb performed
   visibly, not a picture of its output. For a non-product subject (a shop, a studio), the verb is what the
   subject does to its material (turns clay into a vessel).
2. **Enumerate at least 5 candidates**, at least one per family below. For each: one line of what a stranger sees,
   the real data or material it uses, the 1440 composition and the 390 composition.
3. **Score** each 1-5 on distinctiveness (name 3 competitors; could they have it?), truth (only real data or
   material) and scale (can it own 50 percent or more of the first viewport and be first on a phone?). Feasibility
   is scored last. Discard anything that is a panel, chart, table or card row.
4. Pick by distinctiveness plus scale; ties go to distinctiveness.
5. If after two critic rounds the wow is below 4, replace the idea; do not polish a 3.

## 2. Candidate families

| family | what it is | example move (generic) |
|---|---|---|
| data is the brand | the product's real data shape, rendered as identity | thousands of real-shaped records resolving into the one culprit as a query narrows |
| handled object | a physical or simulated object the visitor operates | a rendered dial or key that changes the page, with sound after a click |
| scroll-told scene | 3-5 beats that play the story along a scroll timeline | a request travelling through a system, one station lit per beat, all stations always drawn |
| giant physical metaphor | one large object drawn from the subject's own material | a vessel that morphs form and glaze while the wall takes its colour |
| the input transformed | the visitor's own file, text or number becomes the hero | a typed rule re-matches a sample ledger live |

The familiar chart is the floor; the wow is the step only this product can take. Make the last beat that specific
(the one culprit line pulled out of thousands, readable).

## 3. Acceptance test (written before building)

"A stranger screenshotting this would say: ___" (one concrete sentence about the subject, not about style), plus two
numeric checks, for example: the object occupies at least 55 percent of the 1440 first viewport; the first visible
result appears in under 1.5 s with no click; a numeral is at least 7 vw. Pass the sentence to the critic with
`critic.py --wow-test`.

## 4. Placement

Above the fold or the page's centrepiece. Tool and data products: at least 50 percent of the viewport width, the
product itself and never a neighbour of a headline in a small box. Object heroes may be smaller but never below 25
percent of the width and 30 percent of the height (tells.js `wow_visible`). Measured on public reference sites
(2026-10, 2026-11): one object in the first viewport, display type 4.5-5.5x body, a ground change or a bleed every 1-2
screens, no row of equal panels above the fold.

## 5. Fallback and performance (hard)

- Write the fallback frame first: the reduced-motion or no-WebGL poster states the claim on its own and scores at
  least 3 by itself. Freeze on the most informative beat, not the resolved last frame.
- 60 fps on a mid phone; cap DPR (1.5 touch, 2 desktop); pause on IntersectionObserver exit and `visibilitychange`;
  no per-frame allocation. Slow-frame watchdog: if more than 60 of the first 90 frames take over 24 ms, show the poster.
- Testable fallback flags: `?rm`, `?nogl`, `?savedata`, `?slow`; set `html[data-wow="live|poster"]` and
  `data-wow-why` so the capture script reports which path ran.
- The poster is the LCP element; the live layer fades in after its first frame. Lighthouse mobile performance at
  least 90 with the wow on.
- Audio only after a user gesture with a visible mute; procedural audio needs a human ear before shipping.
- Scroll-driven CSS (`animation-timeline`) is not available in older mobile Safari: drive scenes from
  IntersectionObserver plus a passive scroll listener writing one CSS variable per frame.

## 6. Proving it

`WOW=<selector> node scripts/chrome-shot.mjs <url> <out> 1440,390` captures mid-animation frames (7 time-spaced
frames from 250 ms to 4.5 s for a hero that animates on load or after `WOW_ACT=<js>`; for a `[data-scene]`,
every beat boundary at 250 ms and 700 ms into its transition). Run again with `RM=1` for the fallback frames. LOOK at
every frame, then run `critic.py --wow`. The payoff beat's mid-frame must be its own composition (old and new state
visible at once), not the quietest frame. GPU capture of WebGL needs a real GPU path in headless Chrome
(`--use-angle=metal` on macOS, `--ignore-gpu-blocklist`), otherwise frames come out blank (qa-loop.md).

## 7. When it scores 3

3 means "nice": a competent component of the kind every product in the category has. Go back to step 2 of the
ideation with a different family. Check also that the scene is not judged at rest: motion polish (easing, settle,
no ghosted double-exposed headlines, no particles over text, glow that never muddies labels, half-drawn states that
look intentional, one focal motion at a time) is scored from the middle frames.
