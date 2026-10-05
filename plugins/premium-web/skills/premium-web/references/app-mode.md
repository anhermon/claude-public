# App mode (work tools: dashboards, admin, ops consoles, editors, internal apps)

`tool` is an alias of `app`. Use this when people **operate** the thing (find, compare, trigger, approve, edit, triage),
not when they read it once to be persuaded. Marketing mode is unchanged; do not use app mode for a landing page, and do
not use marketing mode for a screen someone works in. Mixed products: split the deliverable (step 0 `scope:`), one mode each.

**Success = task speed and clarity**, not impression. The old failure: every request was built as hero + scroll sections,
or as the generic mockup (greeting, 4 KPI tiles, chart, 3-row table), and the wow/section rubric fought the work.

## 1. Tasks first (before any layout)

Write **3-5 primary tasks** in NOTES.md (`primary_tasks:` in the step 0 classification), each a verb phrase with an
observable end state: "find the failing run for branch X and open its first error", "approve 6 pending invoices".
Name the user, how often they do it, and the state they start in. No tasks, no design. A task nobody can write down means
the request is READ: go to marketing mode.

Every candidate is judged by **walk-throughs**, not by looking at it. For each primary task fill one block and keep it in
NOTES.md; re-do it after every redesign round.

```
Task:                 <verb phrase>
Start state:          <view, filters, selection, data volume, e.g. 2,400 rows, 3 failing>
Steps / keystrokes:   1. <action> (click | key)   2. ...      -> N steps (clicks + keystrokes counted separately)
Result:               <what is on screen at the end; is it the answer, or one more navigation?>
Time to first meaningful result: <seconds or steps from page load; measured by the Playwright script>
State lost on the way?: <filters, scroll, selection, draft: none | which>
```

Pass lines: the primary task is <= 4 steps from the landing view, the first meaningful result appears with no extra
navigation, no state is lost on back/refresh/tab switch. A task that needs a modal chain, a page reload or re-entering a
filter fails. Compare candidates by these numbers; the walk-through beats the screenshot.

## 2. Structure rules

1. **Persistent shell + navigation** (sidebar or top bar, fixed/sticky) that never scrolls away. The work surface starts in the
   first viewport at 1440x900.
2. **No hero, no scroll-story, no decorative or closing sections.** No "Get started", footer link columns, section eyebrows,
   testimonial or trust strips. Regions of a screen are panes and views, not stacked chapters.
3. **Stated density target** (`density_target` in NOTES.md): rows or items visible at 1440x900 for list/table/log screens,
   chosen from the task. Measured reference: compact rows 32-40 px give 15-20 visible; two-line rows 65-78 px give 8-10
   (GitHub issues 9, Actions 8); wrapped log records 93-110 px gave 8 (Axiom). Say the number and the row height; offer a
   density toggle when both users (scan vs read) exist. Screens with no list declare `data-screen="form|detail|editor"` and
   hold >= 24 data points instead.
4. **Filter, search, sort that work at realistic volume**: build them against >= 500 realistic rows (virtualise or paginate
   honestly), with counts that update, filter chips you can remove, and "no results" that offers the way back.
5. **Selection and bulk actions** wherever a task acts on more than one item: checkbox column, shift-range, select-all with
   the true count ("all 2,400 match"), an action bar that appears in place.
6. **Deep-linkable view state**: filters, sort, selected item, tab and time range live in the URL; refresh and share restore
   the same view. Back button steps through views, not out of the app.
7. **Keyboard path for the primary task**: focus order, visible focus, `/` or Cmd-K to search, `j/k` or arrows through rows,
   Enter to open, Esc to close, with a shortcut hint in the UI. Count keystrokes in the walk-through.
8. **Designed states**: empty (first-run and filtered-empty differ), loading (skeleton at the final layout size, no spinner
   over blank), error (what failed, retry, what is still valid), **partial failure** (3 of 40 rows failed: the 37 stay
   usable and the 3 say why). Mark them `data-state="empty|loading|error|partial"` (or `aria-busy`, `[data-skeleton]`)
   with real message text so the gate can see them; >= 3 of 4 are required, all four for the primary screen.
9. **Accessible**: visible focus ring >= 3:1, text contrast >= 4.5:1 (state colours too, check dark and light),
   targets >= 24 px, named controls, no state by colour alone, `prefers-reduced-motion` honoured (no animation is
   needed for any task).
10. **Responsive**: Playwright at 1440 and at 390 (or 768); no horizontal page scroll (tables scroll inside their pane),
    primary task still completable at the narrow width.

## 3. Signature clarity (replaces the wow)

App mode has **no wow moment**, no `data-wow`, no hero numeral, no full-bleed scale change. In their place: **one
distinctive, truthful way of making the product's own data legible**, a choice a competitor's screen for the same data
would not make. Examples: every item placed on one field (all 300 releases on one time x service plane, hover = detail);
a timeline that doubles as the filter (drag a range, the table below narrows); a run drawn as spans with the failing one
already expanded; rows that are their own sparkline; a diff that is the navigation.

Acceptance (all three, in NOTES.md):
- **Truth**: every mark is a real record (id, state, duration), counts reconcile with the list, no decoration.
- **Walk-through win**: it shortens at least one primary task against the plain table baseline (steps, time-to-first-result),
  with the two numbers written next to each other.
- **Not borrowed**: write the one sentence "this screen shows ___ as ___, which a ___ would show as a table"; if the
  second half is just "a table", the signature does not exist yet.

**Genre escape is layout and data representation**, not ornament. Avoid by default: stat-card hero over a table, 4 equal KPI
tiles, a chart card per metric, a welcome greeting, "insights" paragraphs. Prefer: one pattern repeated many times with the
exception coloured (90 bars per row), the filter built into the visualisation, master-detail where the detail is the real
record, the primary number inside the context that explains it.

## 4. Carry-overs from marketing mode

- Type: one family for UI plus one mono for data, from `type-systems.md` (banned faces stay banned). UI text **12-14 px**,
  never below 12, line-height 1.3-1.5. Headings are small: a view title at 16-20 px; no 28-34 px "Welcome back".
- Tabular numerals (`font-variant-numeric: tabular-nums`) on every column of numbers; **mono for identifiers**
  (ids, hashes, paths, branch names, durations in logs); right-align numbers.
- No uppercase micro-label overload: sentence-case column headers and field labels; caps only for a handful of true
  abbreviations (`caps_micro_labels` gate stays hard).
- Palette restraint and saturation as in `styles.md`/`saturation.py` (unchanged): neutral surfaces, hairline borders,
  **0-3 chromatic hues, spent on state and selection**, no gradient fills, no pastel pills, no card shadows. Dark and light.
- Material: real content, real ids and timestamps (`"2min ago"`, `#339365`, pod names), never lorem or round numbers.

## 5. Gates (all three, in order)

1. **Works**: Playwright at 1440 and 390 (or 768), zero console errors and failed requests, and a script per primary task that
   performs the walk-through and **records the step count and time-to-first-result**; the counts must match NOTES.md.
   Screenshot at both widths; open them and look (an app that renders but whose filter does nothing is a fail).
2. **Not templaty**: `tells.js` app profile (`MODE=app`, `EVAL=scripts/tells.js`). Hard fails kept: `equal_card_grids`,
   `caps_micro_labels`, `palette`, `material`. Added hard fails: `density`, `interactive_affordance`, `state_coverage`,
   `page_shaped_mismatch`. Dropped as hard (measured, not gating): `type_scale`, `wow_visible`, `scale_change`, `panel_run`.
   `scripts/saturation.py` unchanged.
3. **Critic**: `critic.py --mode app` against `rubric-app.md` (task clarity, hierarchy, density, states, interaction,
   distinctiveness incl. signature clarity), per screen and per flow. Pass (mirrors the marketing section verdict): task clarity >= 4, distinctiveness >= 4, no axis below 3, at most two 3s.

Measured reference numbers for what good looks like: `app-exemplars.md`. Anchors: `gallery/README.md`.

## 6. Do not game a marketing gate

**DO NOT add marketing sections to satisfy a gate, and do not wrap things in `data-wow`.** No hero band to pass a scale
gate, no closing CTA, no decorative full-bleed figure, no extra section to vary rhythm, no oversized numeral. If a gate
seems to demand any of that, **stop and report the gate as mismatched** (name the gate, the measured value, and why the
honest app cannot pass it) so the gate is fixed; do not bend the product to the gate. `page_shaped_mismatch` firing means
the structure is page-shaped: rebuild as shell + work surface (or re-classify as READ if nobody operates it), never
paper over it. Marketing-mode thresholds are not loosened by any of this.
