# premium-web

Build web pages that do not look AI-generated. The core skill (`premium-web`) is a small router: it forces written
design decisions before code, names the failure modes of generated sites, and closes the loop with a render, a look,
and an independent critic. Four sub-skills hold the techniques.

| skill | role |
|---|---|
| `premium-web` | process, failure modes, direction, section craft, wow, QA loop, reproduction briefs; scripts (serve, chrome-shot, tells, saturation, critic, Lighthouse) |
| `premium-web-motion` | scroll choreography, text and loader grammar, transitions |
| `premium-web-webgl` | 3D and shader scenes (characters and mascots: `animated-objects`) |
| `premium-web-svg` | code-drawn figures, diagrams, animated SVG, icons, filters |
| `premium-web-imagery` | image and video generation (capability detection, art direction, fallbacks, scrub media) |

The sub-skill templates demonstrate mechanics (stage rig, reveals, hand-offs, filters), not finished design: they use
a neutral system-font placeholder and plain content. Build the page's own look on top of them.

Start at `skills/premium-web/SKILL.md`. No examples, screenshots, generated images or fonts ship in the plugin;
anchors for the critic are supplied at run time (`critic.py --pass-refs DIR --fail-refs DIR`, `--calibrate DIR`).

Requirements: Chrome and Node 22+ for capture, Python 3 with Pillow for `saturation.py` and `critic.py`, the `claude`
CLI (or `codex`) for the critic. Offline self-test: `python3 skills/premium-web/scripts/test_critic_parse.py`.
Evals: `claude plugin eval <path-to-this-plugin>` (see `evals/`).
