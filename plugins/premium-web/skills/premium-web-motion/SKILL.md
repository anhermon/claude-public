---
name: premium-web-motion
description: >
  Choreography for premium web pages, measured from 16 public cinematic reference sites: the entrance chapter (curtain, hole-expand,
  slab-to-node preloaders), headline reveals (blur-line, mask-line rise, word blur, scramble, count-up, typewriter), ONE pinned
  stage driven by a scroll timeline, chapter colour hand-offs, curtain-overlap and card-to-fullbleed transitions, pinned rails and
  steppers, glass chrome, ring cursor and grain, with timing/easing/stagger tables, reduced-motion rules and performance rules.
  Use for "add scroll animation", "make it feel cinematic / less static", "page transitions", "text reveal", "preloader", "sticky
  scroll sections", "parallax", "motion spec", "scroll-driven stage", "why does my page feel flat".
  Do NOT use for 3D or shader scenes (premium-web-webgl), animated SVG, stroke draw-on or path morphing (premium-web-svg),
  generated video or scroll-scrubbed media encoding (premium-web-imagery), page strategy and layout (premium-web), or
  characters and mascots (animated-objects).
metadata:
  version: "0.1.0"
---

# Motion grammar

Models write layout, not choreography. This skill supplies the grammar: a designed entrance, reveals that resolve out of blur,
one persistent stage driven by scroll, palette hand-offs per chapter, finishing. Every number is measured from public reference sites
(2026-11, +-0.3 s) and lives in `references/`; `template/` is working, config-driven vanilla JS with no dependency and no CDN.

## Decision table

| Need | Use | Drive |
|---|---|---|
| Chapter 0 | `loader/curtain-progress` (default), `hole-expand`, `slab-to-node` | time |
| Hero headline | `blur-line` (default), `mask-line` for caps/editorial | time, once |
| Paragraph, stats, grids, labels | `word-blur`, `count-up`, `stagger-grid`, `scramble` or `typewriter` (one signature each) | time (IO 0.5) |
| The persistent object / camera / morph | `pinStage` progress (`--stage-p`) | SCROLL (damped 0.08-0.1) |
| Palette per chapter | `pinStage` chapters, hand-off 0.7 s | time on chapter change |
| Dark-to-light seams | `curtain-overlap` | scroll, damped |
| Pinned horizontal travel, step swaps | `pinStage` `rail` / `steps` | scroll / CSS 0.3 s |
| Chrome | `.glass`, `.nav-island`, `.finish` (grain + vignette), `cursor` | static / pointer |

## Workflow

1. **Write the motion spec** before code (`references/timing-and-scrub.md`, last section): entrance, hero reveal, the ONE stage and its
   3-5 chapters, palette per chapter, transitions, pointer, finishing, reduced-motion plan. No spec, no motion.
2. **Copy `template/`** (`src/`, `motion.css`, `motion.config.js`) into the project; delete unused modules. Open `index.html` over HTTP first.
3. **Edit `motion.config.js`** (loader, chapters, trigger) and mark up with `data-motion`, `data-stage`, `data-curtain`, `data-fullbleed`
   (`references/template-guide.md`). Defaults already carry the measured numbers; change one at a time with a reason.
4. **Bind the hero object** to `--stage-p` / `--stage-chapter` (CSS) or `pinStage` `progress` (canvas); 3D and shaders: `premium-web-webgl`.
5. **Finish**: glass only over something real, grain 6 % on dark, vignette; one accent.
6. **Reduced motion and perf** (`references/reduced-motion-and-performance.md`): final states, no pin, no cursor; transform/opacity/filter only.
7. **Verify** (below) and fix what the frames show.

## Verification loop (mandatory)

- `PLAYWRIGHT_NODE=<dir containing node_modules/playwright> node template/selftest.mjs` runs the demo in system Chrome: three entrances,
  chapters and palette hand-off, stepper, rail, curtain, reduced-motion run, 390x844 at 4x CPU throttle (p50/p99 frame times). Frames land in `.selftest/`.
- On the real page, capture MID-animation frames (t = 0.2, 0.5, 1.0 s after trigger; stage at p = 0.1, 0.45, 0.9) and a real 390 px viewport with
  `?reduced=1`. LOOK at them: line breaks intact, no layout shift when a reveal ends, hand-off colours readable, glass legible on every chapter, no horizontal scroll.
- A page that passes timings but has one effect everywhere, or reveals on every paragraph, is still flat: choose where motion happens.

## Rules

- Never `ease`/`ease-in-out` by default: expo.out for entrances, expo.in-out for lifts; scrub mappings linear with damping.
- Scrub continuous state; time-drive discrete events. Never scrub text reveals except a paragraph ink fill.
- At most one signature text effect (scramble or typewriter) per page; reveals only on what carries meaning.
- Reserve space (no reflow), keep `<br>` and `aria-label`, wait for fonts before splitting.
- Provenance: a parameter without a source line is a practice default and is marked so. No project names, no CDN, no bundled media or fonts.
- Code files <= 800 lines; named constants (module `DEFAULTS` hold them).

## Pointers

| Need | Read |
|---|---|
| The measured grammar, all rows with numbers and modules | `references/grammar.md` |
| Easing, duration, stagger tables; scrub vs time-drive; motion spec form | `references/timing-and-scrub.md` |
| Reduced-motion contract, performance rules, measured results, failure modes | `references/reduced-motion-and-performance.md` |
| Template layout, markup contract, verified/untested status, extending | `references/template-guide.md` |
| 3D/shader hero, point morph, stage rig | `premium-web-webgl` |
| Scrub video / image sequences | `premium-web-imagery` |
