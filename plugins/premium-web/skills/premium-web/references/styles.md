# Style recipes

Pick ONE direction per page from the subject, not from habit. Each recipe says what carries the richness, which
material each section needs (see imagery.md for how to make it), the wow families that fit (wow.md), and the
failure mode that got a real page rejected. Recipes down to "Blueprint / engineering" are for marketing pages; the "App" recipes at the end are for apps (step 0 WORK).

## Faces (the one status table; reconciles type-systems.md rules 8-9 with the recipes below)

Every face a recipe or rule names has exactly one status. A recipe may only recommend a **free** face.

| status | faces | rule |
|---|---|---|
| **banned** (new concepts) | Inter, Geist, Bricolage Grotesque, Space Grotesk, Poppins, DM Sans, Plus Jakarta Sans | type-systems.md rule 8. Verified 2026-10-05: neither skeleton ships Inter (both ship Hanken Grotesk); remaining "Inter" mentions are records of measured sites or of anhermon v4, which predates the ban |
| **placeholder** | Hanken Grotesk (`assets/skeleton/fonts/`, used by `tokens.css` and `tokens-app.css`) | ships so an unrestyled page still renders. It is not a recommendation: a finished concept swaps it, or states in NOTES.md why it was chosen on purpose. The Swiss recipe no longer lists it |
| **reserved** by Angel's earlier concepts (type-systems.md rule 9) | Schibsted Grotesk + IBM Plex Mono (meridian), Martian Mono + Commit Mono (ember), Fraunces + Figtree (pebble), Bodoni Moda + Instrument Sans + Sometype Mono (halcyon), Big Shoulders + Azeret Mono + Archivo (tracer) | do not reuse in a new concept **of the same portfolio**. For a different owner (client work, an unrelated product) the reservation does not apply: write "different portfolio: <owner>" in NOTES.md and use it. The recipes below name them only as the *historical* choice of that concept |
| **free** | Familjen Grotesk, Funnel Display, Public Sans, Albert Sans, Onest, Source Sans 3, Atkinson Hyperlegible Next, Newsreader, Cormorant Garamond, Barlow Condensed; mono: Fragment Mono, JetBrains Mono, Red Hat Mono | open licence expected; confirm with `scripts/get-font.sh <fontsource-id> fonts` (it refuses anything non-open; Familjen Grotesk and Fragment Mono were run through it, the rest were not in this environment). Proprietary faces named in measured tables (SF Pro, Söhne, Recoleta, ...) are measurements, not options |

## Material by style (which visuals come from where)

| style | generated imagery (Codex, imagery.md) | code-drawn (HTML/SVG/canvas) | WebGL |
|---|---|---|---|
| Swiss / data | no (photos break the grid's honesty) | everything: charts, annotated diagrams, tables, specimen-level type | optional, for the data-is-brand wow |
| terminal-native | brand-world plates only (the place the tool lives: a machine room, a desk at 3am), never "a terminal" | session replays, ASCII/box-drawing art, keycaps | optional: phosphor glow / CRT is a cliche, avoid |
| tactile consumer | yes: clay/soft 3D product objects, one per section, consistent lighting | the phone UI with named sample data | rarely |
| cinematic / creative | yes: full-bleed film stills, one per section, one light direction | specs tables, controls | yes: hero shader or audio-reactive |
| editorial dark product (anhermon) | 4:5 plates with real data labels overlaid | proof figures (allowlists, diffs) | hero |
| e-commerce / brand storefront | campaign scenes only (one world: material, room, light), labelled as illustration; the PRODUCTS are real supplier photos, trimmed onto one plate | the guide/finder (real dimensions), the proprietary device (dimension rules, catalogue index), quick view; no charts, badges, stamps | no |
| blueprint / engineering | no | isometric drawings, dimension lines, parts lists, revision blocks | optional |
| app: record-as-landscape (run/trace/log/inventory views) | no (screens show real data, never plates) | the whole record set drawn from its fields, annotated, with the table as evidence | no |
| app: working surface (admin, queue, editor, settings) | no | the live object and its states; real rows, real empty/error states | no |

Code-drawn diagrams beat photos for every technical claim (the steel-slab guard lesson, imagery.md).

## Swiss / data (light, strict grid, one signal colour)

- Richness comes from **precision**: tabular numerals, real units, leader-line annotations, axis labels, small
  multiples, a visible 12-column grid used asymmetrically, hairlines of two weights. Never sparse sketches.
- Type: a grotesk with real character (free: Familjen Grotesk, Funnel Display, Albert Sans; Schibsted Grotesk and Instrument Sans were meridian's and halcyon's, see Faces) +
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

- Colour blocks per section (3-5 saturated-but-soft hues), big friendly display (pebble used Fraunces with SOFT/WONK, now reserved; Recoleta is proprietary: pick a free soft serif or rounded display),
  clay renders with one consistent light, a phone UI drawn in code with named sample data, buttons with depth.
- Each section: one object or one interactive (slider, toggle) doing the product's real arithmetic.
- Fails as: generic gradient blobs, stock 3D emoji, cards without objects.

## Cinematic / creative (halcyon, approved)

- Dark, film-grade. Display serif with contrast (halcyon used Bodoni Moda, now reserved; free: Newsreader, Cormorant Garamond; Playfair is overused), one warm accent, film stills
  with one light direction. Slow reveals (0.8-1.2s). Sound only after a click with a visible toggle.
- Each section: a full-bleed or 4:5 still, or the rendered device. Specs as a real table.
- Type QA: big display serifs collide (descenders into the next line, kerning gaps like "W eather"): check every
  display heading at 1440 and 390.

## Editorial dark product (anhermon v4, shipped)

- One neutral sans at a measured scale, dark default, one blue accent, generated 4:5 plates with real
  data labels, code-drawn proof figures, WebGL hero with honest caption. See rubric.md per-section table.
  (anhermon v4 shipped in Inter before Inter was banned; do not copy the family into a new concept.)

## Blueprint / engineering

- Cobalt-to-ink ground (not neon on black), white and pale-cyan linework, drafting grid, dimension lines, callouts,
  parts-list tables, isometric exploded diagrams, stamped revision blocks. Condensed/technical display (free: Barlow Condensed;
  Big Shoulders and Archivo were tracer's, see Faces) + a mono for callouts.

## App: record as landscape (run, trace, log, inventory, queue views)

For screens whose job is reading many records (mode `app`; read app-mode.md first). Signature clarity applies (wow.md "App mode"), not a hero size.
- The signature object is the data itself when it shortens a task: every record placed once and drawn from its own fields (a run as a lane of spans scaled by duration,
  an inventory as a grid of cells coloured by state, a queue as items at their real age), with a legend and an honest count. The table sits beside or beneath it as evidence and as
  the fallback, never as decoration. No rule sizes it; the walk-through justifies it.
- Chrome recedes: one slim top bar or rail, no KPI tile row, no decorative card borders; groups are separated by ground change, spacing and type weight, not boxes. Selecting a record opens its detail in place.
- Density is the material: tabular numerals, real units, 12-13px data text. Colour: neutral ground, one signal hue plus one status hue, each meaning one thing, explained once.
- Fails as: hero card + stat bar + side panel + table (the attractor, genre-escape.md section 1).

## App: working surface (admin, editor, settings, review queue)

- One primary object (the thing being edited or decided) holds >= 50% of the width; controls hang off it, not beside it in equal boxes. Show the object's real states: loading, empty, error, partial, over-limit
  (`data-state` hooks with real copy, the `state_coverage` gate).
- A decision area states the consequence of each action in data terms ("moves 14 items, 2 fail validation") before commit. Keyboard path and focus ring are part of the design.
- Fails as: a sidebar + topbar + grid of equal cards with a donut and a line chart (admin-template default).

## App type (mode `app`; the numbers are checkable by `tells.js` and `rubric-app.md`)

- **One sans family**, from the Faces table (free faces; open apertures and distinct I / l / 1 and 0 / O matter in an all-day tool: Atkinson Hyperlegible Next, Public Sans, Source Sans 3). Hanken Grotesk is the placeholder.
- **Legible 12-14px**: data and controls 13-14px (12px only for secondary metadata, never below 12), line height 1.4-1.5, weight 400 for data and 500-600 for emphasis (no 300 at 12px), contrast >= 4.5:1. View titles 16-18px; nothing above 28px over data (the hierarchy axis fails it). No display numeral is required.
- **Tabular numerals on every number**: counts, durations, sizes, timestamps, ids with digits (`font-variant-numeric: tabular-nums`), right-aligned numeric columns, units on every value, thousands separators.
- **Mono for identifiers only**: ids, hashes, paths, branch names, commands, log lines, at about 12px beside 13px sans. Never for prose, labels, headings or whole tables (`mono_body` and the critic catch it).
- **No uppercase micro-label overload**: sentence-case column headers and labels. At most one uppercase tracked style on a screen, used for a handful of items at most; `caps_micro_labels` is a hard fail in app mode.
- Sentence case everywhere; relative time with the absolute time on hover/title; truncate with a tooltip, never wrap an id.

## E-commerce / brand storefront (Provenant v1 + v2 rejected 2026-10-11/12)

Angel, v1: "looks terrible - you don't create a luxurious feeling by writing 'luxury' or putting the price at the front,
or covering everything with gold" + "show real products, not concept". v2 (warm paper + Cormorant, small packshots in big
beige boxes, every product link going out to the supplier): "it still doesn't look good". Measured references:
`~/dev/luxe-store/research/refs-v3/TABLE.md` (Angel's list) and `refs-v2/` (The Row, Khaite, Toteme, Minotti, Aesop, Rug Co).

Angel's reference set and what each one is borrowed for (his words in quotes):
| reference | borrow |
|---|---|
| Bang & Olufsen | "aspirational lifestyle imagery with clear product discovery": the product shot as a sculptural object, then a room it lives in, then a direct way to the item |
| Aesop | "a cohesive visual identity, generous spacing, and useful guidance": a product finder/advisor that answers a real buying question |
| Gentle Monster | "a distinctive campaign concept that carries through into the storefront": one world, not a category list |
| Apple (AirPods Pro) | "give each section one clear message, supported by a compelling visual": oversized imagery, one sentence per section |
| Polestar | "a disciplined design system and clear next actions": separate discover / configure / purchase paths |
| LOEWE | "alternate editorial storytelling with focused, shoppable collections" |
| Teenage Engineering | "a consistent graphic language that makes even ordinary interface elements feel proprietary" |

Rules (each is checked by the critic; tells.js counts the measurable ones):
1. **Coherent assortment before any concept.** The store sells ONE category a buyer shops as one thing (lighting,
   fine jewelry, tabletop), with one customer and one buying question. A campaign story cannot glue unrelated
   categories together: v3 "one dining room" over rings + tables + rugs was rejected as "wtf is the common theme
   between rugs, tables and rings? it just looks incoherent". When the assortment comes from sourcing (dropship
   margins), pick the category first, then the suppliers inside it, then the concept. The concept (Gentle Monster
   rule) is the world of that one category.
2. **One message per section** (Apple): a section has one sentence of claim and one dominant visual; never a heading
   plus a paragraph plus a grid plus a note.
3. **Rhythm** (LOEWE): editorial (full-bleed scene, one line) alternates with a focused shoppable collection; never two
   collections or two scenes in a row; at least 2 scale changes per page.
4. **Consistent plates, product at a deliberate scale.** Normalise every supplier packshot (trim the white margin,
   re-pad to one aspect, same fill rule for every item) onto ONE plate colour used site-wide. Measured (refs-v3/TABLE.md):
   plate = flat light grey, no border/radius/card shadow, on a white ground (B&O #f6f6f6, Apple #f5f5f7, Polestar
   #f0f0f0, TE #f5f5f5); product at 40-55% of the plate in list views, 65-75% (cropped off-frame allowed) in the one
   hero moment. Multiply a white packshot onto that grey, never onto beige (v2 was muddy beige-on-beige, products
   floating small in big tinted boxes, one box empty). Price = a 12-13px caption under the name, same weight (B&O,
   TE), or one row in a spec ledger (Polestar).
5. **Discover / configure / purchase paths** (Polestar): every product opens an on-site quick view or detail panel with
   a large image, material, dimensions, lead time, the real configuration options the supplier offers (sizes, carat,
   wood), and one next action. Product links must never send the buyer to the supplier's or a competitor's site; mark each product
   element `data-product` so tells.js `product_links_out` can check it.
6. **Guidance** (Aesop): one finder/advisor that answers a real question with real data (which rug size fits this
   table; which ring setting for this stone), drawn in code with real dimensions; optional, never the only idea.
7. **Proprietary graphic language** (Teenage Engineering): one consistent device carried through ordinary UI (e.g. a
   dimension rule with real measurements on every product, a numbered catalogue index tied to real SKUs, a single
   drawn line motif). One device, used everywhere, not decoration in one place.
8. **Restraint** (still): sans-led or one refined face chosen from the measured table, not warm paper + Cormorant by
   default; near-white or one deep ground; small quiet nav and captions; price small, after the name, in caption
   weight; no "luxury/premium/exclusive/curated"; no gold or brass fills, gradients, metallic textures.
9. **Scenes are labelled.** Generated rooms are atmosphere; a hotspot or "shop the room" on a generated scene must say
   "illustration" and name the closest real piece, never imply the drawn object is the product.
11. **Motion is scrubbed and quiet** (v3 r1: "the animations are quirky, and visually the site still looks mid"):
    a scroll scene's zoom is driven continuously by scroll progress (no timed transition, never a transform-origin
    change between steps, which jumps); image swaps crossfade with scroll; text fades only. No translateY slide-up
    reveals on cards or copy, no staggered card entrances, no hover outlines. Storefront peers barely animate.
12. **No UI cards floating over campaign photography.** Product name, price and "View" sit on the image as a caption
    (B&O/LOEWE) or beside it; a white panel pasted on a photo reads as a widget.
13. **Shop-the-look hotspots are the storefront's explanatory visual** (Provenant v4, critic r1→r2 moved the page from
    closest=rejected to closest=approved): on every campaign photo, a dot on the actual piece + hairline leader + "Name ·
    price" caption linking to the on-site PDP. Positions stored as image fractions and mapped through object-fit:cover.
    Home rows list in-stock pieces first; never show "Unavailable" on the home page. Plates pre-cropped to ~80% fill.
14. **Copy claims follow the metal, not the brand idea.** "Doesn't tarnish / wear it in the water / sleep in it" is only
    safe for verified 14K+ solid gold; 10K and chlorine make it false. Check each product's karat before writing it.
10. **Wow** = editorial scale and pacing on the real goods (a scroll scene that moves from the room to the real product
    at full scale; a packshot held at 60%+ viewport width), not a gimmick widget.
- Fails as: gold plate/badge/stamp hero, price-forward cards, dark + gold, explaining the store's process instead of
  showing the goods, disclaimer above the fold, tiny packshots in big tinted boxes, beige-on-beige, products linking out,
  off-story items that break the concept (a bright orange rug in a madder-and-indigo room).
