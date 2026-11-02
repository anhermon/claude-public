# Section craft: what makes a section designed

Countermeasure for F2, F5 and F10 (failure-modes.md). `critic.py` pastes this file into the critic prompt, so
every rule must be checkable from screenshots. Thresholds are measurable and gated by `scripts/tells.js`.

Contents: 1 The bar - 2 Focal moments - 3 Rhythm numbers - 4 Annotation discipline - 5 Ban list - 6 Templaty tells -
7 Scores and pass rule - 8 Special sections

## 1. The bar

A premium page is premium in every section, not only the hero. Each section has ONE message and ONE focal moment
that carries it. One chapter carries the page's signature moment (wow.md). The persistent hero subject returns,
changed, in the chapters (spec-before-code.md section 4); a section that could be moved to another site fails.

## 2. Focal moments (pick one per section)

1. **The subject's chapter state**: the persistent object in a new form, position, camera or colour grade.
2. **A type moment**: display type at 8 vw or larger, a cropped wordmark, one giant numeral, type passing through
   or behind the subject.
3. **A media band**: a full-bleed or inset photographed, rendered or generated image in the page's light, with a
   caption or a data label that makes it specific.
4. **Real UI in code** with believable, specific data (names, numbers, states, timestamps) at readable size,
   showing a state change or a decision, not a resting screen.
5. **A live micro-demo**: something the visitor presses, drags, replays or types into with a visible result.
6. **An annotated diagram, only when the section's job is to explain a mechanism**: real labels, values and state;
   a reader can learn the claim from it alone (discipline in section 4).

Minimal and Swiss styles are not exempt: richness comes from precision (tabular numerals, real units, leader
lines, texture), not from absence.

## 3. Rhythm numbers (measured by tells.js `craft_fail`)

- **Panel run**: at most 3 consecutive sections whose main content is a bordered or filled box. Mono panels: at
  most 1 per page. Cards are fine when each carries distinct evidence or media.
- **Scale changes**: at least 2 sections below the hero that break the column: an edge-to-edge figure or render, a
  contrasting full-width ground, or display type at 12 vw or larger. "The same column with a bigger heading" does not count.
- **Type scale**: largest text at least 4x the median text; the h1 or one numeral at 7 vw or larger at 1440.
- **Ground rhythm**: alternate ground (ink / paper / muted colour) at least twice; alternate density (a dense
  figure, then one sentence at display size). Never more than two consecutive sections with the same shape.
- **Above the fold** at 1440 and 390: the wow object plus the one action; nothing else is required.
- **Wow placement**: at least 25 percent of the viewport width and 30 percent of its height starting in the first
  viewport (tells.js `wow_visible`); tool and data products 50 percent of the width or more.
- **One real data-driven visual** per page if the product has data: built from real records (all N items placed),
  with a legend and an honest count.
- **Motion tied to meaning**: motion shows a state change (an offset closing, a count running); 0.3-1.2 s; one
  focal motion at a time; reduced motion shows the final labelled state; never ambient dust.

## 4. Annotation discipline

Annotated figures failed polish in every pilot that used many of them. When a figure is justified:
- Every number that appears twice comes from ONE array or object (labels, list rows, readouts, tooltips read the
  same source); reconcile totals so a card and a chart agree and say what each counts.
- Place labels by measuring (`ctx.measureText`, `getBBox`) and clamp them to the frame; give canvas and SVG text a
  halo stroke in the ground colour; minimum 12 px at 390.
- The figure sits inside the section's first 900 px; the critic sees viewport shots only, so a figure below the
  fold scores as absent.
- Resting state is complete and readable; play is opt-in. A counter, replay or typing animation captured at frame
  zero or dimmed is a defect.
- Keep the whole diagram on stage in every scroll beat (all stations drawn, the current one lit) and move the
  subject between them; a stage showing one item per beat on an empty canvas fails.
- At most two annotated figures per page is a guideline; more needs a reason in SPEC.md.

## 5. Ban list (any hit fails the section)

- Uniform panel grid: hairline-bordered boxes on one ground, section after section.
- Stick-figure schematics: a few hairlines, boxes or bars standing in for a concept, with no labels, values or state.
- Bare hairline-and-text: heading, rules and grey paragraphs with nothing designed.
- Decorative numbering: 01/02/03 where order carries no information.
- Whitespace as content: more than half the 1440 frame empty with nothing explaining the claim.
- A list with connector lines presented as a comparison (a comparison is a matrix of real attributes).
- Status as decoration: a bar or chip per item that encodes one bit.
- Interchangeable cards whose content could swap unnoticed.
- Literal-metaphor images that need a caption; stock fibre-optic, glowing-brain or circuit imagery.
- Toy palette: playful primaries at full saturation across big areas, rainbow overprint, sticker and pill colour everywhere.
- Fabricated proof (trust.md).
- A fixed overlay or sticky element covering content at 390.

## 6. Templaty tells (page level)

`scripts/tells.js` detects the structural ones. 4 or more hits is a fail; 3 means look hard; 2 or fewer means no
structural tell (the critic still looks). Thresholds are heuristics set on a small calibration set (see qa-loop.md,
"Calibration"); treat a hit as "the critic must look here".

| tell | detector |
|---|---|
| equal card grids without media | `equal_card_grids` |
| tracked all-caps micro-labels | `caps_micro_labels` |
| bracketed nav | `bracket_nav` |
| one-note palette with no material | `palette` |
| no photographic, rendered or drawn material below the hero | `material` |
| empty spacing | `empty_spacing` |
| monospace body copy | `mono_body` |
| timeline list beside a mono command panel | `timeline_code_split` |
| bordered mono panels in most sections | `mono_panels` |
| no full-bleed moment | `no_fullbleed` |
| saturated fields | `saturated_fields` (and `saturation.py`) |
| category cliches | `cliches` |
| craft gates: panel run, scale changes, type scale, wow above the fold | `craft_fail` |

Page question for the critic: cover the brand name; could this page belong to 20 other products in its category?
Name two lookalikes or say why none exists.

## 7. Scores and pass rule

Five criteria, 1-5, each with visible evidence:

| criterion | 5 | 3 | 1 |
|---|---|---|---|
| distinctiveness | could only belong to this subject | competent, generic for the category | template |
| focal_visual | one focal moment carries the section's message alone | present but decorative or vague | none, or a placeholder schematic |
| finish | lit, material, grain, precise detail; rewards a second look | some detail, large inert areas | flat fills, default shadows |
| hierarchy | one obvious focal point, then headline, then evidence | readable but flat | competing or absent focus |
| polish | aligned, crisp at 1440 AND 390 | minor misalignment, cramped mobile | overflow, clipped or colliding text |

A section passes when `focal_visual` is at least 4, no score is below 3, at most two scores are 3, and there are
no ban hits. The script computes this from the scores and never trusts a model's own verdict. Scale: 4 equals
7 out of 10. With a rubric alone, critics score strictly (a pilot corpus produced no score above 4 in several
sections); set the real bar from external references (qa-loop.md, "Calibration").

## 8. Special sections

- **CTA and pricing are sections too.** Show what happens after the button (a dated sequence of the real
  artefacts) and let the form react to input; show cost across the range with the current point marked.
- **Footer** is chrome and is judged at page level only.
- **Wrapper pages** (portfolio, showcase) keep a neutral identity of their own (trust.md).
- **Accessibility and SEO** are gates, not craft: one h1, landmarks, skip link, 4.5:1 text contrast, 44 px targets,
  visible focus, alt text, `lang`, meta description, canonical, JSON-LD, 1200x630 OG image with text composited
  locally (never generated).
