# Reduced motion and performance rules

Contents: reduced-motion contract, performance rules, measured results of the template, failure modes.

## Reduced motion (`prefers-reduced-motion: reduce`)

| Feature | Reduced behaviour |
|---|---|
| text reveals | final state at once: no blur, no transform, no stagger; content never starts hidden |
| count-up, scramble, typewriter | the final text, no timer, no rAF loop |
| loader | none: no overlay, no scroll lock, `onReveal` fires immediately |
| card-to-fullbleed | already full bleed |
| pinned stage | not pinned (`height: auto`, `position: static`), first chapter palette, all steps visible stacked, rail becomes a native horizontally scrollable strip |
| curtain overlap | plain stacked sections, no sticky, no scale |
| cursor, grain animation, parallax, ambient loops | off (static grain is fine) |
| scrubbed video / sequence | one poster frame |
| WebGL | static poster or a single rendered frame (see `premium-web-webgl`) |

Keep opacity-only crossfades (<= 0.2 s) where meaning needs a transition. Test with the emulated media feature, not by reading code. Provide
`options.reduced` (used by the template tests) so the path is testable without OS settings.

## Performance rules

- Animate `transform`, `opacity`, `filter` and `clip-path` only; never `top/left/width/height/margin`. `will-change` only during the animation, cleared after.
- Blur is expensive: <= 60 simultaneously blurred units, <= 14 px, remove the filter after completion (the template clears inline styles at the end so the final state equals the natural CSS: no reflow, no leftover compositing layers).
- One rAF loop per concern that SLEEPS when settled (`loop()` returns false); no always-on loops except a visible canvas.
- Triggers via IntersectionObserver, not scroll listeners; scroll listeners are passive and only write a target value; the rAF loop does the work.
- Read layout once, write once: split text measures all words in one pass; resize handling is debounced (120 ms) and re-splits only when width changed.
- `backdrop-filter` cost scales with area: cap glass surfaces to chrome-sized elements (nav island, cards), not full-screen sections; at most 3 on screen.
- Grain: a static tiled layer (<= 220 px tile). Never animate a full-screen SVG filter.
- Pause everything off-screen and when the tab is hidden; handle `visibilitychange`.
- Fonts: wait for `document.fonts.ready` before measuring splits, or lines break differently after the swap.
- Budget: 60 fps at 390x844 under 4x CPU throttle; judge p50 and p99 frame time, not averages.

## Measured here (template selftest, headless system Chrome)

| Check | Result |
|---|---|
| 390x844, 4x CPU throttle, 3 s scroll sweep over the whole demo (pinned stage + curtain + reveals) | p50 16.7 ms, p99 16.8 ms, 180 frames |
| reduced-motion run | no hidden state, no animations, no loader, stage unpinned, no cursor |
| no console errors on desktop, reduced and mobile runs | pass |

Caveat: a headless software compositor flatters `backdrop-filter` and blur costs; confirm on a real mid-range phone before claiming 60 fps.

## Failure modes seen while building

- `textContent`-based splitting silently drops `<br>`, merging a two-line headline into one run (fixed in the template: `<br>` is a forced line break).
- Glass cards tinted white vanish on a light chapter; tint from the foreground token.
- Nav links hard-coded light become unreadable when a chapter turns light; give the nav island its own dark tint or follow the chapter palette.
- A video scrub that never seeks is almost always a server without HTTP Range support (see `premium-web-imagery`).
- Entrance and hero reveal both triggered on load make the headline play behind the curtain; use `data-motion-when="entrance"` so it waits for the reveal callback.
