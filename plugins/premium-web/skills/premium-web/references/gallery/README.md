# Gallery index

Screenshots used as calibration anchors for the critic and for human review. All 960 px wide webp.
Prefixes: `accept-`/`approved-` = good anchors; `nice-not-wow-` = competent but below the bar; `reject-` = fails.

## Tool-UI anchors (added 2026-10-05; see `../tool-ui-exemplars.md` for the measurements)
| File | Verdict | Source |
|---|---|---|
| approved-tool-linear-hero.webp | approved (scale: real app at 92% width under the headline) | live capture of https://linear.app at 1440, 2026-10-05, single load |
| approved-tool-vercel-status.webp | approved (one repeated object, one accent hue) | live capture of https://www.vercel-status.com at 1440, 2026-10-05 |
| approved-tool-openai-status.webp | approved (dense uptime grid, colour only as data) | live capture of https://status.openai.com at 1440, 2026-10-05 |
| approved-tool-axiom-stream.webp | approved as a density anchor only (plain table, not a wow) | live capture of https://play.axiom.co stream view at 1440, 2026-10-05, welcome modal dismissed (a small "Command Menu" toast remains bottom-left) |
| reject-tool-generic-a.webp | rejected: STAND-IN built by us, not a real product (sidebar + greeting + 4 KPI tiles + chart + 3-row table + insights card) | /tmp scratch HTML written for this index; no brand, illustrates the "generic AI dashboard" the user rejected |
| reject-tool-generic-b.webp | rejected: STAND-IN built by us (dark gradient, glass cards, gradient headline, KPI cards) | same as above |

The approved captures are third-party product pages shown only as small reference screenshots for calibration; they are not
for reuse in generated pages. The two generic ones are our own invented mockups, not screenshots of anything real.

## Marketing-site anchors (pre-existing)
accept-anhermon-v4-*, approved-halcyon-*, approved-pebble-*, nice-not-wow-meridian-logpanel, reject-anhermon-03364e9-serif-mono,
reject-ember-*, reject-guard-steel-slab, reject-meridian-method, reject-thin-line-art. Their rationale lives in
`../wow.md`, `../rubric.md` and `../genre-escape.md`.
