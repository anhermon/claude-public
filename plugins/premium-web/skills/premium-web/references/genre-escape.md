# Genre escape and section craft (hard rules)

Why this exists: fixmap redesign r2 (2026-10-04) passed type, palette, tokens and Lighthouse and was still
"basic, no wow": every section was a bordered mono panel on a dark graphite ground, the dev-tool genre default.
A tool site drifts to that genre unless forced out. In marketing mode checked by `tells.js` (panel_run, scale_change, type_scale,
wow_visible = `craft_fail`, which fails the page) and the critic; in app mode by the app tells (wow.md "App mode") and rubric-app.md.

## 1. Name the genre you are drifting into (intake, written)

Write: "Left alone this page (app mode: this app) becomes ___" and list 4 things you will change. Known genre attractors:
- **dev-tool dark**: graphite ground, hairline-bordered mono panels, one orange/green accent, 01/02/03 steps, file-tree box.
  Escape: change the ground (a light/paper or saturated-muted hero field), put the product at 50%+ width not in a card,
  use display type at 7vw or more somewhere (guidance, see section 2), replace panels by drawn figures that bleed to the viewport edge.
- **data-docs**: tables + bar lists + chips. Escape: one navigable visual field (all N items as one map/grid), tables only for evidence.
- **SaaS-centred**: centred H1, two buttons, logo row, three cards. Escape: asymmetric hero, product as hero.
- **dashboard / run-view** (app mode): hero card + stat bar + side panel + table; KPI-tile rows (big number, delta
  chip, sparkline); sidebar + topbar admin chrome; donut and line-chart cards in a 2x2 or 3-up grid.
  Escape: make the product's own record the hero object (the run drawn as lanes, the inventory as one cell grid) and
  give it the working area (signature clarity, wow.md "App mode": it must shorten a primary task, no size gate); replace the tile row with one drawn structure of
  the real data (every item placed, one finding as a display numeral); drop the sidebar to a slim rail or a command
  bar and let a ground change, not a card border, separate regions; swap decorative donut/line cards for the one
  chart that answers the screen's question, annotated with real values and thresholds; treat density (tabular
  numerals, small multiples, real units) as the material instead of padding it out with whitespace. Tables remain only as evidence under the figure.
- **editorial-serif-beige**, **gradient-glass**, **terminal-cliche**: see SKILL.md anti-patterns.
If your recipe's "Direction" line equals the genre attractor, you have not chosen a direction.

## 2. Section-craft numbers (all measurable)

(Marketing mode only. App mode does not gate panel runs, scale changes, type scale or wow placement: they measure the shape of a scrolling page. Its thresholds are
in wow.md "App mode" and the type rules in styles.md "App type". Never add sections, bands or a numeral to an app to satisfy one of these numbers; if a gate seems to demand it, stop and report it as mismatched.)

- No more than **3 consecutive** sections whose main content is a bordered/filled box (`panel_run`). Mono panels: max 1 per page.
- At least **2 scale-change sections** below the hero (`scale_change`): edge-to-edge drawn figure, a contrasting full-width
  ground, or display type >= 12vw. Not "the same column with a bigger heading".
- **Type scale**: largest text >= 4x median text (`type_scale`); this ratio is what tells.js enforces (marketing). Guidance, not measured: the marketing h1 or one numeral at about 7vw (100px) or more at 1440.
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
