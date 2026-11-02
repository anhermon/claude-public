// One place for every tunable. Edit this file; src/ never needs touching for a new page.
// Provenance (one line each): "measured" = measured from public reference sites, 2026-11; "authored" = a starting value to tune by eye.
export const WEBGL_CONFIG = {
  stage: {
    backdrop: 'fire',          // authored: 'fire' | 'aurora' | 'cobalt' (floor-glow palettes in src/backdrop.js); or pass your own palette object
    exposure: 1,               // authored
    cameraPos: [0, 0, 12],     // authored
    fov: 40,                   // authored
    budgetMs: 22,              // measured: governor degrades DPR then point count when the median frame exceeds this (~45 fps floor), +-3 ms
  },
  pointMorph: {
    count: { desktop: 24000, mobile: 8000 },   // measured: 20-60k on desktop; mobile share is authored (about a third)
    shapes: [{ type: 'sphere', R: 3 }, { type: 'torus', R: 2.3, tube: 1 }, { type: 'galaxy', R: 3.8, rotation: [0.7, 0, 0.2] }],   // one per scroll state: a sampler name in src/shapes.js, { type, ...options } or a Float32Array
    offsetX: [3, -3, 3],                       // authored: world x per state, so the cloud sits beside the copy; ignored in portrait
    portraitLift: 2.4, portraitScale: 0.55, portraitSizeScale: 0.9,   // authored: portrait shrinks the cloud and lifts it into the upper half, clear of the copy
    size: 2.2,                                 // authored: point size at 900 px canvas height, 26 units from the camera
    shimmer: 0.02,                             // measured: +-2 px idle shimmer (about 0.02 world units here)
    noise: 1.4,                                // authored: mid-flight turbulence amplitude
    gain: 0.75,                                // authored: overall brightness; dense cores (galaxy) saturate to white above about 1
    rim: 0.9,                                  // authored: rim-light strength (the cure for flat additive points)
    key: [0.5, 0.8, 0.6],                      // authored: key-light direction
    colors: { lit: '#ffd9a0', shade: '#c0431f', rim: '#fff1d6' },   // authored
    tiltMax: 0.3, pointerLerp: 0.05,           // measured: pointer coupling lerp .05, tilt <= .3 rad
    spin: 0.9, idleSpin: 0.04,                 // authored: radians per state, radians per second
    boundingRadius: 80,
  },
  field: {
    kind: 'colorField',        // 'colorField' | 'ribbon'
    palette: ['#05060a', '#1b2a6b', '#2f6fd1', '#8fd3ff', '#f4f1ea'],   // authored: 5 stops, dark to light, mixed in OKLab
    renderScale: 0.5,          // measured: colour fields render at 0.15-0.5 of CSS size and are upscaled
    timeScale: 1, staticTime: 6, grain: 0.05,   // measured: grain ~6 %; static frame for reduced motion is authored
    scale: 2.2, warp: 1.6, glow: 0.012,          // authored; glow 0.01/abs(f) measured for ribbons
    poster: 'linear-gradient(135deg, #05060a, #1b2a6b 55%, #2f6fd1)',   // authored: CSS shown with ?nogl and while loading
  },
};
