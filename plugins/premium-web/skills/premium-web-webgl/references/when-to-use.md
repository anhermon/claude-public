# When to use 3D or a shader, and when not

Provenance: budgets and counts are measured from public reference sites, 2026-11 (+-15 %) unless marked "authored".

## Contents
- The test
- Choosing the class
- Budgets
- Failure modes this prevents

## The test

A scene earns its place only if it passes all four:
1. **It is the page's ONE persistent subject** (or a calm atmosphere behind it). Not decoration in a corner.
2. **Scroll or pointer changes it** in a way that says something (a shape becoming another, a light moving, a state arriving).
3. **A poster exists** that is already a good page (CSS gradient or procedural image) so LCP, no-WebGL and reduced motion keep the design.
4. **Copy stays legible** over every frame at 390 px and 1280 px.

If one fails, do not ship WebGL. Spend the time on type, imagery or an SVG figure.

## Choosing the class

| Class | Good for | Cost | Notes |
|---|---|---|---|
| Point-morph (20-60k points) | abstract subject that transforms: concept, dataset, brand shape | low (one draw call) | needs lighting, fog, rim to avoid flat look |
| Shader field (full-screen quad) | colour world, atmosphere, section backgrounds | low at renderScale .15-.5 | grain and dither are part of the look |
| Glass / physical material | a tangible object, product-like hero | medium (transmission renders the scene twice) | needs an environment to refract |
| Particle field 100-250k | dust, rain, galaxy fills | medium | GPU-driven only; no per-frame JS loops |
| Raymarched SDF | organic characters, liquid | high | use `animated-objects:raymarched`, not this skill |
| Modelled character | mascot, creature | n/a | use `animated-objects:threejs` |

## Budgets

| Item | Value | Source |
|---|---|---|
| DPR cap | 2 desktop, 1.5 mobile | measured |
| Mobile point count | about one third of desktop | authored (a built demo used 36k desktop / 9.4k mobile) |
| Frame budget | median <= 22 ms, else degrade DPR then count | measured |
| Colour field internal resolution | 0.15-0.5 of CSS size, upscaled | measured |
| Colour field rate | 30 fps is enough; visible-only | measured |
| First frame | poster visible immediately; canvas fades in after the first good frame | authored, proven in a built page |

## Failure modes this prevents

- Canvas used as wallpaper: the scene does not respond to anything, so it adds weight and no meaning.
- No fallback: blank hero on a software renderer, a low-power laptop or a blocked context.
- Raw point cloud: additive points with no light read as noise.
- A second renderer per effect: two contexts, double the cost, jank on mobile.
