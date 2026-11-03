# QA loop: render, look, critic

Countermeasure for F6, F8 and F9 (failure-modes.md). A passing build is not a passing render, and a passing render
is not a premium page. Metrics are gates, never goals. All scripts are zero-dependency except Chrome, Node 22+,
Python 3 (Pillow for `saturation.py`), and optionally Xcode and `npx`.

Contents: 1 Loop and budget - 2 Gate 1 works - 3 LOOK - 4 Gate 2 structure - 5 Gate 3 independent critic -
6 Calibration - 7 Headless GPU and device notes - 8 Accessibility and SEO - 9 Release hygiene

## 1. Loop and budget

render -> LOOK -> fix -> re-render, then the independent critic, then fix, repeat.
- Round budget: at most 3 critic rounds per section. A section that fails 3 rounds has the wrong concept: replace
  its focal moment, do not polish. At most 4 whole-page rounds; then report what still fails instead of looping.
- The early rounds LOOK and structure scans only; run the critic when you would otherwise ship (it takes minutes
  per run; `CRITIC_JOBS` runs sections in parallel; limit early critic runs to a subset of sections).
- Build rounds count from the FIRST critic input, not from the first line of code: a WebGL or generated-asset page needs two
  builds before any representative still exists. One critic round can take 25 minutes (9 sections plus wow); budget for it.
- Cheap gates before expensive ones: `node scripts/verify-piece.mjs <dir> --fast` every round, the critic only on the sections it
  flags (`node scripts/critic-batch.mjs <dir>`), the full run (Lighthouse, fps) on the final round. See `factory-efficiency.md`.
- Log each round (scores and what changed) in SPEC.md or a `rounds.md` beside it.
- Run the real-browser and Lighthouse gates on the FINAL round and name that round in the report.

## 2. Gate 1: it works

```bash
node scripts/serve.mjs <site-dir> 8790 &        # no-store, trackers stubbed, probe injected; busy port -> next
node scripts/chrome-shot.mjs "http://localhost:8790/?noprobe" <out>/chrome 1440,390   # shots + checks, exit 1 on problems
scripts/shoot.sh http://localhost:8790/ <out>   # Chrome plus real Mobile Safari (private throwaway Simulator, macOS + Xcode)
scripts/lighthouse.sh http://localhost:8790/ <out>/lh 3   # mobile x3 + desktop, trackers blocked
```
chrome-shot checks: horizontal scroll (and which element is too wide), failed fonts, which font actually rendered
per selector, console errors and exceptions, trackers blocked, missing alt. Widths under 768 use true mobile device
emulation (touch, device scale factor 2). Flags: `RM=1` reduced motion, `SCHEME=light|dark`, `EVAL=file.js`,
`H=` viewport height, `SECTIONS=1`, `WOW=<selector>`, `WOW_ACT=<js>`, `SHOTS=0`, `CHROME_FLAGS` extra Chrome args.
Check BOTH colour schemes if the page supports both. Lighthouse on localhost: trust accessibility, SEO, best
practices and CLS; treat performance as relative and read the median of three mobile runs.

One command for all of it: `node scripts/verify-piece.mjs <dir> [--fast]` serves the page and runs this gate plus the structure
scan, saturation, stepped-scroll section stills (1440 and 390, pixel-settled), void, subject/text collision, subject clipped by the
nav, tap-target and minimum-font checks, scroll fps and Lighthouse; it prints <= 40 lines and writes `.verify/report.json` and
`.verify/sections/<nn-id>/{1440,390}.png`. Open only the stills it names. Declare the persistent subject to it (`piece.json`
`verify.subject`, or `verify.subjectBox`: a JS expression returning `{x,y,w,h}` in viewport px) or the collision and nav-clip
checks are skipped.
- A page whose subject is a fixed canvas, a fixed nav and damped scroll does not fit `SECTIONS=1`. Bring your own shots: the
  critic only needs `<sections-dir>/<nn-id>/1440.png`, `390.png` (a tall section adds `1440-p2.png`); `verify-piece` writes exactly
  this layout. Any `<width>-tN.png` in a section dir is judged too: give pinned or morphing sections 3 to 5 frames.
- Damped or eased scroll (the visible state follows the scroll position with lag): a jump-scroll then a fixed wait still shoots a
  transition. Scroll in steps and wait until two frames match, or until the state value has caught up, before shooting. Judge
  an in-flight frame as a hand-off, never as a defect.
- Reveal states: words hidden at low opacity fail axe/Lighthouse `color-contrast` for every not-yet-revealed node. Treat those as a
  reveal artefact (run Lighthouse after scrolling the whole page, or keep hidden text at 4.5:1), not 30 contrast defects.
  `aria-label` is only valid on headings and landmarks: a split-text effect on a `<p>` must append a visually hidden copy and hide
  the generated spans, or Lighthouse reports `aria-prohibited-attr`.
- The font check reports the nearest named instance for a variable font ("SemiBold" for a weight-300 h1). Verify the weight by the
  computed `font-weight` / `font-variation-settings`, not by that label.

macOS has no GNU `timeout`; wrap long commands with `perl -e 'alarm shift; exec @ARGV' 600 <cmd>`.

## 3. LOOK (mandatory, by you)

Read every screenshot: sections, wow frames, real-browser shots. Per shot ask: does it look like a template? Is
there one focal point? Real data visible? Any collision in display type (descenders, kerning gaps) at 1440 and 390?
Text over busy imagery readable? Honeypot invisible? Overflow at 390? Is it the page you think (shared machines
run other servers; `shoot.sh` prints the title)? State what you saw in the report.
- **Mid-animation frames**: `WOW=<selector>` captures 7 time frames or one set per scroll beat. A good last frame
  with a messy middle fails. Scene transitions stay under 0.7 s so captures at fixed offsets show legible states.
- **True 390 viewport**: emulate the device; do not resize a desktop window. A real browser on the final round finds
  what headless misses (toolbars shorten the viewport; a button overlapped content at 402 px).
- **Overflow guard every round**: the report's `scrollWidth` must equal the viewport width; a late CSS override
  can break it silently.
- **Figures in the first 900 px of their section**: the critic sees viewport shots only.

## 4. Gate 2: structure and palette

```bash
EVAL=scripts/tells.js SHOTS=0 SECTIONS=1 WOW=<selector> node scripts/chrome-shot.mjs "<url>?noprobe" <out> 1440
RM=1 WOW=<selector> SHOTS=0 node scripts/chrome-shot.mjs "<url>?noprobe" <out> 1440     # fallback frames
python3 scripts/saturation.py <out>/*.png
```
One width per call when `SECTIONS=1`. `<out>/report.json` -> `eval.hits`: 4 or more structural tells is a fail before
any taste discussion; `craft_fail` also fails the page. A deliberate repeated component is marked `data-tell-ok="reason"`
so `equal_card_grids` and `mono_panels` skip it; never use it to hide real card grids. Mean hot-pixel share above
the `saturation.py` limit is a fail. A scroll-scrubbed wow needs `data-scene` on the WOW element for scroll frames.

## 5. Gate 3: independent critic

```bash
python3 scripts/critic.py <out>/sections --wow wow --wow-test "<acceptance test>" \
   [--pass-refs DIR] [--fail-refs DIR]
python3 scripts/critic.py --calibrate DIR        # DIR contains pass/ and fail/ section images
```
- A FRESH critic per section (`claude -p --allowedTools Read`, Sonnet by default; `CRITIC=codex`), seeing the
  section at 1440 and 390, the rubric (section-craft.md, wow.md, failure-modes.md checks) and, if given, one or two
  anchors from `--pass-refs` and `--fail-refs`. The builder never grades its own work.
- Pass/fail is computed by the script from the scores. Exit 0 = pass, 1 = fail, 2 = usage, 3 = critic unavailable
  (quota: the verdict is unknown, not failed).
- Treat a critic fix as a symptom. It rewards features it can name (leader lines, a comparison table, labelled points), not craft
  it can feel; chasing every list grows the page into a feature sheet. Fix the focal visual or the collision, not the named
  widget, and log the fixes you decline with one line of why.
- The critic judges stills. A pinned, scroll-driven chapter whose payoff is a hand-off scores at most 3 on focal visual from one still:
  supply `<width>-tN.png` frames for it. Wow frames need reduced-motion twins `<width>-rm-tN.png` or `critic.py` exits 2.
- Run it only where it pays: `node scripts/critic-batch.mjs <dir> [--sections a,b | --all] [--max-rounds 3]` (default = the sections
  `verify-piece` flagged; a section past its round budget is skipped with the replace-or-ship verdict).
- Wow is judged separately and is mandatory: below 4 fails the page whatever else scores; the fallback frame must
  score at least 3.

## 6. Calibration against external references

A rubric-only critic scored too strictly in pilots (nothing in the corpus above 4, so "every section 4 or higher"
was unreachable); a critic with unlabeled anchors can drift lenient. Set the bar from outside the repo:
1. Collect 6-12 section screenshots at 1440 of pages the owner has judged: label each `pass` or `fail`, plus a
   few "nice but not wow" in `fail/`. These live in a folder you supply, never in the plugin.
2. `critic.py --calibrate DIR` judges each and reports mismatches. With no DIR it prints how to build a corpus.
3. If good pages fail on a criterion, lower the PASS bar via `CRITIC_FOCAL_MIN` (env) only with the corpus as
   evidence; if bad pages pass, add a ban hit or raise it. Record the corpus size and date next to the setting.
4. Pass `--pass-refs` and `--fail-refs` with one or two anchors per section type when judging real work.

## 7. Headless GPU and device notes

- WebGL in headless Chrome needs a real GPU path or captures are blank or software-slow: on macOS add
  `--use-angle=metal --ignore-gpu-blocklist` (`CHROME_FLAGS`).
- Safari's UA reports a frozen OS version; feature-detect, never UA-sniff. Simulator Safari caches hard (`serve.mjs`
  sends no-store). Reduced motion can only be set by hand in Simulator settings.
- Record real frame timing, not only Lighthouse: scroll the page under a 4x CPU throttle and report p50/p99 frame time (the
  page's own `stats()` if it has one). The throttle slows the CPU, not the GPU: a GPU-bound scene looks better than a phone will.
  `verify-piece` does this and labels it a relative signal.
- A readout that prints a measured value ("0.00 ms") must survive the browser's coarsened `performance.now()`: print "<0.1 ms" or
  time N repeats and divide. Otherwise the critic, rightly, calls it fake.
- The Simulator and emulation cannot tell real fps, Low Power Mode or thermal throttling; test a GPU-heavy wow on a
  real phone before launch.
- Other agents may drive the same Simulator; `shoot.sh` creates a private device and deletes it on exit.

## 8. Accessibility and SEO

Gate at Lighthouse accessibility 100 and best practices / SEO 95 or higher on mobile (a deliberate `noindex` lowers
SEO; state it). One h1; landmarks; skip link; 4.5:1 text contrast; 44 px targets (24 px minimum for inline
controls); visible focus; alt text; `lang`; meta description; canonical; JSON-LD; OG image 1200x630.

## 9. Release hygiene (for the skill itself)

Before releasing a change to this plugin, `grep -rniE` the whole plugin for private project names, stored example folders, and
image or font binaries (`.png`, `.webp`, `.avif`, `.woff2`) inside skills (format support in scripts is allowed). Examples and anchors are
run-time inputs, never shipped.
