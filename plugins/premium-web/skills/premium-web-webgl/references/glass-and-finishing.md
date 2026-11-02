# Glass cluster, lighting, material and finishing

Glass is a reference recipe (NOT in the template, NOT run here). The finishing rules ARE applied in the template
(backdrop glow, grain, dither, key/rim/fog in point-morph) and were looked at. Numbers measured from public reference sites, 2026-11.

## Contents
- Glass cluster
- Floor-glow backdrop
- Lighting and material rules
- Finishing layer
- Banned defaults

## Glass cluster

A group of 3-9 rounded slabs or spheres with transmission, floating in front of a glowing backdrop.
```js
new THREE.MeshPhysicalMaterial({ transmission: .9, thickness: .6, roughness: .25, ior: 1.45, color: '#ffffff', envMapIntensity: 1 });
```
- Transmission only shows what is BEHIND the glass in the scene: the backdrop must be a real opaque object in the scene (the
  template's `createBackdrop` mesh is), not a CSS background, or the glass refracts black.
- Add an environment (`PMREMGenerator` over a gradient scene that matches the backdrop glow) or the glass looks like grey plastic.
- Pointer coupling lerp .05, tilt <= .3 rad; scatter-to-grid assembly 1.6 s `expo.out` on entrance (measured, +-0.3 s).
- Cost: transmission renders the scene again; keep slabs <= 9 and let the governor lower DPR on mobile (authored).

## Floor-glow backdrop

`radial-gradient(ellipse 80% 55% at 50% 100%, hot, mid, deep, #020101)` plus about 6 % noise, breathing +-5 % over about 6 s
(all measured). `src/backdrop.js` renders it as a shader quad with grain and dither and exports the same gradient as CSS for the poster
(`backdropToCss`), so the poster and the live frame match. Palettes shipped: `FIRE`, `AURORA`, `COBALT`; hand-off between chapters:
`stage.backdrop.setMix(t)` with a second palette (time-driven tween, 0.7 s).

## Lighting and material rules

1. One key light, one rim light, one environment: three sources, never a rainbow of point lights.
2. Key and backdrop warm side agree. Cold rim on warm glow (or the reverse) is the cheapest way to look expensive.
3. Every surface needs a gap between shade and lit colour; equal values read flat.
4. Fog or depth attenuation always on: far things darker, near things larger.
5. Rough (.25) beats mirror-smooth; perfectly clean glass reads CG.
6. Tone mapping: ACES filmic exposure 1 on three.js materials; custom shaders output authored sRGB, so match by eye, not by number.

## Finishing layer

| Layer | Value | Provenance |
|---|---|---|
| Grain | 0.05 amplitude, applied after sRGB encode | measured, +-30 % |
| Dither | triangular, 1/255 | authored |
| Glow | additive, `0.01 / abs(f)` for lines; bloom only on desktop | measured (lines) |
| Vignette | 20-35 % at corners | authored; verify on the render |
| Env | gradient env matching the backdrop | measured |

## Banned defaults

- Default `MeshStandardMaterial` grey with the three.js default lights.
- Black or white clear colour with no glow, grain or vignette.
- A rotating object with no relation to scroll or pointer.
- Neon gradient points with no depth cue.
- Bloom everywhere: it hides the shape you spent the shapes budget on.
