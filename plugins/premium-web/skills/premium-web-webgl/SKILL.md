---
name: premium-web-webgl
description: >
  3D and shader scenes for premium web pages, measured from public cinematic reference sites: the stage rig (one fixed canvas
  behind scrolling DOM, scroll-progress uniform, poster, DPR cap, visibility pause, context loss, no-WebGL and reduced-motion
  paths), point-morph clouds, glass clusters, and shader fields (colour field, glow ribbon/strand, halftone/dither,
  pointer-reactive, reeded-glass refraction), plus lighting, material and finishing rules (key and rim light, fog, grain, glow,
  environment) and headless-GPU capture. Use for "add a 3D hero", "WebGL background", "particle morph", "shader background",
  "gradient mesh", "glass object", "three.js scene", "the page needs a persistent hero object", "scene renders blank headless".
  Do NOT use for characters, mascots or hand-modelled objects (animated-objects:threejs, animated-objects:raymarched), for
  DOM scroll choreography, text reveals or preloaders (premium-web-motion), for code-drawn diagrams or SVG (premium-web-svg),
  for generated images or video (premium-web-imagery), or for page strategy (premium-web).
metadata:
  version: "0.1.0"
---

# WebGL: one persistent object, lit, with a fallback

A premium page has ONE persistent hero subject. When that subject is abstract (a field of points, glass, light, a shader),
build it here. The look comes from finishing (light, depth, grain), not from the point count. Numbers are measured from public
reference sites (2026-11); `template/` is working, config-driven code with three.js r170 vendored (MIT) and no CDN.

## Decision table

| The subject is | Use | Template |
|---|---|---|
| A shape that changes with scroll (logo, product, concept) | point-morph, 20-60k points, 3-4 states | `src/point-morph.js` |
| Atmosphere, colour world, behind or between sections | shader field (colour field, ribbon) on its own canvas | `src/field.js` |
| A tangible object (glass slab, ring, cluster) | MeshPhysical glass over the floor-glow backdrop | reference only |
| A character, mascot, hand-modelled prop | stop: `animated-objects:threejs` or `:raymarched` | none |
| A diagram or figure that teaches a claim | stop: `premium-web-svg` | none |
| A photo or video look | stop: `premium-web-imagery` | none |
| Nothing the scene would say | no WebGL; spend the budget on type and imagery | none |

## Workflow

1. **Decide** with `references/when-to-use.md`. Write the subject, the 3-4 scroll states, the palette and the fallback in one line each.
2. **Copy** `template/` next to the page. Edit only `webgl.config.js`; add shapes in `src/shapes.js` if needed.
3. **Stage first.** `init(document.body, {...})` gives the fixed canvas, poster, DPR cap, governor, pause, context loss
   (`references/stage-rig.md`). Never create a second renderer for a second scene; add scenes to the stage.
4. **Scene.** Point-morph: `references/point-morph.md`. Fields: `references/shader-fields.md`. Glass: `references/glass-and-finishing.md`.
5. **Finish** before judging: key light, rim light, fog, grain, glow, a floor-glow backdrop. Flat additive points read cheap.
6. **Fallbacks** are part of the scene, not extras: `?nogl` poster, `?rm` static frame, mobile count and DPR, copy readable in all.
7. **Verify** (below). Do not report done on a passing script alone.

## Verification loop

```
cd template && PLAYWRIGHT_NODE=<dir containing node_modules/playwright> node selftest.mjs
```
It launches system Chrome with `--use-angle=metal --ignore-gpu-blocklist` (without them headless WebGL returns blank or
software frames), checks gl / `?nogl` / `?rm` / `?slow` governor / context loss and restore / 390 px mobile, and measures
frame time (p50, p99). Frames land in `.selftest/`: open them and LOOK. State what you saw for each scroll state.
Details and Linux flags: `references/headless-verification.md`.

## Hard rules

- Canvas behind content: `pointer-events: none`, `aria-hidden`, text always a real DOM element on top; canvas text only with a halo and 12 px minimum.
- DPR cap 2, mobile 1.5 and a third of the points; pause off-screen and on hidden tab; one rAF loop.
- Poster first for LCP (CSS gradient or a procedural image); the canvas fades in after its first good frame.
- Reduced motion: one static frame at the current progress, no loop, no pointer coupling.
- Colour in shaders is authored sRGB; mix gradients in OKLab; add dither so dark ramps do not band.
- No CDN, no fonts, no generated textures bundled; vendored libs go in `vendor/LICENSES.md`.

## What is verified

Verified headlessly on macOS Chrome (Metal), frames looked at: stage modes, point-morph (3 states), colour field, ribbon field,
governor, context loss and restore, 390 px mobile.
NOT verified: glass cluster and halftone/reeded recipes (reference snippets only), real-device frame rate (headless lab
only), pointer coupling with a real mouse, Linux/Windows GPU flags.

## Pointers

- `references/when-to-use.md`: 3D vs shader vs nothing; budgets; asset-plan class.
- `references/stage-rig.md`: fixed canvas, scenes, modes, governor, options.
- `references/point-morph.md`: shapes, shader, lighting, scroll mapping, parameter table.
- `references/shader-fields.md`: five field recipes with GLSL and budgets.
- `references/glass-and-finishing.md`: glass cluster, light, material, grain, glow, env.
- `references/headless-verification.md`: GPU flags, frame-time method, failure modes.
- Companion skills: `premium-web-motion` (DOM choreography, drives `stage.setProgress`), `premium-web-imagery` (poster images).
