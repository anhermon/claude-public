# Style recipes

Pick ONE direction per page from the subject, not from habit. Each recipe says what carries the richness, which
material each section needs (see imagery.md for how to make it), the wow families that fit (wow.md), and the
failure mode that got a real page rejected. Faces are examples with character; check the banned list in
type-systems.md and never reuse a face another concept in the same portfolio owns.

## Material by style (which visuals come from where)

| style | generated imagery (Codex, imagery.md) | code-drawn (HTML/SVG/canvas) | WebGL |
|---|---|---|---|
| Swiss / data | no (photos break the grid's honesty) | everything: charts, annotated diagrams, tables, specimen-level type | optional, for the data-is-brand wow |
| terminal-native | brand-world plates only (the place the tool lives: a machine room, a desk at 3am), never "a terminal" | session replays, ASCII/box-drawing art, keycaps | optional: phosphor glow / CRT is a cliche, avoid |
| tactile consumer | yes: clay/soft 3D product objects, one per section, consistent lighting | the phone UI with named sample data | rarely |
| cinematic / creative | yes: full-bleed film stills, one per section, one light direction | specs tables, controls | yes: hero shader or audio-reactive |
| editorial dark product (anhermon) | 4:5 plates with real data labels overlaid | proof figures (allowlists, diffs) | hero |
| blueprint / engineering | no | isometric drawings, dimension lines, parts lists, revision blocks | optional |

Code-drawn diagrams beat photos for every technical claim (the steel-slab guard lesson, imagery.md).

## Swiss / data (light, strict grid, one signal colour)

- Richness comes from **precision**: tabular numerals, real units, leader-line annotations, axis labels, small
  multiples, a visible 12-column grid used asymmetrically, hairlines of two weights. Never sparse sketches.
- Type: a grotesk with real character (Schibsted Grotesk, Hanken Grotesk, Instrument Sans, Funnel Display) +
  a mono for data only. Big numbers are part of the design.
- Every section's visual is **a figure you could print in a report**: real-shaped sample data, labelled
  "sample data". A parsed log line with every extracted field called out; an alert timeline with its threshold;
  a cost calculator whose arithmetic is visible.
- Second colour: a data hue (or a tint scale of the signal colour) so charts have depth; not one-note.
- Fails as: hairline-and-text sections with stick-figure sketches (Meridian method); a "nice" log panel as the
  only idea (Meridian hero).
- Material and depth (Plumb r5 critic: "one beige sheet... one great object on a plain page"): give one section an
  inverted ink ground with the data glowing in the signal colour, one full-bleed figure that breaks the 12-col
  measure, and a paper/print texture or fine grid on the ground. Data figures fill their frame: scale marks to the
  region (sparse counts become bar segments, not 4px dots under empty space).

## Terminal-native (CLI / dev tool) without the cliche

Ember was rejected as "generic AI templaty" because it was the category average: amber mono on black, `[bracket]`
nav, a `curl | sh` box, a tabbed fake terminal, four "no daemon / exit codes" principle cards. A distinctive CLI
page does at least three of these:

1. **Real product replay, not a typing animation**: a recorded session (asciinema-style JSON of
   `[time, text]` events) of the real tool doing the real job, replayed with true timing, pausable, with
   annotations that pin to lines ("this line is the diff", "exit code 2 = changes pending"). The replay IS the
   explanatory visual for several sections: each section scrubs to a different moment of the same run.
2. **A brand world beyond the terminal window**: the tool's place in the world (the release train, the 3am
   pager, the keychain) rendered as a plate or a scene. The terminal is one object in a composition, not the page.
3. **Bespoke ASCII / box-drawing art direction**: large-scale ASCII figures that are diagrams (a dependency graph
   drawn in box-drawing characters at 10px, a diff rendered as a landscape), not decorative borders.
4. **A strong typographic voice**: a display face that is NOT a mono (a grotesk or a slab with personality) for
   headlines, mono for the tool's own output only. Sentence case. No uppercase micro-labels.
5. **Physical interface**: keycaps you press, a printed man-page specimen, a receipt of a run.
6. **Two or more colours from the tool's own semantics** (diff green/red, exit-code amber, sealed blue), each
   meaning one thing, explained once.
- Banned in this style: `[bracket]` nav, blinking-cursor hero as the only idea, `curl | sh` as the hero CTA,
  principle cards, CRT scanlines/phosphor glow, mono body copy.

## Tactile consumer (pebble, approved)

- Colour blocks per section (3-5 saturated-but-soft hues), big friendly display (Fraunces with SOFT/WONK, Recoleta),
  clay renders with one consistent light, a phone UI drawn in code with named sample data, buttons with depth.
- Each section: one object or one interactive (slider, toggle) doing the product's real arithmetic.
- Fails as: generic gradient blobs, stock 3D emoji, cards without objects.

## Cinematic / creative (halcyon, approved)

- Dark, film-grade. Display serif with contrast (Bodoni Moda, Playfair is overused), one warm accent, film stills
  with one light direction. Slow reveals (0.8-1.2s). Sound only after a click with a visible toggle.
- Each section: a full-bleed or 4:5 still, or the rendered device. Specs as a real table.
- Type QA: big display serifs collide (descenders into the next line, kerning gaps like "W eather"): check every
  display heading at 1440 and 390.

## Editorial dark product (anhermon v4, shipped)

- One neutral sans (Inter opsz) at a measured scale, dark default, one blue accent, generated 4:5 plates with real
  data labels, code-drawn proof figures, WebGL hero with honest caption. See rubric.md per-section table.

## Blueprint / engineering

- Cobalt-to-ink ground (not neon on black), white and pale-cyan linework, drafting grid, dimension lines, callouts,
  parts-list tables, isometric exploded diagrams, stamped revision blocks. Condensed/technical display (Big Shoulders,
  Archivo Narrow) + a mono for callouts.
