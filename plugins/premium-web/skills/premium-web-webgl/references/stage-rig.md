# The stage rig

`template/src/stage.js`. One fixed full-viewport canvas behind the scrolling DOM; scenes register on it.
Technique and numbers measured from public reference sites, 2026-11.

## Contents
- API
- Modes
- Options (defaults)
- Scroll progress
- Governor
- Poster and LCP
- Gotchas

## API

```js
import { init } from './src/stage.js';
const stage = init(document.body, { backdrop, zIndex: -1 });
stage.addScene({ root, init(ctx){}, update(ctx){}, resize(ctx){}, setQuality(q, ctx){}, restore(ctx){}, dispose(){} }, { range: [0, 1] });
stage.onFrame((ctx) => {});    // camera keys, uniforms; runs before scenes
stage.setProgress(p);          // manual progress, e.g. from the motion skill's pinStage; setProgress(null) returns to scroll
await stage.ready;             // resolves with the mode
stage.stats();                 // { mode, frames, p50, p99, dpr, quality, degrades, running }
stage.destroy();
```
`ctx` carries `THREE, renderer, scene, camera, size, dpr, time, dt, progress, velocity, reduced, mobile, pointer, quality`.

## Modes

| mode | when | behaviour |
|---|---|---|
| `gl` | WebGL works, motion allowed | rAF loop, poster fades out after the first frame |
| `static` | `prefers-reduced-motion` or `?rm` | renders one frame on scroll or resize, no loop, no pointer coupling |
| `poster` | no WebGL, `?nogl`, renderer or three import failed | CSS poster only; canvas hidden; page fully usable |
| `pending` | booting | poster shown |

Context loss: the poster returns, the loop stops; on `webglcontextrestored` scenes get `restore(ctx)` and the loop resumes.

## Options (defaults)

`dprMax 2`, `dprMaxMobile 1.5`, `mobileMaxWidth 768`, `budgetMs 22`, `budgetWindow 40` frames, `warmupFrames 40`,
`dprStep 0.8`, `dprMinAbs 0.75`, `countStep 0.25`, `countMin 0.4`, `scrollLerp 0.08`, `fov 40`, `cameraPos [0,0,12]`,
`exposure 1`, `zIndex 0`, `fixed true`, `backdrop FIRE`, `poster null` (derives a CSS gradient from the backdrop), `reduced` (override).
Provenance: DPR caps, 22 ms median and 0.08-0.1 scrub damping measured from public reference sites, 2026-11; the step sizes are authored.

## Scroll progress

By default the stage reads page scroll (`scrollY / (scrollHeight - innerHeight)`) and damps it (`scrollLerp`). To bind it to one
pinned section instead, pass `scroll: { progress: () => p, on: (fn) => unsubscribe }` or call `setProgress`. Scrub is damped;
chapter palette hand-offs are time-driven (see `premium-web-motion`), never scrubbed.

## Governor

Every `budgetWindow` frames the median frame time is compared with `budgetMs`. Above it: DPR scale x0.8 down to `dprMinAbs`, then
`quality.count` -0.25 down to `countMin`. Scenes apply `count` in `setQuality` (point-morph uses `setDrawRange`). Test with `?slow`
(budget forced to 1 ms) to prove the path runs.

## Poster and LCP

The poster is a `div` with a CSS background (default: the backdrop gradient) or any element. It is the LCP element; keep it
a gradient or a procedural SVG. Do not use a bundled generated image.

## Gotchas

- `body { background }` paints over a `z-index: -1` stage when `html` also has a background. Put the page background on `html` only.
- `resize(ctx)` can run before a scene's `init`; guard against missing GPU objects (the template scenes do).
- Do not call `renderer.render` yourself; the stage owns the loop. Anything per-frame goes in `update(ctx)`.
- Pointer coupling lerp .05 and tilt <= .3 rad (measured); anything larger fights the copy.
