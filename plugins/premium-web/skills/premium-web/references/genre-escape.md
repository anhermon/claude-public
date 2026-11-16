# Genre escape and section craft (hard rules)

Why this exists: fixmap redesign r2 (2026-10-04) passed type, palette, tokens and Lighthouse and was still
"basic, no wow": every section was a bordered mono panel on a dark graphite ground, the dev-tool genre default.
A tool site drifts to that genre unless forced out. Checked by `tells.js` (panel_run, scale_change, type_scale,
wow_visible = `craft_fail`, which fails the page) and the critic.

## 1. Name the genre you are drifting into (intake, written)

Write: "Left alone this page becomes ___" and list 4 things you will change. Known genre attractors:
- **dev-tool dark**: graphite ground, hairline-bordered mono panels, one orange/green accent, 01/02/03 steps, file-tree box.
  Escape: change the ground (a light/paper or saturated-muted hero field), put the product at 50%+ width not in a card,
  use display type >= 8vw somewhere, replace panels by drawn figures that bleed to the viewport edge.
- **data-docs**: tables + bar lists + chips. Escape: one navigable visual field (all N items as one map/grid), tables only for evidence.
- **SaaS-centred**: centred H1, two buttons, logo row, three cards. Escape: asymmetric hero, product as hero.
- **editorial-serif-beige**, **gradient-glass**, **terminal-cliche**: see SKILL.md anti-patterns.
If your recipe's "Direction" line equals the genre attractor, you have not chosen a direction.

## 2. Section-craft numbers (all measurable)

- No more than **3 consecutive** sections whose main content is a bordered/filled box (`panel_run`). Mono panels: max 1 per page.
- At least **2 scale-change sections** below the hero (`scale_change`): edge-to-edge drawn figure, a contrasting full-width
  ground, or display type >= 12vw. Not "the same column with a bigger heading".
- **Type scale**: largest text >= 4x median text (`type_scale`); the h1 or one numeral >= 7vw at 1440.
- **One real data-driven visual** per page that is not decoration: built from the product's measured data (all 80 items
  placed, each drawn from its record), with a legend and an honest count. Decorative gradients do not count.
- **Real motion tied to meaning**: motion shows a state change of the data (offset closing, a count running, a segment
  snapping), 0.3-1.2s, one focal motion at a time; `prefers-reduced-motion` shows the final labelled state; never ambient.
- **Rhythm**: alternate ground (ink / paper / saturated-muted) at least twice; alternate density (dense figure, then one
  sentence at display size).
- **Above the fold** at 1440 and 390: the wow object plus the one action. Nothing else needs to be there.

## 3. Reference-gap check (measure, do not guess)

Before building and again before the critic: screenshot the 3-5 best sites of the category (live, 1440), put them
beside your hero in one image, and write the three largest gaps (scale of hero object, type contrast, number of ground
changes). Close the gaps before running the critic. Measured set is in wow.md "Measured exemplars".
