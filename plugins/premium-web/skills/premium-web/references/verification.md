# Verification and the critique loop

A passing build is not a passing render, and a passing render is not a premium page. Three gates, in order.

**Step 0 precedes all of them.** `chrome-shot.mjs` and `critic.py` exit **4** without a valid `## Step 0 classification` in NOTES.md whose `mode:` equals the run's mode
(SKILL.md Step 0; `PW_NOTES=<path>` or an ancestor of the output dir). Only `EVAL=measure-site.js` runs (reference measurement of other sites) are exempt. Exit codes everywhere: 0 clean, 1 failed,
2 usage / Chrome would not start, 3 UNVERIFIED, 4 classification missing or invalid.

**App mode (WORK)** runs the same three gates with different instruments: gate 1 adds a Playwright walk-through per primary task (steps, keystrokes, time-to-first-result written to
`walkthrough.json`, console errors fail it); gate 2 is `MODE=app EVAL=scripts/tells.js SECTIONS="[data-screen]"` (hard fails and thresholds: wow.md "App mode"; no `WOW=` frames, no `data-wow`) plus `saturation.py`;
gate 3 is `critic.py <out>/sections --mode app --signature <screen> --signature-test "<sentence>" --walkthrough walkthrough.json` (screens, flows, signature clarity, generic-template verdict;
exit 3 when the walk-through or the tells scan is missing). The rest of this file describes the marketing instruments; the unrunnable-gate rule applies to both.

## Gate 1: it works (scripts, all zero-dependency except Chrome/Xcode/npx)

```bash
node scripts/serve.mjs <site-dir> 8790 &          # no-store, trackers stubbed, probe injected; busy port -> next
node scripts/chrome-shot.mjs http://localhost:8790/?noprobe <out>/chrome 1440,390   # shots + checks, exit 1 on problems
scripts/shoot.sh http://localhost:8790/ <out>     # Chrome + real Mobile Safari (private throwaway Simulator)
scripts/lighthouse.sh http://localhost:8790/ <out>/lh   # mobile x3 + desktop, trackers blocked
```
chrome-shot checks: horizontal scroll (and which element is too wide), fonts that failed, which font actually
RENDERED per selector (CDP CSS.getPlatformFontsForNode), console errors and exceptions, trackers blocked, missing alt.
macOS has no GNU `timeout`. Portable wrapper for any long command (claude -p, curl, builds):
`perl -e 'alarm shift; exec @ARGV' 600 <cmd>` (or `gtimeout` if coreutils is installed, or a Python `subprocess.run(timeout=)`).
Never write bare `timeout 600 cmd` in a script or checklist.
Flags: `RM=1` reduced motion, `SCHEME=light|dark`, `EVAL=file.js` (measure-site.js, tells.js), `H=` viewport height.

Simulator (what shoot.sh does): `xcrun simctl create` a private device from "iPhone 17 Pro" on the newest iOS
runtime, boot, `bootstatus -b`, warm-up openurl (burns off first-launch Safari tips and system notifications),
then per shot `openurl "<url>?r=$RANDOM&vh=N"`, wait 7s, `io screenshot`; device deleted on exit.
Gotchas: Safari's UA says "iPhone OS 18_7" whatever the runtime (never UA-sniff); Simulator Safari caches hard
(serve.mjs sends no-store, shoot.sh cache-busts); the Simulator cannot block requests (serve.mjs strips trackers);
reduced motion can only be set by hand in Settings; no fps, Low Power Mode or thermal truth. Check BOTH colour
schemes: the Simulator runs light by default and found a dark-poster/dark-text bug Chrome (dark) missed.
**Run the Simulator and Lighthouse gates on the FINAL round and name that round in the report.** sealref shipped
r4 Safari/Lighthouse evidence for an r8 page; the re-run on the final page found a hero button over the sticky stage
and a clipped particle word at 402px that Chrome headless at 390 never showed (Safari's toolbars shorten the viewport).

## Gate 2: it is not templaty

```bash
EVAL=scripts/tells.js SHOTS=0 SECTIONS=1 WOW=<signature selector> node scripts/chrome-shot.mjs <url>?noprobe <out> 1440,390
RM=1 WOW=<signature selector> SHOTS=0 node scripts/chrome-shot.mjs <url>?noprobe <out> 1440,390    # fallback frames, SAME <out>
```
The RM=1 run needs no `EVAL` and does not touch `report.json` (it writes `report-rm.json`), so the eval from the first run survives for
critic.py. Frames are clocked from the scroll to the wow (t1 = 250 ms ... t7 = 4.5 s); a scroll-reveal is still moving for ~.6 s + stagger,
so add `WOW_DELAY=900` (ms, shifts every frame) when the wow reveals on scroll, so the frames show the settled reveal. Apps: `MODE=app` and no WOW frames (see above).
`<out>/report.json` -> `eval.hits`: 4+ structural tells = fail before any taste discussion (rubric.md).
A deliberate repeated component (three registered sheets, table rows) is marked `data-tell-ok` in the markup so
`equal_card_grids` / `mono_panels` skip it; do not use it to hide real card grids. Saturation (toy palette):
`python3 scripts/saturation.py <out>/*.png` (also `eval.tells.saturated_fields`); mean hot share > 0.12 = fail.

## Gate 3: every section clears the rubric (the critique loop, mandatory)

```bash
python3 scripts/critic.py --calibrate             # once per session: the critic must fail/pass the gallery anchors
python3 scripts/critic.py <out>/sections --wow wow --wow-test "<acceptance test>"   # every section + the signature + the whole page; exit 1 = not done, 3 = critic unavailable (quota/session limit: verdict unknown, re-run after reset)
# progress lines go to stderr ([critic +Ns] start/done ...); a round is ~5-20 min, so run it in the background and tail stderr
```
- A **fresh** critic per section (`claude -p --allowedTools Read`, Sonnet by default; `CRITIC=codex` when Codex has
  quota). It sees the section at 1440 and 390, two PASS and two FAIL anchors from gallery/, and the rubric.
  The builder never grades its own work.
- Pass/fail is computed by the script from the scores (explanatory visual >= 4, nothing < 3, at most two 3s, no ban hits, section saturation <= 0.20), the
  wow score (>= 4, fallback >= 3) and the page verdict (not "could be 20 others", closer to approved, hot-pixel share of the wide shots <= 0.12).
- Precedence: the critic wins. If critic.py fails and tells.js is clean, the page FAILS (gate 3 is required; tells only add failures).
- Loop: read `critic.json` fixes -> change the page -> re-shoot -> re-run. Log each round (scores + what changed)
  in NOTES.md. Stop only when the script exits 0. If a section fails three rounds, the concept for that section is
  wrong: replace the visual, don't polish it.
- Why calibrated anchors: an uncalibrated critic called the Meridian method section "visually rich" (2026-10-01).
- Calibration result 2026-10-01 (Sonnet): rejects fail with explanatory_visual=1 and stick-figure ban hits; the
  code-drawn Guard passes 4-5; wow v4 hero 4, Meridian panel 3; pages ember/meridian fail, pebble/halcyon pass.
  The critic is stricter than what shipped on the anhermon observe plate (whitespace): treat it as the bar.

## A gate that cannot run: report UNVERIFIED

No Chrome/CDP (chrome-shot, tells.js, shoot.sh), no `claude`/`codex` session, quota or network (critic.py exit 3),
no Xcode (Simulator), no Lighthouse, a missing walk-through (app): that gate's result is `UNVERIFIED: <gate>: <reason>`, in NOTES.md and at the top of the
reply, next to the gates that did run (state the overall status as NOT VERIFIED). Never report it as pass, never say the page or app is premium or done, never
substitute functional checks, a manual read or self-scoring for it. Fix the cause (start Chrome, wait for the quota
reset, run it where a session exists) or hand that gate to the user. Paste each gate's real output (tells hits,
saturation mean, critic.json summary) into the report; a gate without pasted output counts as not run.

## Then: LOOK yourself

Read every screenshot (sections, wow frames, Safari). Generic checklist per shot: does it look like a template? Is
there one focal point? Real data visible? Any collision in display type (descenders, kerning gaps at 1440 and 390)?
Text over busy imagery readable? Honeypot invisible, checkbox ~20px? Overflow at 390? Same page as you think
(shared machines: other agents run serve.mjs too; shoot.sh prints the title)?

## a11y, SEO, OG (Lighthouse >= 95 perf / 100 a11y, best practices, SEO on mobile)

Marking slips, ghost marks or any decorative/duplicate text kept in the DOM: `inert` (not only `aria-hidden`), or Lighthouse
color-contrast still fails on it. One h1 (a tool's display numeral is a `<p>`/`<div>`, not a second h1); landmarks; skip link; 4.5:1 text contrast (the `--faint` token is the floor); 44px targets (24px minimum
for inline controls); visible focus; alt on every meaningful image, `alt=""` on decoration; `lang`; meta
description; canonical; JSON-LD; OG 1200x630 with text composited locally (never generated); theme-color per scheme.
