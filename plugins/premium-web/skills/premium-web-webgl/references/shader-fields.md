# Shader fields

Full-screen fragment shaders on a raw WebGL2 canvas (`src/fx-canvas.js`; no three.js). Template kinds: `colorField`, `ribbon`
(both verified headlessly, frames looked at). The other three below are recipes (snippets, NOT run here).
Numbers measured from public reference sites, 2026-11.

## Contents
- The shared helper
- Colour field
- Glow ribbon / strand
- Halftone / dither
- Pointer-reactive
- Reeded-glass refraction
- Budgets and parameters

## The shared helper

`createFx(target, { frag, chunks, uniforms, renderScale, poster, ... })` gives a fullscreen triangle, readable shader errors
(type, driver message, offending lines), cached uniforms, DPR cap 2 (mobile 1.5), IntersectionObserver and tab-visibility pause,
resize, context loss rebuild, `?nogl` poster fallback, reduced-motion static frame (`staticTime`), and `fx.frameTimes()`.
GLSL chunks (`fx-glsl.js`): `GLSL_HASH`, `GLSL_NOISE` (value noise, `fbm`, `fbm3`), `GLSL_OKLAB`, `GLSL_FINISH` (grain + sub-LSB dither,
applied AFTER sRGB encode). Always call `finish()` last: without dither dark ramps band at 8 bit.

## Colour field

Low-frequency fbm, domain-warped, mapped through a 4-5 stop palette mixed in OKLab. Measured: about 160 px wide render
(`renderScale .15-.5`) blurred about 2.5 rem on upscale, 4-5 stops, 30 fps, visible-only, grain about 6 %. Pass palettes dark to light;
a colour field as a section background must keep copy contrast: check the lightest region against the text. Slow drift only
(`uTime * .05`); fast motion in a field reads as a screensaver.

## Glow ribbon / strand

`col += glowColor * 0.01 / (abs(f) + eps)` for each of 4-8 domain-warped sine iso-lines, then `1 - exp(-col)` tonemap (measured:
glow .01/abs(f)). Strand variant (a bundle of 40-120 additive curves with bloom, fading in 1.2 s after a 2 s delay, measured): draw
`gl.LINES` along a cubic bezier with per-strand seed and lane offset, additive blend `ONE, ONE`, canvas `mix-blend-mode: screen` over a poster.
The head of each strand brightens as an "exposure" front moves along `t`. Keep strands at 420 desktop / 180 touch (authored, from a built page).

## Halftone / dither

Ordered-dither or halftone in 3 colours, dot 2-4 px (measured), cell about 6 px for halftone with radius `(0.15 + 0.5 * luma) * cell`.
```glsl
vec2 c = floor(gl_FragCoord.xy / CELL); vec2 f = fract(gl_FragCoord.xy / CELL) - .5;
float r = (.15 + .5 * luma) * .5;  float dotMask = smoothstep(r, r - .08, length(f));
```
Source luma from a procedural field (the colour field) or a texture uploaded with `fx.texture('uImg', img)`.

## Pointer-reactive

Feed `uPointer` (-1..1) from `pointermove` on the host (the template does) and warp the sampling domain:
`p += uPointer * .25` (colour field) or offset iso-lines (ribbon). Lerp the uniform in JS (.05) for inertia. No pointer on touch: use
a slow autopilot instead of nothing, or the field looks dead on phones.

## Reeded-glass refraction

Vertical flutes over an image or field: `float cell = floor(uv.x * FLUTES); float k = fract(uv.x * FLUTES) - .5;`, refract the sample
by `k * depth` horizontally, split R/G/B by a dispersion of about .1 of that offset (measured), add a thin specular on each flute edge.
Needs the content below it as a texture: render the colour field into a texture (`fx` extra pass) first. NOT run here.

## Budgets and parameters

| Item | Value | Provenance |
|---|---|---|
| Effect parameters exposed | about 6 sliders per effect | measured |
| DPR cap | 1.5-2 | measured |
| Offscreen | pause (IO) | measured |
| Reduced motion | static frame at `staticTime` | measured |
| WebGL2 missing | CSS poster, same layout | measured |
| Grain | 0.05 amplitude (measured, +-30 %); 24 fps steps and midtone weighting | amplitude measured; steps and weighting authored |
