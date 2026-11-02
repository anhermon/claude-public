# Figures that teach a claim

All values are authored starting points (no measured corpus for this asset type); the template numbers live in `svgfig.mjs` `K`.

## Contents
- The claim test
- Anatomy of a good figure
- Annotated diagrams
- Data figures
- Process drawings
- Fakes to avoid
- Config reference

## The claim test

Write: "This figure shows that ___." If the blank is "our platform" or "how it works", the figure is decoration; replace it with a
specific claim ("every request is checked before it reaches the model"). Then: can a stranger state the claim after 3 seconds?
If the answer needs the caption, the figure is wrong, not the caption.

## Anatomy of a good figure

1. **One path of attention.** Left to right or top to bottom; the accent colour marks the one thing the claim is about.
2. **Direct labels.** Names on or next to the marks; legends only when 5+ series force them.
3. **Callouts say the insight**, not the name ("the only place a request can be rejected"), at most 2-3 per figure.
4. **Real content.** Real stage names, real numbers, a source line; illustrative data is labelled as illustrative inside the figure.
5. **Quiet frame.** No drop shadows, no gradients on marks, no icons-in-circles; 1.5 px strokes, 10 px radius, one type size pair (14/12).
6. **Space.** Gaps between boxes at least 40 px so edge labels fit; 16 px padding to the viewBox edge.

## Annotated diagrams

`kind: diagram`: boxes with `x, y, w, h`, `label` (string or lines) and optional `sub`; `accent: true` on one box. Edges
connect ids: left-to-right edges leave the right side and elbow at the midpoint, others run top-to-bottom. Callouts attach to a node
from `top` or `bottom` with a leader line. Coordinates are explicit on purpose: you choose the reading order and the white space;
auto-layout produces tidy but meaningless graphs. Box width must fit its text (the selftest checks it with `getBBox`).

## Data figures

`kind: bars`: horizontal bars, zero baseline (never truncated), value written at the bar end, one `highlight` for the point of the
figure, `source` line under it. Rules: sort by value or by a natural order (stage order), never alphabetically by accident;
label units once (`unit`); if values differ by 50x the small ones become slivers, which is the honest picture, so say so in the
callout instead of breaking the axis. Lines or scatter: draw with the same conventions, or use a charting library when interaction is needed.

## Process drawings

Steps as numbered boxes in one row (max 5 on desktop; stack to a column on a 390 px viewBox via a second config, not by shrinking).
Pair each step with the artefact it produces (a file name, a status, a number). The draw-on order is the reading order.

## Fakes to avoid

- Invented metrics, logos or customer names in a figure. Use real data or label "illustrative".
- Box-and-arrow with generic labels ("Service A", "Process", "Data") that prove nothing.
- Icon-in-circle rows as "features" when a diagram of the actual mechanism is possible.
- A figure that is wider than the viewport on mobile: give mobile its own config and viewBox.

## Config reference

Common: `id` (unique per page, used for classes and aria ids), `kind`, `width`, `title` (accessible name), `desc` (what a sighted viewer
learns), `trigger` (`load` or `inview`). Diagram: `height`, `nodes`, `edges`, `callouts`. Bars: `values[{label,value,highlight}]`, `unit`, `source`
(height is computed). Colours: override CSS variables `--fig-ink`, `--fig-line`, `--fig-accent`, `--fig-bg`, `--fig-font` on the svg or a parent.
