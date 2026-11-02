# SVG filters and generative patterns

Authored starting values. `template/filters.html` renders gooey, displacement and grain (Chromium, frames looked at). Patterns
and animated filters below are snippets, NOT run here.

## Contents
- Filters
- Costs and limits
- Generative patterns
- Mistakes

## Filters

| Effect | Recipe | Starting values |
|---|---|---|
| Gooey | `feGaussianBlur` then `feColorMatrix` with alpha row `0 0 0 18 -7` | stdDeviation 8, region x/y -20 %, w/h 140 % |
| Displacement | `feTurbulence` (fractalNoise) into `feDisplacementMap` | baseFrequency `.012 .04`, numOctaves 2, scale 14 (<= 20 keeps text legible) |
| Grain | `feTurbulence` baseFrequency .9, `feColorMatrix saturate 0`, alpha table `0 .22`, `feBlend multiply` | static; seed fixed so it does not shimmer |
| Glow | `feGaussianBlur` on a copy, `feMerge` under the source | stdDeviation 4-10 |
| Duotone | `feColorMatrix` mapping luma to two colours | for raster images placed in SVG |

Turbulence is deterministic for a given seed, so a static filter is a texture, not an animation.

## Costs and limits

- Filters rasterise their region at the current scale and repaint on any change. Keep the filter region tight, apply to a group,
  not to the whole page, and do not animate `baseFrequency` or `stdDeviation` on large areas (use CSS transform on the filtered group instead).
- `feTurbulence` is CPU-heavy on large areas in some browsers: render grain once into a tile and reuse, or use the shader grain from `premium-web-webgl`.
- Safari and Firefox differ on filter region defaults and colour space (`color-interpolation-filters="sRGB"` for predictable colour). NOT tested here.
- A page-wide moving grain belongs in CSS/WebGL finishing, not an SVG filter.

## Generative patterns

Seeded, so every build draws the same picture: `mulberry32(seed)` for jitter; a `<pattern>` for repeats. Three starting forms:
- **Dot grid with luma:** rows of circles whose radius follows a function of position (`r = 1 + 2.5 * smooth(noise(x, y))`).
- **Contour lines:** N sine iso-lines `y = a*sin(kx + phase_i)` with `stroke-width` 1 and falling opacity; draw-on in order.
- **Truchet or tile grid:** a 2-state tile chosen by `rng() > .5`, 24-40 px cells.
Keep under about 2,000 elements (file size and paint); beyond that use a canvas or shader (`premium-web-webgl`).

## Mistakes

- A filtered `<text>` headline: distortion plus small sizes kills legibility; filter a decorative layer behind it.
- Pattern with visible tiling seams: use whole-number cell sizes and `shape-rendering="crispEdges"` for hard grids.
- Colour values hard-coded in a pattern: use `currentColor` or CSS variables so themes work.
