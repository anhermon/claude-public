# App exemplars (measured work UIs)

Numbers for **app mode** (`app-mode.md`, `rubric-app.md`): real product screens, not marketing pages (those are in `wow.md`
and `type-systems.md`). Supersedes `tool-ui-exemplars.md` (its four measurements are folded in below).

Method (2026-10-05, one page load each, no crawling, no login): `scripts/chrome-shot.mjs` at 1440x900 and 390x844 (a copy with a
9-15 s settle wait for SPAs) with a throwaway first-viewport probe (visible text nodes, median/max font px, size histogram,
row groups, shell boxes, hue buckets of text/background/border). `measure-site.js` (SUMMARY=1) was the method for the
four folded-in exemplars (E1-E4). "(shot)" = read from the screenshot because the probe could not isolate the object.
Caveats: the probe's row-group finder sometimes latches onto a sidebar list, so row height/visible rows are from the screenshot where
marked; the hue counter misreads `oklch()` colours; live pages change. Copy the structure and scale, not the figures.

## A. GitHub (public, logged-out, github.com/microsoft/vscode), measured 2026-10-05

### A1. Actions: workflow runs list (`/actions`), gallery `approved-app-github-actions-runs.webp`
- Shell (1440): 72 px global header, 48 px repo tab bar, **left nav 320 px** (workflow list, pinned items), content from x=360 to 1416.
- Density (shot): row = title 16/600 + one meta line 12 px, **78 px rows, 7 visible** below a 65 px list header; probe 113 text nodes
  in view, median 12 px, sizes 11/12/14/16/20.
- Per row, left to right: status icon (colour = state), title, `Workflow #run: trigger by actor`, **mono branch chip**, relative time,
  duration with icon, a `...` menu. 3 hues in view (probe buckets orange, green, blue): amber = queued/in progress, green = success.
- Filters: a single filter box on the page plus 5 dropdown filters (Workflow, Event, Status, Branch, Actor) in the list header, with a live count ("2,500+ workflow runs").
- Copy: status icon as the first column; the list header as the filter bar with the count; a mono chip for the one identifier people scan by.
- Avoid / weak: two-line rows spend 78 px per item (fine for 7 rows, a poor fit for 40); timing is text only (see A2).

### A2. Actions: run view (`/actions/runs/<id>`, 6 jobs), gallery `nice-not-wow-app-github-run-view.webp`
- Shell: same 72 + 48 px headers, **288 px job rail** (job name with status icon; "Run details": Usage, Workflow file), title 20 px.
- Summary strip: 4 labelled facts (trigger, Status, Total duration, Artifacts) in one 88 px card; value 14-16/600, label 12 px grey.
- Work surface: the job graph canvas is 1056 x ~470 px but the 6 job cards sit in one 292 px column (**~28% of the canvas width**),
  durations as right-aligned text (`33s`, `13s`, ...); no time axis, so concurrency and the slow job are invisible without reading.
  73 text nodes, median 14 px, max 24 px, 2 hues (green success, blue link).
- Copy: the job rail doubling as navigation, success/failed as the first element in every row, label-over-value summary facts.
- Avoid: a graph with the dimension that matters (time) unplotted. This is the "signature clarity" gap: a timeline of the six jobs,
  each a bar to scale, would show the answer ("Compile 33 s is the critical path") with no reading. It is shown as nice-not-wow.
- Logs ("Sign in to view logs") need login: not measured.

### A3. Issues list (`/issues`), gallery `approved-app-github-issues.webp`
- Shell: 72 px header, **256 px left sidebar** (Issues, Assigned, Created, Mentioned, Recent; Views, Projects, Milestones, Labels), content x=280-1416.
- Density (shot + probe): **65 px two-line rows, 9 visible**; probe 135 text nodes, median 12 px, sizes 11/12/14/16/20/24/32, one
  Mona Sans family + one mono node; 4 hue buckets (green open-state icon, blue links, red/pink labels).
- Controls: an editable search string `is:issue state:open` (typed query, syntax-coloured) above a header with **Open 18,706 / Closed 236,519**
  tabs showing true counts, 6 dropdown filters, sort (Newest), and **a two-state density toggle** (rich rows / compact list). Whether the URL mirrors the
  query was not tested.
- Row: state icon, title 16/600, labels as small coloured chips inline with the title, then `repo#id - author opened 15m ago` at 12 px with the id in the meta; right side: comment count then avatar.
- Copy: typed query + counts + density toggle; labels inline with the title; relative time everywhere.
- Avoid: a bulk-select checkbox is not visible logged-out, so selection could not be judged; pinned cards above the query push the list down 100 px.
- Mobile 390 (shot): sidebar becomes a hamburger, the query bar and counts stay, the two pinned cards stack and push the list ~460 px down so only ~2 rows (3-4 lines each) show in the first screen; filters collapse to 3 + `...`; no horizontal scroll. Reflows, but the narrow first screen is mostly chrome: avoid pinned cards on mobile.

## B. Folded in from the earlier tool-UI set (measured 2026-10-05 with `measure-site.js` SUMMARY=1)

### E1. Linear marketing page, product frame in the hero (https://linear.app)
- 1440: real app (sidebar, issue, activity, properties rail) rendered in the DOM, frame 1320 px = **92% of viewport**, starts at y=527 (41% of the first
  viewport is product UI). h1 Inter Variable 64/510/lh 1.00/-0.022em, h2 48 px; UI text 12-14 px. Probe ratio largest:median 5.3:1. Ground rgb(8,9,10), card fills at 2-5% white,
  hairlines, no shadows; 3 hue buckets (status icons, violet).
- 390: the frame is cropped not reflowed (6 over-wide elements): do not copy. This is a **marketing page showing an app, not the logged-in app** (login-gated, not measured).
- Copy: product UI in its own 13-14 px type with believable records (id, "2min ago", labels).

### E2. Vercel Status (https://www.vercel-status.com), one object per row
- 90-day availability bar per service, 90 bars per row, bars ~34 px tall, 6 rows in view, column 850 px (59% of viewport, shot), Geist 16/500, no h1. Black ground, **one accent hue** for healthy, a dull yellow for the rare
  degraded day; a 56 px solid status banner. Copy: identical objects per row, the exception coloured. A status page, not the Vercel dashboard (login-gated).

### E3. OpenAI Status (https://status.openai.com), dense uptime grid, light mode
- Column 670 px, bar group 634 px (44%), bars 4.8 x 15 px, ~90 per row, 5 rows + incident card in 900 px, 14 list rows, Inter 24/16/12 px (ratio 1.1-2.0:1), 3 hues (teal/amber/red) used only as data, 1 px amber border + pale fill for the incident (no shadow), right-aligned tabular uptime %.

### E4. Axiom Playground stream view (https://play.axiom.co/axiom-play-qf1k/stream/otel-demo-traces, welcome modal dismissed)
- Table = 100% of viewport width/height under a 38 px header; **295 text nodes** in view; rows 93-110 px (wrapped records), ~8 visible; 40 px filter bar. Inter 13-15 chrome, **Berkeley Mono 12** for data, ratio 1.25:1, bg rgb(17,17,17),
  hairlines rgba(255,255,255,.07), 1 hue (teal "Live"). Copy: fixed timestamp column, key bold / value regular, mono only for data. A density reference, not a signature.

## C. Grafana (public play instance), shell only
`play.grafana.org` loaded its shell (a dashboard URL returned "Dashboard not found", so no panels were measured; a second dashboard URL hung the capture, as in earlier runs):
**320 px collapsible left nav** (items 32 px tall, 14 px Inter, grouped sections with chevrons), **48 px top bar** (breadcrumb left; search with a `cmd+k` hint, "+" and Sign in right), dark ground, one blue primary button, 1 hue.
No dashboard density, panel or time-range numbers recorded; do not cite them.

## What good looks like (targets at 1440x900, from A1-A3 and E1-E4)

| Measure | Measured range | Generic stand-in (rejected, `gallery/reject-tool-generic-*`) |
|---|---|---|
| Visible items, rich two-line rows | 7-9 at 65-78 px (GitHub) | 3 rows |
| Visible items, wrapped log records | ~8 at 93-110 px (Axiom); 295 text nodes | 35 text nodes, 4 KPI tiles |
| Visible items, uniform cells | 5-6 rows x 90 cells (Vercel, OpenAI) | 4 equal tiles |
| Shell | 48-72 px top bar + 256-320 px left nav, fixed | sidebar + greeting header |
| UI text | 12-14 px, titles 16/600, no size above 20-24 in the work area | 28-34 px greeting, 28 px KPI numbers |
| Scale contrast | not needed; hierarchy by weight, position, state colour | oversized KPI numerals |
| Chromatic hues | 1-4, all state/label | 4+ plus gradients, pastel pills |
| Surfaces | one ground, 1 px hairlines, no card shadows | white cards, 16 px radius, shadows |
| Controls | typed query + true counts + 5-6 filters + density toggle (GitHub issues) | one dropdown |
| Identifiers | mono chips (branch, id, hash) | proportional text |

Rules that follow: (1) the list/log/graph IS the first viewport; (2) one row pattern repeated, the exception coloured; (3) true counts beside every filter;
(4) put the dimension that matters on an axis (A2 shows the cost of not doing it); (5) 390 must reflow, not crop.

## Not measured (and why)
- **Sentry** (demo.sentry.io): redirected to a sign-in page on 2026-10-05; no product UI reachable. (The earlier attempt hung on a splash.)
- **Honeycomb** (play.honeycomb.io): opens on a 4-card "Welcome" modal over the query view; behind it a heatmap + results pane (Roboto 14 px, ~1,100 px chart) is visible, but dismissing the modal needs interaction beyond this script; **no numbers recorded**.
- **Linear app, Vercel dashboard, Retool, Datadog**: behind login (or no public demo reachable); only the marketing/status counterparts above were measured and are labelled as such.
- Radar (Cloudflare 403), Plausible demo (rendered unstyled), HyperDX (connection modal): unchanged from the earlier attempt.
