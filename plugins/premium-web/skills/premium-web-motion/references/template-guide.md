# Template guide: modules, wiring, verification status

Contents: layout, markup contract, config, module status, extending, copying into a project.

`template/` is vanilla ES modules, no build step, no CDN, no dependency (about 1.3 k lines in 25 small files). Serve over HTTP (`python3 -m http.server`), open `index.html`.

## Layout

| Path | Role |
|---|---|
| `motion.config.js` | the file you edit: loader type, trigger, per-effect overrides, stage chapters (palette per chapter), curtain/fullbleed/cursor switches |
| `motion.css` | tokens (durations, easings, blur, glass, grain) + `.glass`, `.nav-island`, `.finish` (grain + vignette), `[data-step]`, split classes |
| `src/motion.js` | `startMotion(config)`: scans `data-*` markup and starts everything |
| `src/core/` | `easing` (tokens, tween, reduced-motion), `scroll` (damped lerp source), `split` (accessible line/word/char split), `reveal` (shared WAAPI runner) |
| `src/text/` | blur-line-reveal, mask-line-rise, word-blur-reveal, stagger-grid, count-up-blur, scramble-resolve, typewriter |
| `src/loader/` | curtain-progress, hole-expand, slab-to-node |
| `src/transition/curtain-overlap.js`, `src/util/helpers.js` | overlap panels; shared easing, rAF loop, scroll adapter |
| `src/timeline.js`, `src/fullbleed.js`, `src/cursor.js` | pinned stage (chapters, hand-off, rail, stepper), card-to-fullbleed, ring cursor |
| `index.html` | demo page exercising every row of the grammar |
| `selftest.mjs` | headless Playwright check + frames (`PLAYWRIGHT_NODE=<dir with node_modules> node selftest.mjs`) |

## Markup contract

```html
<h1 data-motion="blur-line" data-motion-when="entrance">Headline<br>second line</h1>
<p data-motion="word-blur" data-motion-delay="0.4">Copy</p>
<b data-motion="count-up">1,240</b>
<section data-stage> <div class="pin"> <h2 data-step>One</h2> <h2 data-step>Two</h2> <div data-rail>...</div> </div> </section>
<div data-curtain> <section>..</section> <section>..</section> </div>
<header data-fullbleed>..</header>   <body class="finish">
```

`data-motion-when="entrance"` waits for the loader's reveal; `data-motion-scrub` on `word-blur` scrubs it with scroll; effects accept
`options.reduced` for tests. Every module returns `{destroy()}` and cleans listeners, observers and rAF (verified for the text and loader modules by the original per-module tests).

## Module status (what was verified, and how)

| Module | Status |
|---|---|
| blur-line, mask-line-rise, word-blur (load/view), stagger-grid, count-up, scramble, typewriter | verified: per-module Playwright tests (duration within +-15 %, no hidden state after finish, destroy leaves no observers or rAF, reduced-motion final state, no console errors, 60 fps) re-run and passing; in the demo page I looked at settled frames and a mid-reveal blurred headline (seen behind the slab entrance) |
| curtain-progress, hole-expand, slab-to-node | verified: same per-module tests; frames of all three entrances looked at in the demo page |
| curtain-overlap | verified: 15/15 checks of its test; mid-transition frame looked at (rounded cream panel sliding over the dark one) |
| timeline (pinStage): chapters, palette hand-off, stepper, rail | written for this template; verified by `selftest.mjs`: chapter sequence arrival/method/proof, three distinct stage backgrounds, one step per slice, rail travelled; frames looked at |
| fullbleed | verified by `selftest.mjs` (clip-path cleared after play) and a frame; not timed against 0.9 s |
| cursor | initialised without errors on a desktop run; NOT exercised with real pointer movement: untested |
| word-blur scrub mode (`data-motion-scrub`) | NOT exercised in `selftest.mjs`; the module's own original test covers load and view only: untested |
| FLIP shared-element expand, cloud wipe, word swap | not in the template (grammar rows marked practice) |

## Extending

- New effect on the reveal runner: copy `text/blur-line-reveal.js` (12 lines): supply `DEFAULTS`, `pick`, `hidden`, `keyframes`; register it in `src/motion.js`.
- New chapter: add `{id, bg, fg, accent}` to `stage.chapters`; progress shares split equally unless `at` is set.
- Hero object: drive it from `--stage-p` / `--stage-chapter` (CSS) or `pinStage({onChapter})` and the `progress` getter (canvas). See `premium-web-webgl`.
- Colour in OKLab for long gradients; the sRGB lerp in `timeline` is fine over 0.7 s.

## Copying into a project

Copy `template/src`, `motion.css`, `motion.config.js`; delete the modules you do not use (each is independent; `core/` and `util/` are shared). Replace the demo
palette and wordmark. Fonts are fetched at build time; the template ships none. Constants live at the top of each module with a provenance comment: keep them when tuning.
