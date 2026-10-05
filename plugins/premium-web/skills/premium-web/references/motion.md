# Motion

- **UI feedback** .15-.2s; **reveals** .6s, ease cubic-bezier(.2,0,0,1), 12px rise, stagger 60ms via `--i`.
  Cinematic pages may slow reveals to .8-1.2s. Nothing bounces.
- **Reveals use IntersectionObserver** (`assets/skeleton/reveal.js`): scroll-driven CSS (`animation-timeline`)
  works only from iOS 26; the Simulator's Safari UA is frozen at "iPhone OS 18_7", so never UA-sniff, feature-detect.
- Reveal content is visible without JS: the `.js` class gates the hidden state.
- **Scroll scenes**: `assets/recipes/scroll-scene.js` (sticky stage, IO + passive scroll + one rAF writing `--p`
  and `data-step`). See wow.md.
- **WebGL hero** (`assets/skeleton/hero-strands.js`): poster `<img>` is the LCP element and the fallback; canvas
  fades in after its first good frame (`html[data-hero="gl"]`). Falls back to the poster on reduced motion,
  Save-Data, no WebGL, `webglcontextlost`, or the slow-frame watchdog (> 60 of the first 90 frames over 24ms).
  URL flags force each path: `?rm ?savedata ?nogl ?slow`. DPR capped 1.5 touch / 2 desktop; paused off-screen
  and on hidden tabs. Deterministic seed: same picture on every device.
- **prefers-reduced-motion**: no transforms, no auto-play, final states shown; the page must still look finished.
- 60fps: animate `transform`/`opacity` only; no layout-triggering properties per frame; no scroll-jacking.
- What the Simulator cannot tell you: real fps, Low Power Mode, thermal throttling. Use `?slow` to prove the
  watchdog path; test on a real phone before launch if the wow is GPU-heavy.

## Polish checklist for the signature interaction (Angel on ember r2's Rail: "nice, the animation needs a bit more polish")

A signature moment is judged **in motion**, not at rest. Before the critic sees it, check each item on the
mid-animation frames (`WOW=<sel>` captures 7 time frames or 6 scroll positions; `WOW_ACT=<js>` starts an
interaction such as a click or replay first):
- **Easing and settle**: every moving thing eases out (cubic-bezier(.2,0,0,1) or a critically damped spring) and
  comes to rest exactly once: no overshoot wobble, no linear slide, no stop-start between beats, no element still
  drifting after its label appears. Stagger groups (40-80ms), never everything at once.
- **Particle budget**: at most ~2,500 points on touch and 6,000 on desktop (particles.js), fewer when each point
  glows. Points are information (one per real item) or they are cut; no ambient dust.
- **No particles over text**: points, trails and glows stay out of the text column's box and never pass behind a
  label; reserve the region (`region()` in the recipe) and clip to it. The reverse also counts: beat text that
  scrolls with its step slides across the canvas, so beat text lives inside the sticky stage (scroll-scene.js).
- **When the field becomes a word** (`textPoints()`, particles.js), keep a residue where the story says the thing
  stays (sealref: the keystore keeps its copy, the child keeps its env) so no box is left empty mid-sequence.
- **Glow never muddies labels**: additive glow/bloom sits under labels, with labels on an opaque chip or with a
  2-4px halo in the ground colour; label contrast stays >= 4.5:1 on every frame, not only the last one.
- **Half-drawn states look intentional**: in a mid-frame nothing is clipped, overlapping, or half-faded into a
  smear; a stroke being drawn has a visible head; numbers count with tabular figures, not jittering widths.
- **Beat text never double-exposes**: when beats swap, the old text is fully out before the new one starts
  (out .2s, then in .3s with a .2s delay; or a hard swap), never two headlines cross-fading over each other. Both
  acceptance pages failed motion_polish 3 on exactly this (sealref r8 t2/t4/t6 headline ghosts; Plumb r8 h1 under the nav).
- **One focal motion at a time**: while the signature plays, nothing else on screen animates.
- **Frame-sequence review**: open all mid frames yourself, then run the critic (`critic.py --wow`), which scores
  motion polish from the same frames. A good last frame with a messy middle fails.

## Transitions, captures and the static fallback (ember v3 skill gaps)

- **Scene transitions stay under 0.7s** (beat swaps, sheet registration passes, text swaps). chrome-shot captures frames at
  fixed offsets (250/700ms after a beat boundary), so anything longer is shot mid-flight and the critic reads garbled
  overprint text or half-faded copy as a polish collision. If the signature needs a longer, slower pass (a registration
  pass of 1.2-2s), keep the TEXT out of the moving layer: only shapes move, labels swap hard or fade in after the settle,
  and every intermediate frame must be a legible, intentional state.
- **Reduced-motion / static fallback is part of the design.** Freeze on the most informative beat (the one that shows the
  claim: the diff, the drift), not the resolved last frame, and lay the poster out deliberately (a stack of the beats
  or one beat plus a caption). The critic scores the fallback as its own dimension.
- Wrap sticky headers' height into scroll offsets (`scroll-margin-top`); chrome-shot hides sticky/fixed headers in section
  shots and offsets WOW scrolls by the measured header height.
