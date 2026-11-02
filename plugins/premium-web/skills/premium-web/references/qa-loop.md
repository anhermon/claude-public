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
