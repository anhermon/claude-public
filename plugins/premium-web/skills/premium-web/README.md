# premium-web

A Claude Code skill for building premium web pages. Start at SKILL.md. This file records what has been tested.

## Tested (2026-10-01 to 10-02, macOS, Chrome headless over CDP, iOS Simulator Safari 18.7)

Real runs:
- `scripts/chrome-shot.mjs`: viewport shots, `SECTIONS=1`, `WOW=` (7 time frames or 6 scroll positions, plus `RM=1`
  poster frames), `EVAL=`. Ran on the anhermon site, the skeleton, Plumb, sealref, and pinned ember, meridian,
  pebble and halcyon snapshots. A dead server makes it exit non-zero; it no longer screenshots Chrome's error page.
- `scripts/tells.js`, calibrated as hits at 1440 / 390. A page is templaty at 4 or more.

  | page | hits (1440 / 390) | verdict |
  |---|---|---|
  | ember r1 (Angel rejected it) | 9 / 7 | templaty |
  | ember r2 (Angel: "mid") | 6 / 4 | templaty |
  | meridian (rejected) | 5 / 4 | templaty |
  | pebble (approved) | 2 / 3 | not templaty |
  | halcyon (approved) | 2 / 2 | not templaty |
  | Plumb (acceptance page) | 0 / 0 | not templaty |
  | sealref (acceptance page) | 1 / 1 (material) | not templaty |

  Re-run 2026-10-02 after no_fullbleed learned contrasting full-width sections with display type.

- `scripts/critic.py`: `--calibrate` passed twice (`claude -p`, Sonnet). It judged section, wow and page on Plumb.
  The reachability check on Angel-approved pages led to the current pass rule. A quota error now exits 3 and prints
  "unavailable"; this path was tested with a fake `claude` on PATH.
  The claude critic returns structured output (`--json-schema`, typed per judge); free-text JSON lost 4 verdicts on
  sealref r8. `parse_reply` is the fallback (and the codex path), self-check `python3 scripts/test_critic_parse.py`.
  An unparseable reply keeps the full text under `raw` in critic.json. `--calibrate` re-passed after the change.
- `scripts/shoot.sh`: a private throwaway Simulator device, created and deleted per run. It ran on the skeleton
  (where it found the light-mode poster bug) and on the final sealref (r8b, 2026-10-02). On the final page it found two
  defects that Chrome headless at 390 did not show: at 402px the hero "Install from GitHub" button overlaps the
  transcript box, and the `«redacted:demo/API_KEY»` particle word clips at the box edges. Both are left unfixed (page frozen).
- `scripts/lighthouse.sh` on the final sealref (r8b):
  - desktop 100/100/100, LCP 0.4 s, CLS 0, TBT 0 ms, 112 KiB
  - mobile 98/100/100, LCP 1.8 s, CLS 0
  - SEO is 60 on both because of the deliberate `noindex`
- `scripts/measure-site.js`: tested on linear.app. `get-font.sh`: tested on Familjen Grotesk and Fragment Mono.
- `mcp/imagegen`:
  - 12 unit tests pass (`uv run --with pillow==12.3.0 --with mcp==1.29.0 python -m unittest test_core`)
  - the stdio checks `initialize`, `tools/list` and `tools/call` pass
  - one real Codex call hit the usage limit; the quota path now reports the reset time and never adopts another
    session's image

Mocked or untested:
- Live API image providers. No keys were available; the 5 API adapters run only against mocks.
- A full Codex image generation (quota exhausted until 2026-10-02 01:58).
- Gemini-web and Higgsfield browser handoffs.
- Audio-reactive and physics recipes.
- Real-device fps (particle budgets are from an M-series Mac in Chrome).

## Acceptance test (built only from the skill)

- `examples/plumb/`: Swiss/data concept (log search). Shots and critic output are in `shots/`.
- `examples/sealref/`: terminal-native concept (a real tool; facts from its README at c069111). Shots are in
  `shots/`; real Mobile Safari shots are in `shots/safari/`.

Neither page clears the section bar (final critic, shots/sections/critic.json): sealref r8b 0/6 sections, WOW 4 /
fallback 3 / motion 3, PAGE PASS; Plumb r8b 1/6, WOW 4 / 4 / 3, PAGE FAIL (an earlier run passed it).
Serve either one with `node scripts/serve.mjs examples/<name> 8860`. Details and open weaknesses are in NOTES.md.
