# premium-web

A Claude Code plugin for building (and redesigning) premium web pages. Every section gets a drawn explanatory visual, the page gets one signature "wow" moment, and a calibrated critic, not the builder, decides when it is done.

**Since 2.0 it is also a Claude Code [mod](https://claude.com/blog/claude-code-mods).** A premium page is a taste decision, so the skill no longer builds one page and hopes: it builds several materially different **candidates**, shows them in a pane, and finishes the one you pick.

## How a build goes

1. Claude decides how many candidates to build (see "Candidate count"), writes that many genuinely different directions (different style, palette, type voice, layout and signature wow idea each) and builds them in parallel.
2. Each gets one critic pass and a screenshot; Claude writes `.premium-web/candidates.json` and calls the `premium_web_present_candidates` tool, then stops and waits.
3. The **Premium candidates** pane opens (or run `/candidates` any time; `/candidates 2` or `/candidates b` jumps to a candidate):
   - tab per candidate (hotkeys `1`-`9`), with the direction, scores, notes and screenshot (drawn in terminals that show images; a path line on desktop);
   - `o` **Open in browser**: the candidate's preview URL, or its folder served on `127.0.0.1` (a tiny `python3 -m http.server`, one per candidate, stopped when you close the pane or the session ends);
   - `p` **Pick this one**; `c` **Request changes** (reveals a field); `f` **Feedback on all** (reveals a field).
4. Your pick or feedback is saved to `.premium-web/decision.json`, remembered per project, and sent to Claude as a message. Feedback sends Claude back to iterate (that candidate, or all) and present again. A pick takes only the chosen candidate through the full critic loop to final.

Without the mod (older Claude Code, mods disabled, `claude -p`) the skill falls back to listing previews and screenshots in chat and asking you to pick.

## Requirements

- Claude Code **2.1.287 or later** for the mod (mods are early access; check `claude --version`). On builds where function hooks are still gated, set `CLAUDE_CODE_ENABLE_FUNCTION_HOOKS=1`. The skill itself works on any version.
- `python3` on `PATH` for "Open in browser" on candidates that have a `dir` but no `url`.

## Candidate count

Default **3**. Change it for good in your Claude Code settings (`candidateCount`, 1-6):

```json
{ "pluginConfigs": { "premium-web@claude-public": { "options": { "candidateCount": 5 } } } }
```

(the key is the plugin id as `/plugin` shows it; for a copy loaded with `--plugin-dir` it is `premium-web@inline`). Or override it per run in your request ("build 5 candidates", "just one"): the request wins over the setting, and more than 6 is capped. The skill reads the setting through the `premium_web_get_settings` tool.

## Security

**Mods are not sandboxed**: the hooks module runs with your user's permissions. This one is deliberately small (`hooks/register.ts`, `hooks/lib.ts`, read them before installing). It:

- reads `<project>/.premium-web/candidates.json` and writes `<project>/.premium-web/decision.json`, plus its own `$.store` entry;
- validates `candidates.json` strictly (ids `[a-z0-9-]{1,32}`, size caps, paths must stay inside the project, `url` must be http(s)); every hook catches its errors and falls back to Claude Code's behaviour;
- runs `python3 -m http.server --bind 127.0.0.1` (never `0.0.0.0`), `uname -s` and your OS's open-a-URL command (`open` / `xdg-open` / `cmd start`);
- sends your pick/feedback back to Claude with `$.prompt.submit`. It makes no other network calls, reads no environment variables and handles no secrets.

Limits: path checks are lexical (a symlink inside the project that points elsewhere is not followed or blocked); the local preview server serves the candidate folder to anything on this machine while it runs.

## Contents

`.claude-plugin/plugin.json` (manifest, `candidateCount` setting) · `hooks/` (the mod) · `tests/` (run with `CLAUDE_CODE_ENABLE_FUNCTION_HOOKS=1 claude plugin test .`) · `skills/premium-web/` (rubric, wow ideation, genre-escape and verification references, `references/candidates.md`; scripts for screenshots, Lighthouse, saturation and the critic; an optional image-generation MCP server).

Image keys are read through [vaultlet](https://github.com/anhermon/sealref) refs only; set `IMAGEGEN_VAULT_GROUP` to your group. Never paste keys into config.
