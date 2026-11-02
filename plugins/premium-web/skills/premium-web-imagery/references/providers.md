# Providers, the imagegen MCP server, licences and terms

Contents: the MCP server, provider order, quota behaviour, browser handoff, licence and ToS notes, privacy.

## The `premium-web-imagegen` MCP server (`mcp/imagegen/`)

Stdio server over `core.py` (Python 3, Pillow; the `mcp` package only for the server). Same code path from the shell:
`python3 mcp/imagegen/core.py {providers|art|gen|compare|optimise|review|complete} ...`.

| Tool | Does |
|---|---|
| `list_providers()` | which providers are usable now, and why not |
| `art_direct(brief, slot, style_preset, colours)` | slot composition + style look + negative list; returns the prompt and a review checklist |
| `generate_image(prompt, aspect, out_dir, name, provider="auto", variants=2)` | idempotent names `<slug>-<hash8>.png`, skips existing, appends `MANIFEST.md`, global rate limit |
| `compare(paths)` | contact sheet + dimensions, aspect drift, bytes, near-duplicates (dHash); no text detection |
| `optimise(path, widths, formats)` | AVIF + WebP at 640/1024/1536, never upscales, srcset strings, budget warnings |
| `record_review(path, verdict, note)` | verdict (keep / cut / redo) into `MANIFEST.md` |
| `complete_browser_job(job_id, path)` | finishes a browser handoff after a browser agent saved the file |

Register (the user runs this; a skill never edits config):

```bash
claude mcp add premium-web-imagegen -- uv run --with mcp==1.29.0 --with pillow==12.3.0 \
  python <path-to-plugin>/skills/premium-web-imagery/mcp/imagegen/server.py
```

Tests: `python3 mcp/imagegen/test_core.py` (fake codex, fake secrets runner and a local HTTP stub stand in for every provider; no network, no spend).

## Provider order (`auto`)

codex (`codex exec --skip-git-repo-check`, ChatGPT login) -> local (CLI from `IMAGEGEN_LOCALGEN` or `localgen` on PATH) ->
API providers OpenAI / Gemini API / fal / Together / Replicate (only when the key exists in the configured secrets group;
run through a secrets runner as a child process so the key never enters the prompt, log, or this process) -> browser handoff.

- **Codex quota**: on its usage limit codex still exits 0. The tool reads its own log, reports `failed: codex quota/usage limit (try again at ...)` and never adopts an image it did not name (other agents' images land in the same generated-images folder). When generation is unavailable, draw in code and say so; do not wait.
- **Local CLI contract**: `<cli> <prompt> --size WxH --quality draft|final --out PATH`. Quality via `IMAGEGEN_LOCAL_QUALITY`.
- **Secrets**: `IMAGEGEN_SECRETS_GROUP` names the group, `IMAGEGEN_SECRETS_CMD` the CLI (default `secrets-runner`); only key NAMES are listed, never values.
- State and browser jobs live under `IMAGEGEN_STATE` (default `~/.cache/premium-web-imagegen`).

## Browser handoff (consumer web UIs)

Writes a job file with browser-agent steps and returns `needs_browser_agent`. Terms-of-service grey area, stated plainly:
automating a consumer web UI is not what those products intend. Acceptable only as the account owner's own logged-in session,
at low volume, never solving CAPTCHAs, never entering credentials; stop and report on any login, paywall or CAPTCHA. Download
buttons are often blocked for automation; a tight screenshot of the image is the fallback capture (lower resolution: note it in the review).

## Licence and ToS notes (practice, not legal advice)

- Read the provider's terms for commercial use, attribution and output ownership before shipping; terms differ per plan and change. Record provider, model and date in `MANIFEST.md`.
- Some jurisdictions give no copyright to purely machine-generated images; a project that needs ownership should add human authorship (compositing, drawing, significant edits) or use code-drawn assets.
- Do not prompt with living artists' names, brand names, trademarks or real people's likenesses. Do not generate or imply endorsements.
- Image generators can reproduce recognisable stock or watermark patterns; reject and regenerate.
- Disclose AI-generated imagery where the context requires it (editorial, news, regulated claims, product photos presented as real).
- Generated "customers", "team photos" or "product shots" presented as real are fake proof. Label concepts, or leave the slot honestly empty.
- Fonts and any licensed asset used in compositing carry their own licences; fetch fonts at build time, do not bundle.

## Privacy

Prompts and reference images go to the provider. Do not include secrets, unreleased product names under NDA, or personal data in prompts or reference images unless the provider's terms and the user allow it.
