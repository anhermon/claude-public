# Factory page grammars

## Job 2 checkpoints

1. Terminal: independent window-first renderer and runtime added. Scroll selects a
   command chapter; a monotonic clock reveals one character per 35ms, then outputs
   its block instantly. Split diagram/log panes, 260ms scanline glitch, live clock,
   mobile stack and static reduced-motion frames are implemented. Render pending.
2. Collage: independent type-first renderer and bounded damped pointer/scroll
   controller added. Alternating type weights, flat cutouts, SVG paper plate,
   marquee, focus/hover/tap captions and mobile scroll reflow. Render pending.
3. Proof enrichment: stack and bleed each have six authored sections including
   two full-bleed drawn plates. Rail retains six content chapters with a paper
   commerce ground and staggered pricing rows. Terminal/collage have six chapters
   each; fictional specs created. Before renders preserved in .verify-before.
   Initial after-render: rail passes all hard gates but still has templaty tells;
   adding an illustrated full-width interlude. Baseline bleed had a mobile pricing
   collision; its variant mobile subject scale is now .72 (desktop stays 1.2).
4. Schema/loader/generator accept terminal and collage with isolated runtime file
   sets, shared commerce dependencies, cross-grammar rejection and palette-index
   checks. Eight new executable selftest cases pass, including controller mocks for
   actual typing, backwards scroll, bounded pointer, tap, mobile and reduced motion.
5. Documentation stays below 200 lines; factory skill below 110. Four new routing evals
   (two per grammar) use the existing case/prompt/regex-grader format under this
   skill's evals directory to respect edit scope. Model-based evals not run.
   Added a factory-local portfolio adapter: terminal has command/figure order;
   all five source specs pass with no structural siblings. The sibling gate alone
   cannot read terminal sessions; no files outside this skill were changed.
6. Final remote renders at 1440 and 390: rail, stack, bleed, terminal and collage
   all PASS with zero hard failures, no horizontal overflow, no void warnings and
   no craft failures. Latest reports are each piece/.verify/report.json. Iterations
   after baseline: rail 2, stack 3, bleed 1, terminal 2, collage 3.
   Tells: rail equal_card_grids/palette (2); stack none; bleed none; terminal
   caps_micro_labels/mono_body/mono_panels (3, expected console idiom); collage
   caps_micro_labels (1). None are classified templaty. Existing demos retain
   24–44px tap warnings; live visuals/clock/marquee have settling warnings.
   Looked at desktop and mobile section PNGs: console log/diagram separation,
   paper collage with the corrected outlined MARK, full-bleed contour plates,
   rail paper commerce, cleared mobile coil/pricing and cleared stat/ring caption.
   Stack and bleed have six authored sections; rail has four horizontal panels,
   drawn interlude and two commerce sections. New demos each have six chapters.
   Passed factory selftest, five-piece variation gate, 170 JS/MJS syntax checks,
   authored-code 800-line limit and git diff --check. Legacy byte golden passes.
   No browser launched. Final fonts, full interactive browser sweeps and model
   routing evals remain unverified; controller behavior is covered by mocks.
   Screenshot attachment is blocked: no ticket id was supplied and tickets.py
   is absent from PATH/worktree. Asked for both; no answer received yet. Before
   shots remain in each original demo's piece/.verify-before/sections/; after
   shots in piece/.verify/sections/. No screenshot/font/image assets are tracked.

## Job 1 handoff

1. Grammar contract: schema and loader accept `morph-subject` (default) and `rail`;
   legacy normalization keeps omitted grammar out of serialized output. Baseline example
   generated at `/private/tmp/pw-factory-legacy-before` for byte comparison. Original selftest passed.
   Grammar module selection is wired alongside the rail module in item 3.

2. Morph hero variants: independent stack, bleed and type-only compositions; optional
   wordmark and card/inline/no readout. Variant-only subject core freezes forms for
   orbit/static; orbit changes camera position. Original runtime files remain intact.
   Browser verification is reserved for the orchestrator.

3. Rail grammar: independent panel renderers, CSS and runtime selected at generation;
   damped pinned horizontal travel, bounded velocity typography, scale/wipe figure
   handoffs, scroll-driven SVG contours and progress. Mobile, reduced motion, no JS
   and over-height panels use a vertical stack. Shared calculator/FAQ follow vertically.
   Rail output contains no WebGL, three or motion-template dependencies.

4. Portfolio gate: `skills/premium-web/scripts/variation-check.mjs` accepts registries,
   directories or specs; prints a similarity matrix, ground sequence, hue spread and
   font pair, and rejects structural siblings, identical orders or close hues/fonts.
   Includes circular hue and registry-resolution selftests.

5. Documentation: concept decision table, grammar/hero/scroll contracts, panel kinds,
   parameter bounds, portfolio rule and render handoff in `references/grammars.md`.
   Factory skill updated; premium-web changed only in its factory router row.

6. Proofs: `.proofs/{rail-demo,stack-demo,bleed-demo}/spec.json` and generated `piece/`
   directories exist (Vellumet / Resonae / Glyphen, all labelled fictional). Generated
   offline with `--no-fonts`; no images, fonts or screenshots added. Added two routing
   eval cases under `evals/` in the existing case/prompt/regex-grader format.

   Passed: factory selftest (legacy byte golden, 12 hero/scroll combinations, schema,
   actual fixed vertex arrays, mock rail scroll/mobile/reduced-motion/overflow,
   shared pricing, idempotence); variation selftest and three-proof gate;
   verify-piece's offline selftest; syntax checks on 148 JS/MJS files including
   all 95 generated JS; `git diff --check`. All code files are below 800 lines;
   factory/router skills are 84/91 lines and grammars reference is 121 lines.

   Render handoff: no browser launched. Render at 1440 and 390, sweep the horizontal
   panels and unpin boundary, check final fonts, collision/void gates, `?rm`, `?nogl`,
   calculator, FAQ and focus. Attach before/after PNGs to the ticket with
   `tickets.py attach <id> <png> --caption ...` in the orchestrator session.
   Model-based plugin evals were not run; their cases are added, not claimed passed.
