# Direction: style, genre, type and palette as decisions

Countermeasure for F1, F4 and F5 (failure-modes.md). Every section below is a procedure that ends in a written
decision in SPEC.md. A default you did not decide is the genre average.

Contents: 1 Choose the style - 2 Genre attractors - 3 Banned defaults - 4 Type: the measured method - 5 Type rules -
6 Palette restraint - 7 Finish - 8 Reference gap check

## 1. Choose the style

1. Name the subject and what a visitor must feel (calm, precise, tactile, cinematic, authoritative).
2. Pick ONE row below that serves the subject; do not blend two. The row decides what carries the richness.
3. Pick the asset class per row (code / procedural / media) and write it in the asset plan.

| style | richness comes from | asset class | common failure |
|---|---|---|---|
| Swiss / data | precision: tabular numerals, real units, a visible asymmetric grid, hairlines of two weights | code-drawn figures from real-shaped data | sparse hairline sketches and grey text |
| terminal-native | a recorded real session replayed with true timing, a brand world around the window, large box-drawing diagrams | code, plus one world plate | the category-average dark page with a typing animation |
| tactile consumer | colour blocks with material, soft objects under one light, a UI drawn in code doing real arithmetic | generated or rendered objects (one set) | gradient blobs, stock 3D emoji |
| cinematic / creative | film-grade imagery or shader, one light direction, slow reveals (0.8-1.2 s), high-contrast display serif | shader or generated stills | colour that carries the whole idea |
| editorial dark product | one neutral sans at a measured scale, one accent, plates with real data labels | mixed | serif plus tracked mono eyebrows plus an italic accent word |
| e-commerce / storefront | one category, one campaign world, real product photos on one plate colour, a finder, on-site quick view | media (real products), scenes labelled illustration | tiny packshots in large tinted boxes, concept metaphor replacing taxonomy |
| blueprint / engineering | drafting grid, dimension lines, isometric exploded drawings, revision blocks | code / SVG | neon on black |
| type-led / portfolio | giant cropped type as the image, one photograph or shader, glass chrome | procedural plus one asset | the same layout for every project |

Storefront rules that held up: one category a buyer shops as one thing; one message per section; products
normalised onto one plate colour at 40-55 percent fill (65-75 percent in the single hero moment); price as a small
caption after the name; no "luxury / premium / exclusive" words; no gold or metallic fills; scenes labelled.

## 2. Genre attractors

Write "left alone this page becomes ___" (spec-before-code.md section 3). Known attractors and the escape:
- **Dark developer tool**: graphite ground, hairline mono panels, one orange or green accent, numbered steps.
  Escape: change the ground (light or muted saturated hero field), put the product at 50 percent or more of the
  width instead of in a card, display type at 8 vw or larger once, drawn figures that bleed to the edge.
- **Data / docs**: tables, bars, chips. Escape: one navigable visual field (all N items as one map), tables only
  as evidence.
- **Centred SaaS**: centred h1, two buttons, logo row, three cards. Escape: asymmetric hero, the product as hero.
- **Editorial cream plus serif**, **gradient glass**, **terminal cliche**: same test; the escape is a changed
  ground, scale or subject, never a different accent colour.
If your direction equals the attractor you have not chosen one.

## 3. Banned defaults (an external reference unlocks one; a sentence does not)

- Scope: this list governs pages you build. The sub-skill templates use a neutral system-font placeholder so they
  run offline; they demonstrate mechanics, not finished design. Replace it (`scripts/get-font.sh`) before shipping.
- Type: the family that is the modal choice (Inter, Roboto, Arial, system stack as display, Space Grotesk,
  Poppins, DM Sans, Plus Jakarta Sans, Geist, a tight condensed grotesk for everything); condensed display
  serif plus uppercase tracked mono eyebrows plus an italic accent word.
- Layout: centred hero with two buttons; three equal bordered cards; logo strip with invented logos; numbered 01 / 02 / 03
  steps without a real sequence; bracketed nav `[how] [config]`; blinking-cursor-only hero.
- Surface: default box-shadow, flat panels as finish, blurred gradient blobs, glowing-brain or circuit imagery,
  literal-metaphor photos that need a caption.
- Palette: mono ground plus one accent with no material; warm beige plus serif as a default; full-strength
  primaries across large areas; three or more chromatic hues at once.
- Copy: "seamless", "blazing fast", "supercharge", "zero config", "all-in-one".

## 4. Type: the measured method

Do not pick sizes from memory. Measure, then decide.
1. Pick 6-12 live references for THIS direction (not the category average).
2. Run `scripts/measure-site.js` on each at 1440 and 390 (headless: `EVAL=scripts/measure-site.js SHOTS=0 node
   scripts/chrome-shot.mjs <url> <out> 1440,390`, or paste into a browser tool). It reports h1, h2, body and nav as
   family, px, weight, line-height, tracking, transform, plus header height, button size and section padding.
3. Tabulate; compute display-to-body ratio, weight contrast, tracking by size and padding rhythm.
4. Write the chosen values in SPEC.md with one line on which references justify them.

Ranges measured from public product sites (2026-10, about 11 sites, plus 2026-11 recordings; +-10 percent):
- h1 48-96 px desktop, 34-48 px phone; body 14-20 px; display-to-body ratio 4.5-5.5x on UI-led pages; type-led
  pages crop a wordmark at about 38 percent of viewport height or larger.
- Weights: 300-600 for display (light display with tight tracking is common on dark pages), 400-500 body.
- Tracking at display sizes: -0.015 to -0.05 em (neutral grotesks about -0.022 em at 32 px or larger; display
  serifs need less); body 0 to -0.011 em.
- Line-height: display 1.0-1.08, h2 1.1, body 1.35-1.6. Section padding 80-160 px desktop, 32-112 px phone.
- Header 44-78 px; primary button 32-48 px tall.

## 5. Type rules

1. One family carries the page; a second face only as a deliberate voice (a display serif, a mono for the tool's
   own output). 11 of 11 measured product sites use one sans for everything.
2. Mono is for code, data, paths and terminal output. Mono body copy and mono labels everywhere are a tell.
3. Sentence case for headings, buttons, nav. Tracked uppercase micro-labels: at most one per section, ideally none.
4. Check collisions at 1440 and 390: descenders into the next line, kerning gaps at 100 px or larger.
5. Self-host a latin woff2 subset: `scripts/get-font.sh <fontsource-id> fonts` (refuses non-open licences, prints
   `@font-face`). Preload the one face above the fold. The chrome-shot report lists the font actually rendered per
   selector; "(system)" on the h1 means your font did not load.
6. Density varies: some sections are one sentence at display size, others are dense.
7. Size mono labels at 12 px or larger on phones (a legibility audit penalises smaller).

## 6. Palette restraint (premium reads as calm; toy reads as loud)

- One or two saturated colours per page, at small area (a rule, a mark, a key line, one button). Large fields stay
  neutral or low-chroma: paper, stone, near-black, desaturated ink, a deep muted ground.
- A neutral surface ramp (for example three steps of near-black) with hairlines at 8 and 16 percent of the ink;
  all colour comes from content, the subject and light.
- Never fill big areas with a full-strength primary (S > 0.72 at V > 0.5). Muted colour blocks (S 0.55-0.70) work
  when they carry material and soft light.
- No rainbow: three or more chromatic hues visible at once reads as a toy unless colour is the subject.
- Tints (10-35 percent of a muted ink) for overprint and multiply, not full inks.
- Per-chapter grade: shift the ground, accent and environment together over 0.6-0.8 s per chapter.
- Take colour out first and check the page still has its wow; if not, the idea was the colour.
- Measure: `python3 scripts/saturation.py <shots...>` (hot-pixel share; thresholds and provenance in the script).
- Photographic or filmic imagery can carry colour; the critic judges it, not the number.

## 7. Finish

Decide light, grain, vignette and material in the finishing layer of SPEC.md (spec-before-code.md section 8).
Hairline 1 px at 8 percent ink; concentric radii (inner radius = outer radius minus the padding); glass (backdrop
blur 18-24 px) only on floating chrome with a 1 px inner top highlight.

## 8. Reference gap check

Before building and again before the critic: screenshot 3-5 live best-in-class pages for the direction at 1440,
put them beside your hero in one image, and write the three largest gaps (scale of the hero object, type contrast,
number of ground changes). Close them first.
