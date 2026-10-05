# Tool-UI exemplars (application UIs, not marketing sites)

Separate from the marketing exemplars in `wow.md` and `type-systems.md`: those measure landing pages. This file measures
**product UIs** (dashboards, tables, run/log/status views), because a tool UI needs different numbers (the data object
is the hero; display type is small by design). For the procedure and acceptance test see the "Tool mode" section of
`wow.md` (maintained there, not here).

Method: skill's own `scripts/measure-site.js` (SUMMARY=1) at 1440x900 through a copy of `chrome-shot.mjs` with a longer
settle wait (SPAs need 3-10 s), plus a throwaway viewport probe (text nodes, rows, largest font, data-object area, hue
buckets). Measured 2026-10-05, one page load each, no crawling. Numbers below are real output; "(screenshot)" marks
values read from the captured image because the DOM probe could not isolate the object.
Caveats: the probe's hue counter misreads `oklch()` colours (Axiom, Vercel), so hue counts there come from the screenshot.
Live pages change (status colours, log rows); the structure and scale are what to copy, not the exact figures.

## Exemplars

### 1. Linear - product frame inside the hero (https://linear.app), measured 2026-10-05
- Hero data object: the real app (sidebar, issue "Faster app launch", activity feed, properties rail) rendered live in the DOM.
- 1440: frame 1320 px wide = **92% of viewport**, starts at y=527, so **41% of the first viewport** already shows product UI, 720 px tall.
- Type: h1 Inter Variable 64 px / 510 / lh 1.00 / -0.022em; h2 48 px; body 14 px / 400. Probe: largest 64 px vs median 12 px in
  view = **5.3:1**; inside the frame the UI text is 12-14 px (the app speaks small, the headline speaks big).
- Colour: bg rgb(8,9,10), card fills at 2-5% white; 3 chromatic hue buckets in view per the probe (yellow status icon, blue-grey, violet); everything else neutral. Sidebar, rows and borders are hairlines, no shadows.
- 390: h1 38 px / lh 1.10, section heights 575-581 px, but the probe reports 6 over-wide elements (the product frame is wider than
  the phone viewport), so the frame is cropped, not reflowed: do not copy that at 390 (see `tells.js` horizontal scroll).
- Steal: show the real product at >= 90% width straight under the headline, in its own UI type (13-14 px), with real
  copy and a believable record (issue id, "2min ago", labels). Scale contrast comes from headline-vs-UI, not from big widgets.

### 2. Vercel Status - one object per row (https://www.vercel-status.com), measured 2026-10-05
- Hero data object: the 90-day availability bar, one per service (AI Gateway, API, Build & Deploy, CI/CD, CDN, ...).
- 1440: content column 850 px (59% of viewport, screenshot), bars ~34 px tall, 90 bars per row, 6 rows in the first viewport,
  with "90 days ago" / "Today" as the only axis labels. Geist 16 px / 500 for service names; no h1 at all (probe: h1 null).
- Colour: black bg (oklch(0 0 0)), **one** accent hue (blue) for every healthy bar, a dull olive-yellow for the rare
  degraded day, white text. Overall banner "All Systems Operational" is a full-width solid blue bar, 56 px tall.
- 390: probe returned the same structure (no horizontal overflow reported).
- Steal: when the data is a time series, make every row the same object and let the single exception colour carry the information.
  A solid status banner plus a lot of identical cells reads designed because nothing else competes.

### 3. OpenAI Status - dense light-mode uptime grid (https://status.openai.com), measured 2026-10-05
- Hero data object: per-product uptime bars (APIs, ChatGPT, Codex, FedRAMP, Ads) under a tinted incident card.
- 1440: column 670 px wide (centered), bar group 634 px = **44% of viewport** (probe), each bar 4.8 x 15 px, ~90 bars/row,
  5 rows plus an incident card in the first 900 px; 14 list-row elements in view; probe leaf-element count for bars is 2,184
  (includes sub-elements, not a bar count). Inter 24 px h1-style title / 16 px h2 / 12-14 px body: ratio **1.1-2.0:1**.
- Colour: white bg, ink rgb(41,41,47), 3 chromatic hues (teal ok, amber degraded, red outage) plus a pale-yellow incident tint.
  Colour is used only as data.
- 390: probe ran (inter 24/16/12 px); no horizontal overflow reported.
- Steal: tiny uniform cells make an at-a-glance pattern (outages cluster), the incident card uses a 1 px amber border plus a
  pale fill instead of a shadowed alert box, uptime % is right-aligned tabular text.

### 4. Axiom Playground - Stream view (https://play.axiom.co/axiom-play-qf1k/stream/otel-demo-traces), measured 2026-10-05
- Hero data object: a live log table of real OpenTelemetry events (`_time` | raw record).
- 1440 (after dismissing the welcome modal): table = **100% of viewport width and height** under a 38 px header; **295 text
  nodes** in view (a marketing hero has 15-40); rows are 93-110 px tall (long wrapped records), ~8 records visible; filter bar 40 px.
- Type: Inter 13-15 px for chrome, **Berkeley Mono** 12 px for data (probe: largest 15 px vs median 12 px, ratio 1.25:1). No
  heading hierarchy; the data is the type.
- Colour: bg rgb(17,17,17), borders rgba(255,255,255,0.07), text near-white and grey; keys bold, values regular; **1 chromatic hue**
  (teal for "Live"/"New"). Saturation is spent on state only.
- Steal: density with structure. Hairline row dividers, a fixed-width timestamp column, key bold / value regular inside the
  record, mono only for data. It is a plain table, so it is a **density** reference, not a wow reference; pair it with 1-3 for scale.
- Note: the Playground opens with an Introduction modal and a "Command Menu" toast; the page was measured with the modal
  dismissed (the first probe with the modal up read 7 rows and max font 28 px, which is the modal, not the product).

## What these share (the numbers a tool UI should hit)

Distilled from the four above plus the generic stand-ins in `gallery/` (verdicts in `gallery/README.md`). These are targets for
tool/dashboard/app pages only; do not apply them to marketing pages (those are in `wow.md` / `type-systems.md`).

| Measure at 1440x900 | Exemplars (measured) | Generic stand-in (rejected) |
|---|---|---|
| Hero data object width | 44-100% of viewport (Linear 92, Vercel 59, OpenAI 44, Axiom 100) | table 50% wide, 8% of area |
| Data object visible in first viewport | 41-100% (Linear 41%, below a 64 px headline) | 8% of viewport area |
| Text nodes in first viewport | 29-295 (Linear 63, Vercel 29, OpenAI 35, Axiom 295) | 35 across 4 KPI cards (12k, 98%, ...) |
| UI body / data type | 12-14 px, data in mono where it is data | 14 px, all one weight |
| Display type | none (status pages, Axiom) or 64 px headline over a 14 px product (Linear): never mid-size 28-34 px "Welcome back" | 28-34 px greeting + 28 px KPI numbers |
| Chromatic hues | 1-3, used only for state (ok / warn / fail / status) | 4+ plus gradient fills and pastel pills |
| Surfaces | 1 bg, hairline borders (5-7% white, 1 px grey), no card shadows | white cards, 16 px radius, drop shadows |
| Repetition | the same cell or row repeated 90x per row, 5-6 rows | 3 table rows, 4 equal KPI tiles |
| Content | real record ids, timestamps, units, long wrapped values | "Welcome back, Alex", +12%, "performing well" |

Rules of thumb that follow:
1. The product's own data object is the hero and is >= 40% of the first viewport (width >= 44% at 1440, ideally >= 90% for a
   frame or table). If you can swap your hero for the stand-in's 4 KPI tiles and nothing changes, it fails.
2. One pattern repeated many times (bar cells, rows) beats many different widgets. Variation is the data's, not the layout's.
3. Chrome is quiet: type 12-14 px, hairlines, 0-1 accent hues. Scale contrast lives between the data object and its labels.
4. Real, specific, slightly ugly data (ids, k8s pod names, "Ongoing for 4 hours") is what separates these from AI mockups;
   greetings, round percentages and "insights" paragraphs are the tell.
5. Check at 390 as well: Linear's wide frame cropped, the status pages reflowed. A tool UI that overflows at 390 fails `tells.js`.

## Not measured (and why)
- demo.sentry.io: stuck on the "Loading a ... ton of JavaScript" splash in headless Chrome, no UI to measure.
- radar.cloudflare.com: 403 Cloudflare challenge.
- play.grafana.org: loaded the shell (sidebar, 48 px top bar, 320 px nav) but the content area stayed empty and the capture
  script hung on repeated runs; no dashboard numbers recorded.
- plausible.io/plausible.io (public demo): rendered unstyled (no JS/CSS) in headless; skipped.
- play.hyperdx.io: opens on a connection-setup modal; not measured further.
