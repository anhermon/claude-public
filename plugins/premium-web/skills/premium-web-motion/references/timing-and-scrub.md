# Timing, easing, stagger and what to scrub

Contents: easing table, duration table, stagger table, scrub vs time-drive, scroll source, assembling a page's motion spec.

Provenance: measured from 16 public cinematic reference sites, 2026-11; +-0.3 s (10 fps sampling) unless marked practice.

## Easings

| Name | CSS | Use |
|---|---|---|
| expo.out | `cubic-bezier(0.16, 1, 0.3, 1)` | almost every entrance and reveal; fast start, long settle |
| expo.in-out | `cubic-bezier(0.87, 0, 0.13, 1)` | curtain lifts, slab shrink, word roll |
| power3.out | `cubic-bezier(0.215, 0.61, 0.355, 1)` | word blur, palette tweens, counters |
| ease-in (accelerating) | `cubic-bezier(0.7, 0, 0.84, 0)` | hole expand only: it accelerates away |
| linear | `linear` | scrub mappings (progress -> value); the damping provides the feel |
| spring | WAAPI `linear()` sampled curve, overshoot ~8 % | practice: tactile/playful genres only; one overshoot, never bouncy lists |

Default to expo.out. A page where everything uses `ease` or `ease-in-out` reads as templated.

## Durations

| Event | Duration | Notes |
|---|---|---|
| line blur reveal | 0.5-0.7 s | exit 0.3 s |
| mask rise | 0.8 s | |
| word blur | 0.6 s | |
| card grid stagger | 0.8 s per item | |
| count-up | 0.9 s | |
| hole expand | 0.25-0.5 s | |
| curtain lift | 0.7 s | |
| slab to squircle | 0.55 s | |
| card to full bleed | 0.9 s | 0.25 s observed |
| palette hand-off | 0.6-0.8 s | background-only tweens 0.4 s |
| stepper crossfade | 0.3 s | |
| FLIP expand | 0.7 s | |
| wipe | 0.6 s | |
| nav drop | +0.1 s after the card starts | |
| hover / press | 0.15-0.25 s | practice |
| exit / dismiss | 60-70 % of the enter time | practice |

## Stagger

| Unit | Stagger |
|---|---|
| characters | 20-40 ms (28 ms scramble lock) |
| words | 40 ms |
| lines | 60 ms (mask) to 100-150 ms (blur) |
| cards / items | 100-120 ms |
| chapters of a hero composition (headline, copy, stats, nav) | 0.1-0.4 s offsets, headline first |

Cap the total: stagger x count <= ~1.2 s, otherwise the last item feels late; group instead.

## Scrub vs time-drive

| Quantity | Drive | Why |
|---|---|---|
| camera yaw/pitch/position, object morph amount, tint mix | scrub (progress, damped) | continuous, reversible, tied to reading position |
| rail translate, parallax, scrub video frame, paragraph ink | scrub | same |
| text line/word reveals, card entrances | time (IO 0.5, then play once) | scrubbed text feels laggy and is unreadable mid-way |
| palette hand-off | time, on chapter change | scrubbing colour per pixel looks muddy and flickers on boundaries |
| loader, nav drop, stepper swap, hover, cursor | time | discrete events |
| ambient (drift, shimmer, idle sway) | time loop, paused off-screen | stillness reads cheap; keep amplitude small |

## Scroll source

One shared source: native scroll plus a damped lerp (0.08-0.1 per 60 Hz frame, scaled by dt), never scroll hijacking. Smooth-scroll libraries
(for example Lenis) were seen site-wide; the template's `core/scroll` gives the same glide in ~50 lines without a dependency. Every module takes the
source as an option instead of attaching its own listener. Convert lerp factors to frame-rate independence: `1 - (1 - k) ** (dt * 60)`.

## A page's motion spec (fill this before coding)

| Field | Example |
|---|---|
| entrance | curtain-progress, 1.0 s minimum, wordmark docks to header |
| hero reveal | blur-line headline, word-blur copy at +0.4 s, stats stagger-grid at +0.6 s |
| stage | ONE persistent object, 4 chapters, camera keys at p = 0, .33, .66, 1 |
| palette per chapter | name each (bg, fg, accent); hand-off 0.7 s |
| transitions | curtain overlap between dark and light chapters |
| pointer | ring cursor on fine pointers; object tilt <= 0.3 rad |
| finishing | glass chrome over the stage, 6 % grain, vignette |
| reduced motion | final states, no pin, no cursor, no loop |
