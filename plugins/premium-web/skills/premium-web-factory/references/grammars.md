# Page grammars

Choose the reading and motion structure before the subject, fonts or palette. A new
colour on the same choreography is still the same page.

**Every new piece must be a different grammar OR a different `hero.layout` +
`scroll.mode` combination from every existing piece.** Also change chapter order;
the portfolio gate rejects identical orders and close palettes with the same fonts.

## Pick from the concept

| Concept's central verb / experience | Grammar | Hero / scroll | Why |
|---|---|---|---|
| Transform, assemble, distribute; one object explains the mechanism | morph-subject | split / morph | Copy and object take turns through subject targets. |
| Listen, contemplate, inspect a single coherent form | morph-subject | stack / orbit | Centred title introduces a form below; camera explores it without reshaping. |
| Immerse, surround, expose material at scale | morph-subject | bleed / static | Edge-to-edge subject medium, a deliberate left copy zone, changing grounds. |
| Declare, name, announce; language carries the identity | morph-subject | type-only / static | Huge headline, small subject accent, no readout card. |
| Sequence, route, compare, unfold a process or editorial collection | rail | panels / horizontal | A pinned strip of wide graphic panels; no 3D and no persistent subject. |
| Observe, diagnose, record; a tool session tells the story | terminal | window / command chapters | Scroll chooses a command; real typing and immediate log output. |
| Imprint, cut, rearrange; language is the material | collage | type / spatial chapters | Huge contrasting words, flat paper cutouts and bounded cursor response. |
| Scrub video, multiple scenes or a bespoke composition every section | hand-built | premium-web-motion / webgl | Outside these factory grammars. |

## morph-subject (default)

`"grammar": "morph-subject"` is optional. Old specs retain their original output,
including serialized config and manifests. Keep the usual `subject`, `chapters`,
targets, placement and ground sequence from `spec-authoring.md`.

```json
"hero": { "layout": "stack", "wordmark": false },
"readout": "inline",
"scroll": { "mode": "orbit" }
```

| Field | Values / behaviour |
|---|---|
| `hero.layout` | `split` (default): copy left, subject right; `stack`: centred headline with subject below; `bleed`: large subject across the right edge, headline in a left clear zone; `type-only`: oversized type and small subject accent. |
| `hero.wordmark` | Boolean, default true; overrides legacy `subject.wordmark`. False removes the hero's GL and DOM wordmarks and their reserved band. Footer is independent. |
| `readout` | Top-level `card` (default), `inline` (a compact query line under the CTAs), `none`. `type-only` always omits the readout. |
| `scroll.mode` | `morph` (default): continuous target reshaping; `orbit`: first shape held while camera orbits/dollies and placement follows chapters; `static`: first shape and placement held, sections change ground. |

Each layout has a separate mobile composition. Stack puts copy first and the subject
below. Bleed reserves a subject zone above the copy on mobile. Type-only keeps its
type first and subject small. Keep headlines short; the factory falls back to system
fonts when `--no-fonts` is used. Test with the final self-hosted fonts before shipping.
For static mode, compose later copy opposite the fixed subject; avoid arbitrary
side changes. Controls remain functional; pricing does not stretch a static subject.
Reduced motion and `?rm` keep a still assembled scene; `?nogl` uses the poster path.

## rail

Use `"grammar": "rail"`, omit `subject`, `hero`, `readout` and `scroll`. No WebGL,
three, CDN or media files are generated. The first panel is the hero. Desktop pins
the strip; vertical scroll drives a damped horizontal translation. Words respond
to bounded scroll velocity, figures scale or wipe at handoff, SVG contours sweep,
and a rule shows progress. The page unpins into a full-bleed drawn interlude, then commerce.

```json
"grammar": "rail",
"rail": {
  "panels": [
    { "id": "start", "title": "Keep things moving", "eyebrow": "A fictional study",
      "nav": "Start", "copy": "An invented process, shown one decision at a time.",
      "figure": { "kind": "stat", "value": "24", "label": "Sample routes" } },
    { "id": "route", "title": "One clear path", "copy": "From idea to dispatch.",
      "figure": { "kind": "diagram", "items": ["Intake", "Edit", "Send"], "label": "Illustrative process" } }
  ],
  "params": { "transition": "wipe", "scrollRatio": 1 }
}
```

All normal concept, direction, fonts, ground, budgets and assets fields are shared.
Give each panel an id, title, copy and figure. `eyebrow` and `nav` are optional.
Panel ids and chapter ids must be unique. Ground entries correspond to panels,
then commerce chapters; the last entry repeats if there are fewer grounds.

| Figure kind | Fields | Composition |
|---|---|---|
| `stat` | `value`, `label` | One huge, explicitly labelled sample number. |
| `timeline` | `items` (2–6 strings), `label` | Numbered process list. |
| `diagram` | `items` (2–6 strings), `label` | Connected nodes with matching text labels. |
| `quote-free` | `label`, optional `value` | Abstract SVG seal / short editorial note; no fabricated testimonial. |

| `rail.params` | Default | Bounds / meaning |
|---|---|---|
| `damping` | 0.12 | 0.05–0.3, frame-rate-normalized lerp. |
| `panelVw` | 100 | 85–100, panel width as desktop viewport percent. |
| `scrollRatio` | 1 | 0.6–1.8, vertical pixels per horizontal pixel. |
| `velocityMax` | 1.2 | 0–1.5, kinetic-type amplitude cap. |
| `ambientLines` | 12 | 4–24 procedural contour lines. |
| `transition` | `scale` | `scale` or `wipe`; applied to the figure, keeping copy legible. |

`chapters` may be omitted. When present, they contain only `pricing` and `faq`, use
the existing copy/commerce fields, and need no targets. Both render as ordinary
vertical sections after the rail and share the original calculator/disclosures.
The rail ends with a compact notice and return link, without a giant wordmark.

Mobile uses the same panels in a vertical stack. Reduced motion (`?rm` or system),
no JS, and desktop panels too tall to fit also use the vertical stack. Resizing
recomputes pin travel; internal panel links map to the correct vertical position.

## terminal

Use `"grammar":"terminal"`; omit `subject`, `hero`, `readout`, `scroll` and `rail`.
The hero is a complete instrument window, with no preceding marketing hero.
Required `terminal` fields:

```json
"terminal": {
  "prompt": "field@local:~$",
  "theme": { "screen":"#0c1819", "text":"#e5efdc", "signal":"#a4efba" },
  "session": [
    { "id":"wake", "title":"Open the notebook.", "nav":"Wake",
      "cmd":"instrument wake", "output":["Local notebook ready."],
      "pane": { "kind":"quote-free", "label":"Instrument reticle" } },
    { "id":"sample", "title":"Read the field.", "cmd":"sample collect",
      "output":["24 simulated readings."],
      "pane": { "kind":"stat", "value":"24", "label":"Sample observations" } }
  ]
}
```

`session` takes 2–8 unique command chapters. `output` is 1–16 strings; pane uses
the rail figure contract above. Diagram/timeline require items; stat requires value.
Scroll scrubs chapter selection, forwards or backwards. Entering a chapter replays
its command at 35ms/character, then reveals the entire output instantly. Completed
and offscreen chapters retain full output. A 260ms scanline glitch marks entry.
Split log/diagram panes and an SVG reticle form the instrument's brand world; a
local clock updates once a second. Mobile stacks the panes and chapters. No JS,
`?rm`, or reduced motion shows the final command/output frame of every chapter.
Optional top-level `chapters` contain only target-free pricing/faq after the session.

## collage

Use `"grammar":"collage"`, with `collage.words` (2–8 strings, up to 12 characters each), `collage.palette`
(2–6 hex colors), and `collage.blocks` (1–8 `{label, caption, color}` objects).
`color` is a zero-based palette index. Optional `collage.marquee` supplies its line.
Top-level `chapters` use `archetype:"collage"` and `copy:{title,deck}`; chapter ids
must be unique. Subject, hero, scroll and other grammar payloads are rejected.

Words alternate heavy sans, italic serif and outlined type; no unsupported font
variation axes are assumed. Chapter order rotates the word composition and flat
paper grounds. Pointer input shifts words toward the cursor through a time-based
damped lerp with different word depths, capped at 18px horizontally. Scroll changes vertical displacement and
scale within a padded safe area. Phones use scroll and tap to reflow the words;
captions stay visible.
Cutouts reveal captions on hover, keyboard focus or click; the plate is inline SVG.
Reduced motion / `?rm` stops type transforms and the marquee. No JS preserves the
complete composition and native hover/focus captions.

## Portfolio gate and rendered proof

`node skills/premium-web-factory/scripts/variation-check.mjs <spec-or-piece-dirs...>`
supports all four grammars, including terminal's command/figure order. It extends
the shared gate without changing sibling skills. The original registry-capable
`node skills/premium-web/scripts/variation-check.mjs <registry-or-dirs...>` reads
`spec/piece.json`, source `spec.json`, or the generated config of older pieces.
Registries can be arrays of paths or `{ "pieces": [{ "dir": "relative/path" }] }`.
Paths resolve relative to the registry; multiple inputs are supported.
It fingerprints grammar, subject, hero, scroll, chapter/panel-figure order, ground
sequence, circular palette hue spread and display/body font pair. It exits 1 for:

- Matching grammar + subject + hero layout + scroll mode.
- Identical chapter order (rail panel figure kinds are included).
- Palette hues within 25 degrees with the same display/body font pair.

Generate all five `.proofs/*/spec.json` files with `--no-fonts` for offline review.
Run factory `--selftest`, the five-piece variation gate, generated JS `node --check`, then render
with `verify-piece.mjs` at 1440 and 390. Rail's horizontal panels need an additional
manual sweep through progress 0%, 33%, 66%, 100%; the verifier's vertical section
anchors alone cannot capture every horizontal panel. Check the unpin boundary,
commerce sliders and disclosures, keyboard links, resize, `?rm` and `?nogl`.
Attach before/after PNGs with `tickets.py attach <id> <png> --caption ...` from the
rendering session. Offline checks are not a substitute for looking at the page.
