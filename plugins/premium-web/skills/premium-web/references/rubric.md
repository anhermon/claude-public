# Premium vs placeholder: the section rubric

This file is the standard. `scripts/critic.sh` pastes it into the critic's prompt verbatim, so every rule here
must be checkable from screenshots. Anchors live in `gallery/` (960px webp, real screenshots from our own work).

## The bar

A premium page is premium **in every section**, not just the hero. Each section has one designed visual moment
that **explains that section's claim**. One of the sections carries the page's **signature moment** (the "wow"):
the thing a visitor stops on and shows someone.

A section's visual moment is one of:
1. **Real product UI rendered in code** with believable, specific data (names, numbers, states, timestamps), at
   readable size, showing a state change or a decision, not a resting screen.
2. **A diagram with real labels, annotation and state**: the actual paths, values, counts, pass/fail outcomes.
   A reader can learn the claim from the figure alone.
3. **A generated image chosen for what it communicates**, overlaid with a real data label, and passed by critic.
4. **A live micro-demo**: something the visitor can press, drag, replay, or type into, with a visible result.

**No section is exempt**: the access/CTA section and pricing are sections too (Plumb r5: a form beside three text
rows scored explanatory 1; a calculator with an empty left column scored density 2). The CTA section shows what
happens after you press the button as a figure (a dated timeline with the real artefacts: the endpoint, the first
searchable line, the deletion letter) and its form reacts to input (choosing a volume updates an estimate). Pricing
shows the cost across the range (a curve with the current point marked), not only the current total. The footer is
chrome and is judged at page level only.

**Layout rhythm**: never more than two consecutive sections with the same shape (headline-left + figure-below is the
default trap). Across the page use at least three shapes: full-bleed figure, split figure|text, inverted colour
block, inset close-up. One section on an inverted ground (dark or a deep MUTED colour, never a full-strength primary: see Saturation and restraint) breaks the "one beige sheet".

**Annotation collisions are polish failures**: labels crossing bars, a card covering an axis label, text clipped
at 390. Place labels by measuring (`ctx.measureText`, `getBBox`) and clamping to the frame; reconcile every number
that appears twice (an alert card's 58 vs a chart peak of 57 needs both labelled for what they count).

Minimal and Swiss styles are not exempt. They get richness from precision instead of decoration: typographic
detail (tabular numerals, real units, fine annotation, leader lines, callouts), real data, texture, depth, and
state. Absence is not minimalism.

**Craft gates (tells.js `craft_fail`, fail the page)**: >3 consecutive bordered-panel sections; fewer than 2 scale-change
sections below the hero; largest type < 4x median; no wow object >= 50% wide in the first viewport. Details and
escape moves: references/genre-escape.md.

## Ban list (any hit fails the section)

- **Uniform panel grid / dev-tool template**: sections whose container is a hairline-bordered box (mono or not) on one ground, section after section.

- **Stick-figure schematics**: a few hairlines, boxes or bars standing in for a concept, with no labels, no values,
  no state. Thin line art, generated or hand-drawn. (gallery: reject-meridian-method, reject-thin-line-art)
- **Bare hairline-and-text**: a heading, rules and grey paragraphs with no visual that explains anything.
- **Decorative numbering**: 01/02/03 where order carries no information. Numbering is fine only when the steps
  are a real sequence and the visual shows that sequence (anhermon v4 Observe -> Pin down -> Guard is a real
  method order, and each step has its own explaining figure).
- **Whitespace as content**: a section where more than half the 1440 frame is empty and nothing in the remainder
  explains the claim. Scroll scenes count beat by beat: a stage that shows one string per beat on an otherwise empty
  canvas fails (sealref r7 top: "one-string-per-step figure"). Keep the whole diagram on stage in every beat (all
  stations drawn and labelled, the current one lit) and move the subject between them.
- **A list with connector lines**: needs on the left, answers on the right, curves between them. It is still a list
  (sealref r7 alternatives: explanatory 2). Comparisons are a matrix of real attributes with filled, empty and
  "not stated" cells, and the subject's row is the one the reader's eye lands on.
- **Status as decoration**: a bar or chip per item that encodes one bit (sealref r7 platform bars: density 2). Show
  the evidence grid (what ran, against what, with which result) or the before/after output.
- **Captured mid-load**: a replay, typing or counter shown dimmed, empty or at frame zero in its resting screenshot
  (sealref r4 replay: hierarchy 2, polish 2). Its resting state is the complete, readable result; play is opt-in.
- **Interchangeable cards**: identical cards whose content could swap without anyone noticing. Cards are fine when
  each carries distinct, specific evidence (anhermon v4 proof cards each have their own licence, release, and an
  amber Limit callout quoting the README).
- **Literal-metaphor images** that need a caption to make sense (gallery: reject-guard-steel-slab: "this image is
  weird"), stock fibre-optic or glowing-brain imagery, circuit boards.
- **The rejected type direction**: condensed display serif or tight condensed grotesk with uppercase mono eyebrows
  and an italic accent word (gallery: reject-anhermon-03364e9-serif-mono).
- **Toy palette** (Angel on ember v3: "oversaturated, feels like a game / toy, doesn't give a premium feeling"): playful
  primaries (pink, blue, yellow, red) at full saturation across big areas, rainbow overprint, sticker/pill colour
  everywhere. See "Saturation and restraint" below; `scripts/saturation.py` measures it. (gallery: reject-ember-v3-toy-*)
- **Fabricated proof**: numbers, logos or testimonials that are not real. Sample data must say it is sample data.

## Templaty tells (page level; Angel rejected ember "generic AI templaty" with Lighthouse 100)

Metrics cannot catch these. `scripts/tells.js` detects the structural ones in the DOM; the critic judges the rest.
A page with **4+ DOM hits fails** (calibrated 1440 / 390 on a fully revealed page, 13 detectors: rejected ember r1 9 / 7 (pinned at commit
dc9a1ed), ember r2 "mid" 6 / 4 (commit 97486ed), meridian 5 / 4; approved pebble 2 / 3, halcyon 2 / 2; acceptance
pages Plumb 0 / 0, sealref 1 / 1). With the 13th detector `saturated_fields` (2026-10-02, 1440 / 390): pebble-v2 2 / 3, halcyon-v2 2 / 2, tracer 4 / 3 (its own
equal_card_grids + caps + mono_panels + no_fullbleed; approved by Angel, so the 4-hit rule is a flag for the critic to look hard, not an absolute), ember v3 4 / 3 and
only it hits `saturated_fields` (3 toy sections); approved pages never do). The scan scrolls
the page first: unrevealed `[data-r]` content at opacity 0 reads as "no media" and inflates hits. Calibrate
against pinned snapshots, not live concept dirs that other work keeps changing.

| tell | how it is detected | what approved pages do instead |
|---|---|---|
| repeated equal card grids (3-4 bordered boxes, same size, no media) | tells.js `equal_card_grids` | pebble's 3 cards each have their own colour block and clay render |
| ALL-CAPS tracked micro-labels on everything | tells.js `caps_micro_labels` (>12, or >=2 in most sections) | one label voice used sparingly; halcyon uses them but under full-bleed imagery |
| bracketed nav gimmicks `[how] [config]` | tells.js `bracket_nav` | plain nav words |
| one-note palette: mono background + one accent, no depth | tells.js `palette` (1 hue AND <2 images below hero) | pebble: 3+ colour blocks; halcyon: one accent but film-grade imagery carries colour |
| no photographic, rendered, illustrative or generated material | tells.js `material` (no >=200px img/canvas/video/svg/bg-image below hero) | clay renders, film stills, a rendered brass dial |
| generous-but-empty spacing | tells.js `empty_spacing` (<30% of a section's grid covered) | space framing an object, not space instead of one |
| monospace body copy | tells.js `mono_body` (>60% of paragraphs) | mono only for code, data and terminal |
| timeline list beside a mono command panel (Angel on ember r2's revisions section: "looks bad") | tells.js `timeline_code_split` (a 3+ item list side by side with a bordered mono panel in one section) | show the change itself: a drawn diff, a version strip with what moved, a before/after |
| bordered mono panels in every section (the "terminal card" as the default container) | tells.js `mono_panels` (bordered/filled box whose text is mostly mono in >= 60% of sections) | at most one or two real terminal moments; the rest are drawn figures, type and imagery |
| no full-bleed moment: every section sits in the same centred column | tells.js `no_fullbleed` (no visual or typographic element >= 95% of viewport width and >= 40% of its height below the hero, and no contrasting full-width section carrying media or display type) | **required**: at least one section per page is a full-bleed typographic or drawn moment (a giant number, a full-width figure, an edge-to-edge render) |
| fully saturated big fields: playful primaries as grounds, toy / game look (Angel on ember v3) | tells.js `saturated_fields` (>25% hot-colour grid in 2+ sections or >15% on average) + `scripts/saturation.py` on shots + critic ban "Toy palette" | muted neutral grounds, one small spot colour, material and craft carry the wow |
| category cliches: `curl | sh` install box, "no daemon / no telemetry" principle cards, "blazing fast", "zero config", "seamless" | tells.js `cliches` (2+) | a real product replay that shows the claim |
| headline-then-3/4-cards, section after section | critic | each section changes shape |
| sections could swap places without changing meaning | critic `sections_interchangeable` | each section answers the next question a visitor has |

**Distinctiveness test** (the critic's page question): cover the brand name. Could this page belong to 20 other
products in its category? If the critic can name two lookalikes, the page fails.

## Saturation and restraint (premium reads as calm; toy reads as loud)

Angel rejected ember v1/v2 (full-bleed amber slab, mono everything) and ember v3 (pink/blue/yellow primaries as full
grounds: "oversaturated, feels like a game / toy") while approving pebble, halcyon and tracer. The rule, from that
evidence:
- **One or two saturated colours per page, at small area** (a spot colour on a rule, a mark, a figure's key line, one
  button). **Large fields stay neutral or low-chroma**: paper, stone, near-black, desaturated ink, a deep muted ground.
- **Never fill big areas with a full-strength primary** (HSV S > .72 at V > .5). Approved colour blocks (pebble clay)
  sit at S .60-.70 and come with material (renders, soft light); flat full-saturation fields read as a toy.
- **No rainbow**: three or more chromatic hues visible at once is a toy unless the work is colour itself (a printer's
  swatch book) and the hues are muted.
- Overprint / multiply / tint effects use tints (10-35% of a muted ink), not three full inks multiplied.
- Premium comes from craft instead: type precision, hairlines, fine print detail, real data, material, motion
  easing. Take colour out first, then check the page still has a wow; if it does not, the idea was the colour.
- Photographic or filmic imagery (halcyon's dusk sea) can carry colour: judge it by the critic, not by the number.

Measure: `python3 scripts/saturation.py <shots...>` prints, per screenshot, the share of pixels that are hot
(S > .72, V > .5) and a TOY / LOUD / ok verdict; exit 1 when the mean share of the inputs is > 0.12. Calibration
(share of screenshot area, 1440 viewport shots): approved pebble v2 0.00, halcyon v2 0.00, tracer 0.01; rejected
ember v2 0.14 (amber slab section 0.58), ember v3 0.19 (drift section 0.64, hero 0.17). `critic.py` runs it on
every section and on the page's wide shots, and fails a section above 0.20 or a page whose mean exceeds 0.12.
tells.js `saturated_fields` is the DOM twin (>25% of a section's grid on a hot background in 2+ sections).

## A wrapper / showcase page has an identity of its own

A site that presents other sites (portfolio, gallery, case-study index, directory) must not inherit the author's own
site styling (Angel on hc-folio: "the wrapper is using the styling of anhermon.dev and doesn't feel like a portfolio").
Give the wrapper a neutral, deliberately different identity (its own type pairing, palette, grid, nav) so the sites it
shows are the content, and write that identity down in intake before building. Check: put the wrapper's hero beside
the author's own site; if one could be mistaken for the other, it fails.

## Approved vs rejected gallery (gallery/, the critic compares against these)

| file | verdict | Angel's words / why |
|---|---|---|
| approved-pebble-hero, approved-pebble-jar-maths | APPROVED | tactile fintech: clay renders, colour blocks, a phone UI in code with named invoices, a slider that fills the jar with real arithmetic |
| approved-halcyon-hero, approved-halcyon-instrument | APPROVED | cinematic: film-grade sea at dusk, Bodoni display, a rendered brass dial you can turn, sound on click |
| accept-anhermon-v4-* | SHIPPED | see per-section table below |
| reject-ember-hero-terminal, reject-ember-principles-cards | REJECTED | "not good, generic AI templaty": amber mono everything, bracket nav, `curl | sh` box, four identical principle cards, half-empty terminal |
| reject-ember-v3-toy-hero, reject-ember-v3-toy-fullbleed | REJECTED | "oversaturated and feels like a game / toy, doesn't give a premium feeling or a wow factor": pink/blue/yellow primaries as grounds and as three multiplied sheets, a full-bleed pink slab with blue below, pill chips and offset-shadow cards (the registration concept itself was liked) |
| reject-meridian-method | REJECTED | "a template with stick-figure placeholders": hairline sketches, 01/02/03, grey text |
| nice-not-wow-meridian-logpanel | NICE, NOT WOW | "it's nice, but it's missing a wow factor": competent log panel every log product has |
| reject-anhermon-03364e9-serif-mono | REJECTED | serif + mono eyebrows + italic accent word: read as AI-generated |
| reject-guard-steel-slab | REJECTED | "this image is weird": literal metaphor photo; replaced by the code-drawn allowlist |
| reject-provenant-gold-plate | REJECTED | "looks terrible - you don't create a luxurious feeling by writing 'luxury' or putting the price at the front, or covering everything with gold"; "show real products, not concept": brass plate hero with price range as the headline, concept marks instead of goods (styles.md luxury retail) |
| reject-provenant-v2-beige-boxes | REJECTED | "it still doesn't look good": warm paper + Cormorant default, small packshots floating in large beige boxes (one box rendered empty), beige-on-beige, product links sending buyers to the supplier, two off-story products; no campaign concept, no discovery path (styles.md e-commerce) |
| reject-thin-line-art | REJECTED | generated hairline diagram: says nothing, same disease as the Meridian method sketches |

## Scores (1-5, each with visible evidence)

| criterion | 5 | 3 | 1 |
|---|---|---|---|
| distinctiveness | could only belong to this subject; a specific idea | competent, generic for the category | template |
| explanatory_visual | figure alone teaches the claim, with real labels/data/state | visual present but decorative or vague | none, or placeholder schematic |
| density_detail | rewards a second look: annotation, real values, texture, states | some detail, large inert areas | sparse lines and grey text |
| hierarchy | one obvious focal point, then headline, then evidence | readable but flat | competing or absent focus |
| polish | aligned, crisp, consistent type and spacing at 1440 AND 390 | minor misalignment, cramped mobile | broken layout, overflow, clipped text |

Scale mapping: 1-5 here, and 4 = 7/10 (the "7/10 and above" bar in briefs). The critic's rule is below; the old
"all five >= 4" was unreachable for approved pages (see critic.py `verdict`).

A section **passes** when every score is >= 4, explanatory_visual is present, and ban_hits is empty.
`critic.sh` computes pass/fail itself from the scores; it does not trust a model's verdict.

## Wow (page level, scored once, on the signature section)

Question: **would someone screenshot this and send it to a colleague?** Score 1-5 with evidence.
- 5: a moment with no obvious precedent in the category, tied to the subject (anhermon v4: the hero light strands
  are drawn from an 8-span run, replayable, "same seed, same frame" with the frame hash shown).
- 3: "nice": a competent, conventional component done well. Meridian's interactive log panel (filter + histogram +
  table, gallery: nice-not-wow-meridian-logpanel) is the 3 ceiling: good, but every log product has it.
- 1: nothing a visitor would remember.
Pass: >= 4, and **a wow below 4 fails the whole page regardless of every other score** (a page of 4s with a wow of 3 is a polished template: fixmap r2). Judged against the page's written acceptance test (wow.md v2). The reduced-motion / poster frame must still score >= 3 on its own (the fallback is part of the work).

## Concrete standard: what anhermon v4 does per section (measured from frontpage-v4/after shots)

| section | visual moment | why it passes |
|---|---|---|
| hero | WebGL light strands through glass panes, poster fallback; caption row "agent.run · 8 spans · 4.82s", "run 1 · frame 88f9c8af", Replay run button | signature: subject-derived, replayable, honest caption ("illustrative 8-span run") |
| 01 Observe | generated 4:5 plate (blue light along a row of pins) overlaid with real span labels `plan 0.43s`, `llm.chat 1.31s`, `tools/call fetch timeout` + tool chips | image picked for what it says; data labels make it specific |
| 02 Pin down | dark textured plate, two converging strands, typography "run 1 / run 2 / diff 0" | one number states the claim |
| 03 Guard | code-drawn allowlist: the real 15 GET paths, `POST /api/Orders/SendOrder` pill hitting it, `ValueError` line, 4-cell outcome grid incl. the server's own misspelling "Summery" | a reader learns the rule from the figure; a photo was tried and rejected |
| proof | 5 repos, each with real licence/release/stars-with-date and a quoted Limit | distinct evidence per card |

Before -> after: commit 03364e9 (serif + mono eyebrows + italic accent, waterfall table) was rejected as
"AI-generated looking"; v3 (Bricolage condensed, steel-slab guard photo) rejected; v4 shipped (Inter, measured
scale, code-drawn Guard). The Meridian method section (gallery: reject-meridian-method) is what "template with
stick-figure placeholders" looks like: three hairline sketches, 01/02/03, grey text.
