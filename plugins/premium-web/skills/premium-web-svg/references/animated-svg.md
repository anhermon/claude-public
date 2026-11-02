# Animated SVG

Starting values are authored (no measured corpus). Easing is the expo-out used across this plugin (measured for UI motion, see
`premium-web-motion`). Verified: draw-on, fade, scaleX, triggers, reduced motion. NOT run: path morph, SMIL, masks.

## Contents
- Pick the technique
- Draw-on
- Path morphing
- Masks and clips
- Triggers and scroll
- Reduced motion
- Performance
- Parameters

## Pick the technique

| Technique | Use when | Avoid when |
|---|---|---|
| CSS animation / transition | draw-on, fades, transforms, hover states; works in inline SVG and standalone files | the animation needs sequencing logic from data |
| SMIL (`<animate>`) | the SVG must animate inside an `<img>` or CSS background and CSS cannot (rare); `animateMotion` along a path | anything that needs reduced-motion handling in the page; SMIL ignores `prefers-reduced-motion` unless you add the media query inside the SVG file |
| JS (WAAPI, rAF) | scroll-scrubbed progress, path morphing with interpolation, data-driven sequences | a one-shot reveal CSS can do |
| Scroll timeline | a figure scrubbed by scroll: set `--p` on the svg from the motion skill's stage and use `calc()` in CSS | time-driven reveals (those play once, not scrubbed) |

Default: CSS inside the SVG. It survives being a standalone file, needs no JS, and the generator emits it.

## Draw-on

Give each path `pathLength="1"`, then `stroke-dasharray: 1; stroke-dashoffset: 1` animating to `0`. `pathLength` makes the dash
independent of the real length, so one keyframe serves every path. Only stroked paths draw on; for filled shapes fade or clip-reveal
(`clip-path: inset()` animating), or draw the outline then fade the fill in. Order delays in reading order.

## Path morphing

Two paths morph only if they have the same number and types of commands. Author both with the same structure (same `C` count) or
resample both to N points in JS and interpolate. CSS `d: path()` transitions work in Chromium, not everywhere: ship a JS
interpolation (WAAPI keyframes on a `d` attribute string is not portable) or use opacity cross-fade as the fallback. NOT run here.

## Masks and clips

`clip-path` for hard reveals (wipe, iris); `<mask>` with a white-to-black gradient for soft edges; animate the mask shape's
transform, not its path. Masks force offscreen compositing: keep them small and few. NOT run here.

## Triggers and scroll

`trigger: "load"` for standalone files and above-the-fold figures. `trigger: "inview"` plays when 30 % of the figure is visible
(IntersectionObserver in `figure.js`, 10 % bottom margin); the hidden state exists only under `.pending`, which JS adds, so without
JS the figure is simply drawn. Never hide the figure in static CSS.

## Reduced motion

`@media (prefers-reduced-motion: reduce)` is inside the generated SVG: no animation, final state. `figure.js` also skips adding
`.pending`. A looping decorative animation (pulse, flow dots) is removed entirely under reduced motion.

## Performance

- Animate `stroke-dashoffset`, `transform`, `opacity`. Not `d`, not filter parameters, not `width`.
- Under about 200 animated elements per figure; no per-frame JS for a one-shot reveal.
- Pause infinite loops off-screen (`animation-play-state` via IO) and never animate a filter region larger than the figure.

## Parameters (authored starting values; tune on the render)

| Parameter | Value | Note |
|---|---|---|
| Node stagger | 300 ms | reading order; whole figure under about 2.5 s |
| Draw | 600 ms | edge draws between its two nodes |
| Fade | 500 ms | nodes, arrows, labels, callouts |
| Bar grow | 700 ms, 120 ms stagger | scaleX from the left |
| Easing | `cubic-bezier(.16,1,.3,1)` | expo-out |
| In-view threshold | 0.3 | share of the figure visible |
