# Writing a spec

A spec is one JSON file. `spec.schema.json` is the contract (the generator rejects unknown keys and lists every problem at once);
`example.spec.json` is a complete, neutral example to copy. This page explains the choices the schema cannot.

## Order of work

1. Concept: invent it, label it (`concept.notice`, `concept.noticeShort`), no real brand, person or product. Say plainly that
   numbers are invented. Every page the factory builds carries the notice in the nav and the footer.
2. Subject kind (see SKILL.md). One persistent subject, never a second one.
3. Chapters: pick archetypes in reading order, give each one with a `target` a layout and a placement.
4. Direction: palette, fonts, one `ground` entry per act.
5. Commerce (needed by `pricing`, `faq`, `footer`), then the assets plan.

## Top level

| Key | Notes |
|---|---|
| `name`, `slug` | `name` is the wordmark (the giant type). Keep it short: 4 to 9 letters fit a wide band. |
| `concept` | `notice` (long, nav on desktop), `noticeShort` (nav on mobile), `description` (meta). |
| `direction.palette` | `ground`, `ink`, `inkSoft`, `accent` required; `accentText` is the accent used on text (keep contrast); `light{}` holds the light-world overrides. |
| `direction.fonts` | `display`, `body`, `mono`: `id` is a fontsource id fetched by premium-web `get-font.sh`; `family` is the CSS name; `weight`, `stretch` optional. A missing font degrades to a system stack with a warning. |
| `direction.ground[]` | One entry per act (acts = chapters that have a `target`). Each: `base`, `accent?`, `light?: true`, `glow{at:[x,y], radius:[rx,ry], colors:[c0,c1,c2]}`. Fewer entries than acts repeats the last one (warning). |
| `subject` | `kind`, `items` (8-256; shader-field at most 64), `seed`, `count` (point-cloud points), `wordmark` (bool), `params` (per kind, unknown keys rejected). |
| `interaction` | Labels for the cursor query: `title`, `groups[]` (chips and layer names), `names[]` (item name stems, same length as groups), `scanLabel`, `footnote`. |
| `budgets` | `dprMax`, `dprMaxMobile`, `frameMs`, `mobileMaxWidth` (default 820). |

## Subject params

- glass-lattice: `radius`, `rodRadius`, `ior`, `thickness`, `dust`, `tints[]`, `rodsPerNode`.
- point-cloud: `size`, `gain`, `rim`, `lit`, `shade`, `rimColor`, `swirl`, `anchorSize`. Additive glow on dark grounds; a light ground
  switches to ink dots in the accent colour, so give light grounds a dark `accent`.
- shader-field: `scale`, `warp`, `speed`, `contrast`, `veins`, `refract`, `wells`. The field is calm away from the subject so copy
  stays readable; raise `contrast` or `veins` with care.

## Chapters

```json
{ "id": "index", "archetype": "explainer", "nav": "Index",
  "target": { "layout": "layers", "k": 4 },
  "place":  { "desktop": "right", "mobile": "top", "scale": 0.95, "pitch": 0.42, "yaw": -0.3 },
  "copy":   { ... archetype fields ... }, "params": { ... } }
```

- `nav` adds the chapter to the top nav. `id` is the anchor.
- `target.layout`: cube, sphere, ring, helix, layers, clusters, towers, shards, wave, galaxy, scatter, plane; `k` is the group count
  where it matters (layers, clusters, towers, shards); `params.spread` widens it. Items are grouped by `floor(i*k/n)`, and chips,
  tiers and layers all use the same rule, so the lit group always matches what the copy says.
- `place.desktop`: left, right, center, top, bottom. The copy goes to the opposite side. `bottom` leaves the top of the screen for
  copy, so use it for `stat`. `place.mobile`: top (default), center, bottom. `scale` 0.3 to 1.4; `pitch`/`yaw` set the tilt.
- Band and footer have no `target`: they hold the previous act.
- Vary placement across chapters. Two chapters in a row on the same side look like a template.

## Commerce

`inputs` are two sliders with ids `a` and `b` (`label`, `min`, `max`, `step`, `value`, `suffix`). A tier costs
`fixed + max(0, a - included.a) * rates.a + max(0, b - included.b) * rates.b`; `cap{a,b}` marks a tier that cannot serve the
usage (dimmed, never chosen). The cheapest tier that fits is "best fit" and lights its group in the subject; the arithmetic is
printed under the total. Prices are invented and must be labelled so. `faq[]` is `{q, a}`; `cta` feeds the footer card.

## Assets plan

`assets.plan[]`: `{slot, source: code|procedural|generated-with-prompt, prompt?, alt?}`. The band and footer plates are procedural
SVG contours until a file named in the plan exists in `img/`. To replace one, generate it with premium-web-imagery, put it in the
asset cache, copy it to `img/<file>` with `premium-web/scripts/package-piece.mjs`, then regenerate. Never commit generated art
into this plugin.
