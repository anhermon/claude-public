---
name: premium-web-factory
description: >
  A small deterministic generator for premium single-page pieces: a short declarative spec (JSON) in, a working page out,
  with no LLM in the loop. Choose a page grammar: morph-subject (persistent 3D/shader, four hero layouts, morph/orbit/static
  scroll), rail (pinned horizontal panels), terminal (scroll-selected typed command sessions) or collage (giant type and
  paper cutouts with damped pointer/scroll response). Code-only grammars have no WebGL. All share tokens,
  fonts, nav, live commerce, fallbacks and safe manifest regeneration. Three subject kinds: glass-lattice, point-cloud,
  shader-field. Use for "generate a premium page from a spec", "spin up another piece like
  the last one", "scaffold a 3D landing page fast", "a concept page with a 3D subject and a pricing calculator", or when
  premium-web needs a strong baseline in seconds so the effort can go to the one bespoke wow moment.
  Also use for "generate a pinned horizontal rail from JSON, no 3D", "terminal session hero", "collage typography from JSON"
  and "vary hero layout and scroll grammar".
  Do NOT use for hand-built one-off scenes (premium-web-webgl), for structures outside these grammars (premium-web),
  for dashboards or app UI, for characters or mascots, or when the brief needs bespoke art direction
  on every section.
---

# premium-web-factory

Spec in, page out. `node scripts/new-piece.mjs <spec.json> <out-dir>` writes a complete static piece (HTML, CSS, JS, vendored
three for morph-subject, fonts) in about 20 ms (about 1-2 s the first time, while fonts download). Same spec plus same factory gives the same
bytes. It reuses the webgl stage rig, the motion template and the vendored three r170 from the sibling skills at generation
time; none of that is duplicated here.

## What it gives you, and what it does not

- It gives a **strong baseline fast**: choreography, a live subject, a calculator that drives it, mobile composed separately,
  fallbacks, and the critic fixes already built in (readout never over the wordmark, faq clear of the nav, no big mobile gaps).
- It does **not** give a wow moment. Measured against a hand-built, critic-iterated piece, factory output is a competent baseline,
  not a finished premium page. The signature moment is authored per piece in `bespoke/index.js` (a file the factory creates once
  and never overwrites), following premium-web `references/wow.md`.
- It stores **no art**. Plates and posters come from premium-web-imagery through the asset cache (`assets.plan.json` lists the
  slots). Until a file exists the factory draws a seeded procedural contour plate. No image, font or screenshot lives in the plugin.

## Workflow

1. Pick the grammar using `references/grammars.md`, then read `references/spec-authoring.md` and `spec.schema.json`.
   Start morph-subject from `example.spec.json`; code-only examples are `.proofs/*/spec.json`.
   Invent a concept, label it as such (`concept.notice`), use no real brands.
2. `node scripts/new-piece.mjs spec.json out/piece` (`--dry-run` to preview, `--no-fonts` to stay offline).
3. Serve and LOOK: `node ../premium-web/scripts/verify-piece.mjs out/piece` (sections at 1440 and 390, console, h-scroll).
   Also open `?nogl` (poster path) and `?rm` (reduced motion). Fix the spec or the factory, never the generated files.
4. Add the one wow moment in `bespoke/index.js`; fill art slots via premium-web-imagery; run the critic loop from premium-web.
5. Regenerate after any spec change. The manifest refuses to overwrite a generated file you hand-edited unless `--force`.
6. Run `node scripts/variation-check.mjs <spec-or-piece-dirs...>` across the portfolio before adding a piece.
   Every new piece must use a different grammar OR a different `hero.layout` + `scroll.mode` combination from every existing piece.

## Commands

| Command | Does |
|---|---|
| `node scripts/new-piece.mjs <spec> <out>` | generate or regenerate; prints created/updated/unchanged/kept per file |
| `... --dry-run` | report what would change, write nothing |
| `... --force` | overwrite hand-edited generated files |
| `... --no-fonts` | skip the font fetch (system stacks) |
| `node scripts/new-piece.mjs --selftest` | generate the example to a temp dir and check manifest, idempotence, no-overwrite, validation |

## Choosing a subject kind

| Kind | Look | Fits | Poster/fallback |
|---|---|---|---|
| `glass-lattice` | transmission-glass spheres on rods, wordmark refracted through the glass | dark or light grounds, "structure" concepts | DOM wordmark + gradient ground |
| `point-cloud` | 24k GPU points morphing between layouts, additive glow (ink dots on light grounds) | warm, dense, "swarm" concepts | same |
| `shader-field` | caustic ink flow around item wells, wordmark seen through the flow | atmosphere-first concepts; calm copy zones | same |

Pick the grammar first. Rail has no 3D subject. Within morph-subject pick the kind, hero composition and scroll mode from the concept.

## Hard limits

- Items: 8-256 (shader-field at most 64, enforced); point-cloud takes a third of its points on mobile.
- Morph archetype order is free, but `pricing` and `faq` need `commerce`, and every archetype with a `target` adds one act (one ground
  entry per act in `direction.ground`).
- Rail takes 2–8 panels; optional `chapters` contain only `pricing` and `faq`, rendered vertically after the rail, without targets.
- Terminal takes 2–8 session commands with output lines and pane figures; collage takes words, blocks, palette and collage chapters.
- Specs in `.proofs/` are source fixtures; generated pieces, screenshots and downloaded media remain ignored.
- Omitted `grammar` preserves the original output bytes. New options also emit `spec/piece.json` for the portfolio gate.
- The factory has no CDN at runtime and writes no timestamps. Output is static files; serve over http (file:// blocks modules).
- Do not hand-edit generated files. Extend per `references/extending.md`.

## References

- `references/spec-authoring.md` how to write a spec: fields, layouts, placement, palette, ground, commerce math.
- `references/grammars.md` concept decision table, hero variants, rail fields/params, portfolio gate and verification.
- `references/archetypes.md` each archetype: copy fields, params, mobile composition, the critic fixes it encodes.
- `references/extending.md` bespoke hook, custom subject module, adding an archetype or kind, the write policy.
- `references/when-not.md` when the factory is the wrong tool and what to use instead.
