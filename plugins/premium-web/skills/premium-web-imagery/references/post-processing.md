# Post-processing generated and procedural images

Contents: the pipeline, grade and grain, formats and sizes, budgets, HTML, checks.

Raw provider output is never shipped. Every image goes through the same pipeline so the set matches and the weight stays down.
`template/pipeline.py post <id>` does all steps with the numbers in `imagery.config.json` (`post`).

## Order of operations

1. **Trim** (cut-outs only, `asset.trim: true`): crop the uniform border (alpha, or the matte colour within a small tolerance) and keep a few px of padding. Full-bleed plates are never trimmed.
2. **Matte**: flatten transparency onto the page ground colour so edges do not halo against the page.
3. **Grade**: contrast about 1.04, saturation about 0.95, brightness 1.0 pull generator output (often over-saturated and over-sharp) toward the page palette. Grade the whole set with the same numbers.
4. **Grain**: a seeded mid-grey noise tile, overlay-blended (`grain_amount` 0.03-0.05). It hides banding in dark gradients, unifies generated and procedural assets, and matches the page's own grain layer. Seeded, so reruns are byte-identical.
5. **Resize** to 640 / 1024 / 1536 px wide, never upscaling (a smaller source produces only its own width).
6. **Encode** AVIF (quality about 55) and WebP (about 80); step quality down by 8 until the budget holds, floor 30.
7. **Manifest**: the script prints ready-to-paste `srcset` strings and any budget warnings.

## Budgets (per image, KB)

| Slot | Desktop (1536 w) | Mobile (<= 640 w) |
|---|---|---|
| hero poster | <= 180 | <= 90 |
| section plate | <= 90 (1024 w) | <= 50 |
| backdrop | <= 60 | <= 30 |

Total image weight on mobile <= 900 KB. Dark smooth gradients compress well but band; grain costs bytes and buys the banding back.
Numbers: practice defaults, not measured from references; tune per project.

## HTML

```html
<picture>
  <source type="image/avif" srcset="img/hero-640.avif 640w, img/hero-1024.avif 1024w, img/hero-1536.avif 1536w" sizes="100vw">
  <source type="image/webp" srcset="img/hero-640.webp 640w, img/hero-1024.webp 1024w, img/hero-1536.webp 1536w" sizes="100vw">
  <img src="img/hero-1024.webp" width="1536" height="1024" alt="..." fetchpriority="high" decoding="async">
</picture>
```

- Explicit `width`/`height` (no layout shift). `fetchpriority="high"` on the LCP poster only; `loading="lazy"` on the rest.
- Meaningful `alt` for subjects, `alt=""` for pure atmosphere.
- A dominant-colour or CSS gradient background on the container avoids a flash before decode.
- Art-direct crops for mobile (a different file via `<source media>`), do not just squeeze the desktop plate.

## Compositing text and data

Never generate text. Put real labels, values and numbers in HTML or SVG over the plate. For OG cards, composite the title locally
(Pillow `ImageDraw` with a font fetched at build time, or render an HTML card headlessly and screenshot it) onto the generated background.

## Contrast check on the final crop

Text over a plate must pass the page's contrast target measured on the rendered crop behind the text, not on the plate overall.
If a bright highlight sits under copy, move the copy, darken a gradient scrim under it, or regenerate with a darker region there.

## Quick audit before shipping

- [ ] Every shipped file is in `out/`, produced by the script; no raw PNGs referenced by the page.
- [ ] Budgets met, srcset present, width/height set, one LCP image prioritised.
- [ ] The set viewed side by side: same light, grade, grain.
- [ ] No generated asset committed into a skill or plugin repository; assets live in the user's project only.
