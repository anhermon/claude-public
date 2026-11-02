---
name: premium-web-svg
description: >
  Code-drawn SVG for premium web pages: figures that teach a claim (annotated diagrams, data figures with real labels, process
  drawings), animated SVG (stroke-dash draw-on, path morphing, masks, filters such as turbulence, displacement and gooey; SMIL vs CSS
  vs JS), icon systems, generative patterns, accessibility and optimisation, with a config-driven diagram generator. Use for
  "draw a diagram", "architecture figure", "animated SVG", "draw-on line", "icon set", "chart without a library", "morph this
  shape", "SVG filter", "replace the stock illustration", "the page has icon cards and blobs".
  Do NOT use for 3D or shader scenes (premium-web-webgl), generated photos, illustrations or video (premium-web-imagery), DOM
  scroll choreography or text reveals (premium-web-motion), interactive dashboards with many series (use a charting library), or
  characters and mascots (animated-objects).
metadata:
  version: "0.1.0"
---

# SVG: figures that carry a claim

Without real imagery, models fall back to icon cards, blobs and gradients. A figure drawn in code can be the page's subject or the
proof under a claim, stays sharp at any size, weighs a few KB and can be animated and read by assistive tech. Starting values here
are AUTHORED from sound practice (no measured corpus exists for this asset type); each table says so. `template/` is working code.

## Decision table

| Need | Use | Where |
|---|---|---|
| A process, architecture or flow that backs a claim | `kind: diagram` (nodes, edges, callouts) | `template/svgfig.mjs` |
| A comparison of a few numbers | `kind: bars` (zero baseline, direct labels, one highlight) | `template/svgfig.mjs` |
| Many series, interaction, zoom | a charting library; not this skill | none |
| Icons next to text or in buttons | sprite of `currentColor` symbols | `template/sprite.mjs` |
| A texture, wobble, liquid or grain on flat vector | SVG filter, static first | `template/filters.html`, `references/filters-and-patterns.md` |
| One shape becoming another | path morph (equal command structure) | `references/animated-svg.md` (snippet, not run) |
| A photo-like or painterly picture | stop: `premium-web-imagery` | none |
| A moving 3D or shader subject | stop: `premium-web-webgl` | none |

## Workflow

1. **Claim first.** Write the sentence the figure proves, then what the viewer must see in 3 seconds. No claim, no figure (`references/figures-that-teach.md`).
2. **Truth inventory.** Labels, numbers and sources must be real or marked illustrative in the figure itself.
3. **Config.** Copy `template/`, edit a config (`diagram.config.json` or `bars.config.json`): coordinates, labels, one accent, `title`, `desc`.
4. **Generate:** `node svgfig.mjs diagram.config.json > figure.svg`; inline it in the page (inline gives CSS tokens, fonts and play-on-view); add `figure.js`.
5. **Animate with intent:** draw-on in reading order, one accent, final state is the designed state (`references/animated-svg.md`).
6. **Accessibility and weight** before judging (`references/icons-and-accessibility.md`).
7. **Verify** (below).

## Verification loop

```
cd template && PLAYWRIGHT_NODE=<dir containing node_modules/playwright> node selftest.mjs
```
Checks: XML-valid, size under 12 KB, `role="img"` with title and desc wired by `aria-labelledby`, labels fit their boxes, edge
labels clear of nodes, hidden before view, mid-flight draw-on, final state, reduced-motion and no-JS show the final state at once,
sprite icons inherit colour, filters demo has no errors. Frames land in `.selftest/`: LOOK at the mid and final frames and the
filters page; a passing script does not prove the figure reads.

## Hard rules

- Text stays real `<text>` (selectable, translatable), at least 12 px at the size shown; never outline text.
- Final state is the designed state; the hidden state exists only while the figure is pending in the page (visible with JS off, in print, with reduced motion).
- Animate `stroke-dashoffset`, `transform`, `opacity` only; filters animate at their own risk (repaint).
- One accent colour per figure; colours from CSS custom properties so dark mode and theming work.
- Bars start at zero; direct labels, no legend when there are fewer than 5 series; no 3D, no gradients on data marks.
- Every figure has an accessible name and description; icons beside text are `aria-hidden`.

## What is verified

Verified headlessly (frames looked at): diagram and bars generation, draw-on and fade timing, in-view trigger, reduced motion,
no JS, standalone-file autoplay, sprite icons, gooey, displacement and grain filters (static). NOT verified: path morphing, SMIL,
masks, generative patterns (snippets only), screen-reader output, Safari and Firefox rendering of filters, `svgo` output.

## Pointers

- `references/figures-that-teach.md`: claim, anatomy, diagrams, data figures, process drawings, fakes to avoid.
- `references/animated-svg.md`: draw-on, morph, masks, SMIL vs CSS vs JS, triggers, reduced motion, performance.
- `references/filters-and-patterns.md`: turbulence, displacement, gooey, grain, generative patterns, costs.
- `references/icons-and-accessibility.md`: icon system, favicon, accessibility checklist, optimisation.
- Companions: `premium-web-motion` (scroll-driven timelines can set `--p` on an SVG), `premium-web-imagery` (raster fallback), `premium-web-webgl`.
