# Extending the factory

Rule: fix at the source, regenerate, diff. Never edit generated files; the manifest refuses it.

## Per piece: the bespoke hook

`bespoke/index.js` is created once and never overwritten (mode `user` in the manifest). It runs after the stage and subject are
live: `export default function bespoke({ piece, subject, stage, motion, root })`. Put the one signature moment here (see premium-web
`references/wow.md`). Guard with `subject.live`: the subject is inert when WebGL is off. Subject API: `setAct`, `setMask(fn)`,
`setCustom({fn(time, out)})`, `setHover(group, k)`, `setPark(bool)`, `setHide(bool)`, `setDrive({stretch})`, `groupOf(i, k)`,
`itemName(i)`, `assemble()`, `scan.top`.

## A different subject: custom-module

`"subject": { "kind": "custom-module", "module": "bespoke/my-subject.js" }` imports your module, which exports
`createSubject(piece, { mobile })` returning the API above plus `scene` (a stage scene). Every archetype still works because they
talk to the API only.

## A new archetype

1. `archetypes/<id>.mjs`: export `meta {id, needsTarget, needsCommerce, copyRequired, params, doc}`, `render(ch, piece, env)`, `css(piece, ch)`.
   Use `_shared.mjs` helpers (`actOpen`, `h2`, `deck`, `mq`). Give it a mobile composition in `css`.
2. Register it in `archetypes/index.mjs`.
3. `runtime/archetypes/<id>.js`: export `mount(el, { subject, piece, ch })` returning `{enter?, leave?}`. Reset anything you set on the
   subject in `leave`.
4. Add it to `spec.schema.json` (enum) and `references/archetypes.md`; add a chapter to a spec and look at 1440 and 390.

## A new subject kind

1. `runtime/subjects/<kind>.js` exporting `create(core, piece)` returning a stage scene. Use `core.frame`, `core.view`, `core.keys`,
   `core.litStep`, `core.query`, `core.asm` and `core.onWorld` as the three existing kinds do. Honour `st.mask`, `st.custom`,
   `st.hideV` (already applied to `key.s`), `st.parkV`, `st.stretchV`.
2. Add defaults to `SUBJECT_DEFAULTS` in `scripts/lib/const.mjs` and the kind to the schema enum.
3. The generator copies only the used kind. Keep each file under 800 lines.

## Write policy

`.factory-manifest.json` records a sha256 per generated file. On regeneration: unchanged files are skipped, files still matching their
recorded hash are updated, hand-edited files are refused (all listed) unless `--force`, user-owned files are kept, files dropped by
the spec are removed only if untouched. `fonts/` is fetched before the write and is never treated as foreign content. The generator
fails loudly if the motion template changes shape: it patches `motion.js` to call `config.onReveal` so the curtain lifting can start
the subject assembly.

## Tests

`node scripts/new-piece.mjs --selftest` covers generation, manifest, idempotence, bespoke preservation, hand-edit refusal, `--force`,
validation and the prefetched-fonts case. Run it after any change to `scripts/`. Look at a render after any change to `runtime/` or
`archetypes/`: no test substitutes for that.
