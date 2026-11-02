# Point-morph

`template/src/point-morph.js` + `src/shapes.js`. One `THREE.Points` with three position buffers (start, T1, T2) morphing in the
vertex shader. Verified headlessly: sphere, torus, galaxy states looked at. Numbers measured from public reference sites, 2026-11.

## Contents
- Parameters
- Shaders: what makes it look lit
- Mapping scroll to states
- Shapes
- Mobile and quality
- Mistakes

## Parameters

| Parameter | Value | Provenance |
|---|---|---|
| Points | 20-60k desktop (template 24k), about a third on mobile | measured |
| Transition | 1.1 s ease-in-out when time-driven; scrubbed when scroll-driven | measured, +-0.3 s |
| Idle shimmer | +-2 px (template `shimmer 0.02` world units) | measured |
| Stagger | 70 % of a transition spent staggering points by a stable per-point seed | authored |
| Mid-flight turbulence | swirl displacement peaking mid-transition (`noise 1.4`) | authored; "curl-noise midpoint" measured |
| Pointer coupling | lerp .05, tilt <= .3 rad | measured |
| Spin | 0.9 rad per state, 0.04 rad/s idle | authored |
| Point size | 2.2 at 900 px height, scaled by 26 / depth, clamped 1-22 px | authored |
| Gain | 0.75 | authored: dense cores (galaxy) hit white above about 1 |

## Shaders: what makes it look lit

Flat additive points were the weakest part of an earlier build. The vertex shader therefore derives a pseudo-normal (direction from
the cloud centre) and computes:
- **key light** `diff = max(dot(n, key), 0)` mixing `shade` to `lit` colours;
- **rim** `pow(1 - dot(n, view), 3)` in a pale tint: edges glow like backlit dust;
- **back-face dim** (x0.45) so the far side recedes: reads as volume;
- **fog** by view depth (floor .15) and **size attenuation** by depth;
- sprite falloff `pow(1 - r, 1.7)` in the fragment shader, additive blending, `depthWrite false`.
The cloud sits over the floor-glow backdrop (`src/backdrop.js`), whose warm light matches the key side. Match the key light's
colour to the backdrop or the cloud looks pasted on.

## Mapping scroll to states

`morph = progress * (states - 1)`. Segment `i` blends state `i` to `i+1` with a smoothstep ramp offset by the point seed, so points
leave one after another. `offsetX[i]` moves the cloud beside the copy of each chapter (desktop); portrait moves it to the upper
half at 55 % scale so the copy sits below it. Drive `progress` from page scroll (default) or `stage.setProgress` from a pinned stage.

## Shapes

`sphere, torus, galaxy, helix, text(str), image(img), mesh(positions)` return `Float32Array(n * 3)`, seeded (`mulberry32`) so every
device draws the same picture. Random order matters: the governor's `setDrawRange` cut then thins the cloud uniformly. For a word
or logo use `text` or `image` (density follows alpha x luma). The subject's shape should be the page's subject, not a stock sphere.

## Mobile and quality

`count.mobile` is chosen in `init` from `ctx.mobile`; the governor lowers `quality.count` (draw range) if the median frame exceeds
22 ms. DPR is capped by the stage. `uPx` multiplies point size by DPR and canvas height so the picture is resolution independent.

## Mistakes

- Same colour everywhere: with no `shade`/`lit` gap the light has nothing to show.
- Cloud behind the headline: put the object beside the copy (`offsetX`) or fade it where copy crosses it; in portrait keep it above.
- More points instead of better light: 60k flat points look worse than 20k lit ones.
- Mutating the camera from the scene: use `stage.onFrame` for camera keys so scenes stay composable.
