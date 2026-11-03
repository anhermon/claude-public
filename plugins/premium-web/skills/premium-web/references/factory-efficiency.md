# Factory efficiency: building many pieces cheaply

Use when more than one piece is built (a portfolio, a template family, a batch of concept pages). The premium bar does not move;
the cost of reaching it does. Everything mechanical is a script, so the model spends tokens only on decisions and on looking.

Contents: 1 Baseline - 2 Principles - 3 Pipeline and gates - 4 Round budgets - 5 Context hygiene - 6 Concurrency - 7 Cache -
8 Model routing - 9 Token budget - 10 Known-defects exit

## 1. Baseline to beat (measured on one WebGL page, built twice)

| run | tokens | tool calls | wall clock | note |
|---|---|---|---|---|
| v1 (manual loop) | about 224k | not recorded | not recorded | every gate hand-run, screenshots read one by one |
| v2 (skill v2, scripts hand-written per piece) | about 137k | 248 | about 5 h | per-piece capture, poster, loop and QA scripts rewritten |

Target once the scripts and a scaffold exist: **60k tokens or less per piece**, under 100 tool calls. These are targets, not
measurements: log the real number per piece in `rounds.md` and replace this table's targets when they differ.

## 2. Principles

1. **Spec first, write each section once.** A complete SPEC.md (chapters, text region and subject region per chapter and
   breakpoint, 390 composition, asset plan, acceptance tests) is the cheapest rework prevention. Most v2 rework was layout
   collisions between copy and the subject that the spec did not name.
2. **Cheap gates before expensive ones.** Scripts are free; the critic costs minutes and tokens; a human look costs attention.
3. **Never carry an image in context unless it failed a gate.** Open only the stills a script names.
4. **Resume, do not restart.** State lives on disk (SPEC.md, `.verify/report.json`, `rounds.md`, the asset cache); a killed
   worker is continued from them.
5. **Do not hand-write what a script already does.** Per-piece capture, poster, loop and overflow scripts are the largest
   avoidable cost in the baseline.

## 3. Pipeline and gates (cheapest first)

| order | step | cost | command |
|---|---|---|---|
| 1 | structure and palette scan, console, overflow, fonts | free | included in verify-piece |
| 2 | per-section stills at 1440 and 390, void, subject/text collision, nav clip, tap targets, minimum font, fps | free | `node scripts/verify-piece.mjs <dir> --fast` |
| 3 | fix everything gate 2 lists (no images read yet except the named stills) | model | edit |
| 4 | LOOK at the named stills and the wow hand-off frames | model, few images | open only `failing_sections` |
| 5 | critic on flagged sections only | tokens + minutes | `node scripts/critic-batch.mjs <dir>` |
| 6 | final round: critic `--all` with wow, Lighthouse, fps, real mobile browser | highest | `verify-piece.mjs` (no `--fast`), `critic-batch.mjs --all --wow ID` |
| 7 | package | free | `node scripts/package-piece.mjs <dir>` |

Do not start gate 5 while gate 2 has hard failures: the critic will name the same defects at 100 times the price.

## 4. Round budgets

- At most **3 build rounds**, counted from the first round that has representative stills (after assets and the subject exist).
- At most **3 critic rounds per section** (`critic-batch.mjs` enforces it and skips the section with a verdict).
- After the budget: either escalate once (stronger model for that section, or replace its focal moment) or ship with a written
  known-defects list (section 10). Never loop a fourth time on the same section with the same approach.
- Treat a critic fix as a symptom (qa-loop.md): fix the focal visual or the collision, not the named widget.
- A single full critic round can cost 25 minutes on a 9-section page: plan the wall clock, run it in the background, work on
  another piece meanwhile.

## 5. Context hygiene

- Read the one-screen summary from `verify-piece` (about 40 lines). The full data is in `.verify/report.json`; grep it, never `cat` it.
- Open a screenshot only if it is listed under "failing sections" or you are doing the final LOOK. State what you saw in a line.
- Never paste a Lighthouse or console log: the summary carries the scores and the first failing audits.
- Large reference files: `grep -n` the heading first, read the section.
- Keep generated output (media, shots, raw images) out of the plugin and out of context.

## 6. Concurrency

- One worker per piece, from spec to package. Do not split one piece across workers: the spec is the only shared contract.
- At most **2 pieces concurrently**: scripts launch Chrome (and Lighthouse), and the critic is rate-limited by the subscription.
- Give each worker a unique port (`verify-piece` picks a free one) and its own piece dir; shared state is only the asset cache.
- Assume a worker can die without warning: it writes SPEC.md, `.verify/` and `rounds.md` as it goes; the next worker resumes.

## 7. What to cache (and what never to)

| cache | where | key |
|---|---|---|
| generated imagery | `$PREMIUM_WEB_ASSET_CACHE` (default `~/.cache/premium-web/assets`) via `scripts/asset-cache.mjs` | sha256(prompt, provider, size) |
| self-hosted fonts | one font dir per family outside the plugin; `get-font.sh` into each piece | family + subset |
| vendored libraries | pinned copies in the scaffold, never a runtime CDN | name + version |
| verify results | `<piece>/.verify/report.json`; re-run only after an edit | the piece dir |
| packaged media | `<piece>/media/` (package-piece reuses it; `--force` re-records) | the piece dir |

Flow for imagery: write the prompt to a file, `node scripts/asset-cache.mjs get prompt.txt --provider P --size WxH --out piece/img/x.png`.
Exit 0 = hit, use it. Exit 10 = miss: it prints the exact instruction; generate ONCE with `premium-web-imagery`, register it with
`asset-cache.mjs put <key> <file>`, then `get` again. The script never calls a provider and nothing generated is ever stored in the plugin.

## 8. Model routing

| work | model and effort |
|---|---|
| spec, direction, wow ideation, hard judgment (replace a concept, resolve a critic conflict) | strongest available, medium or high |
| section implementation from a finished spec and scaffold | mid tier (sonnet class), low or medium, with the spec as the brief |
| mechanical edits, renames, running scripts, reading a summary | light tier, low |
| verification scripts (`verify-piece`, `critic-batch --dry-run`, `package-piece`) | no model: free |
| the critic | a fresh mid-tier model per section (`CRITIC_MODEL`), never the builder |

Do not let a worker inherit the session's top model by accident: set model and effort explicitly on every spawn. Spend the strong
model on the spec and on the final look, not on typing sections.

## 9. Token budget per piece (target)

| stage | target tokens | how |
|---|---|---|
| spec + direction + wow | 12k | one strong-model pass, written to SPEC.md |
| scaffold + sections | 25k | sections written once from the spec, not iterated blind |
| gates and fixes (2 to 3 rounds) | 15k | scripts do the measuring; read summaries, not logs |
| looks (named stills only) | 5k | about 6 images across the whole piece |
| critic and final | 3k in the builder's context | the critic runs as a separate process; read its fix lines |
| package | 0 to 1k | one command |
| **total** | **about 60k** | v2 baseline was about 137k |

The split is an estimate for planning, not a measurement.

## 10. Known-defects exit

When the budget is spent and a gate still fails, ship only with this block in `rounds.md` and the report: the failing gate or
section, the evidence (stills path), why it was not fixed (budget, needs a new concept, upstream limit), and the cost to fix.
A hard gate (console error, overflow at 390, failed font, tap target under 24 px, subject over copy) is never shipped as a known
defect without a named human decision. State what was not tested (real device, Safari, screen reader).
