# App rubric: scoring a work screen and a work flow

`critic.py --mode app` pastes this in verbatim; every line must be checkable from screenshots, the walk-through log in NOTES.md
and the Playwright step counts. Marketing pages use `rubric.md`; do not mix them. Score **each screen** and **each flow**
(one flow per primary task, from `app-mode.md` section 1). Scores 1-5, whole numbers; judge against `app-exemplars.md` and
`gallery/` anchors, not against "looks nice".

**Pass** (screen or flow): task clarity >= 4, distinctiveness >= 4, no axis below 3, at most two axes at 3, no ban hit.
**Fail line** is stated per axis; any single fail line fails the screen.

## Axes

### 1. Task clarity (the primary task: can a new user do it, fast, without being told?)
| Score | Anchor |
|---|---|
| 5 | The answer or the next action is visible on arrival; the task takes <= 3 steps; the walk-through log shows no detour, and you can say what the screen is for in one sentence from the screenshot alone. |
| 4 | <= 4 steps, one place that is slightly slow (a menu hop); result is on screen at the end. |
| 3 | The task is possible but needs a modal chain, a second page or hunting for the control; 5-6 steps. |
| 2 | The reviewer needs the walk-through script to find the control; primary action competes with 3+ equal buttons. |
| 1 | The primary task cannot be completed, or the screen is a page that *describes* the tool. |
**Fail line: <= 2, or the walk-through log is missing, or its step count does not match the Playwright run.**

### 2. Information hierarchy
| 5 | The eye goes (1) the thing to act on, (2) its state, (3) detail, in that order; one dominant region, everything else quieter; state is readable at a glance (position, shape or a single state hue, never colour alone). |
| 4 | Order is right; one secondary element is as loud as the primary. |
| 3 | Everything is readable but equally weighted; the user must read to find the state. |
| 2 | Greeting, banner or decorative chart outranks the work; headings 28 px+ over 12 px data. |
| 1 | No hierarchy: card soup or uniform grid. |
**Fail line: <= 2.**

### 3. Density
| 5 | Meets the stated `density_target` at 1440x900 with room to scan: row height and type chosen for the task (compact 32-40 px rows or rich two-line 64-78 px), tabular numerals, aligned columns, 12-14 px legible text, a density toggle if two reading modes exist. |
| 4 | Meets the target; one column or region wastes space. |
| 3 | Within 25% under the target, or dense but cramped (touch/click targets < 24 px, 11 px text). |
| 2 | Under half the target, big paddings, KPI tiles or cards doing the job of rows. |
| 1 | A hero-and-scroll page shape; most of the first viewport is not data or controls. |
**Fail line: <= 2, or the measured `density` gate fails.**

### 4. State coverage
| 5 | Empty (first-run vs filtered), loading (skeleton at final size), error (cause + retry + what is still valid) and partial failure are designed and reachable (a way to see them in the demo); copy is specific. Destructive actions confirm or undo. |
| 4 | All four exist; one is generic ("Something went wrong"). |
| 3 | Three of four; loading or empty is bare. |
| 2 | Only the happy path plus a spinner; errors are a toast that disappears. |
| 1 | Happy path only, or a state that shows blank/NaN/undefined. |
**Fail line: <= 2, or `state_coverage` gate fails.**

### 5. Interaction quality
| 5 | Filter/search/sort work at volume (>= 500 rows) and update counts; selection and bulk actions in place; view state in the URL and survives refresh; keyboard path for the primary task with visible focus and a hint; hover/focus/active/disabled distinct; reduced-motion honoured; nothing moves that the task does not need. |
| 4 | One of those is missing (e.g. no bulk action where the tasks need none is fine; no URL state is a miss). |
| 3 | Works with the mouse only, or URL state lost on refresh, or filters reset on navigation. |
| 2 | Controls that look clickable but do nothing, or fake data in controls; focus invisible. |
| 1 | Static mock: nothing responds. |
**Fail line: <= 2, or `interactive_affordance` gate fails, or the Playwright run records a console error.**

### 6. Distinctiveness (incl. signature clarity)
| 5 | One distinctive, truthful way of making this product's own data legible (all items on one field, a timeline that is the filter); every mark is a real record; written sentence "this shows ___ as ___, which a ___ would show as a table" holds; it **shortens a primary task** against the table baseline by recorded numbers; type, palette and chrome are specific to the product; could not be 20 other tools' screens. |
| 4 | A real signature, truthful, with a small walk-through gain; chrome is good but close to a known pattern (Linear/GitHub). |
| 3 | Competent and clean: sidebar + table + detail panel with good type. No signature, or the signature is decoration. This is the "nice" ceiling. |
| 2 | Stat-card hero + chart card + 3-row table; pastel pills; greeting; gradient; "insights". |
| 1 | The generic AI dashboard (see gallery `reject-tool-generic-*`). |
**Fail line: <= 3 for this axis fails the pass (distinctiveness must be >= 4); <= 2 also names the generic tell.**

## Flow scoring (per primary task)
Score task clarity, state coverage and interaction quality **on the flow**: re-run the walk-through in the shots. Add:
- **State never lost**: filters, scroll position, selection and drafts survive open-detail/back, refresh and tab switch (5 = all, 3 = one lost, 1 = routinely).
- **Recovery**: an error mid-flow leaves the user where they were with the work intact (5), or restarts the flow (2).
Flow fail line: any lost state in a flow that edits or filters data, or a flow longer than the walk-through log claims.

## Bans (any hit fails; carried over)
Marketing structure on an app screen (hero, section eyebrows, closing CTA, footer link columns, testimonial strip); `data-wow` or an
oversized decorative numeral added to satisfy a gate; equal-card KPI grid as the page's content; uppercase micro-label overload;
pastel pill soup; gradient fills or drop-shadowed cards; lorem, round or "+12%" placeholder data; a greeting ("Welcome back");
banned type faces; saturation over the `saturation.py` limit.
