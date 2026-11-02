# Capability detection (run FIRST, before any prompt is written)

Contents: the ladder, how to probe each rung, what to record, what to say when nothing is available.

Never assume image generation exists. Probe, record the result in the asset plan, and pick the rung once for the whole set
(mixing a generated hero with a code-drawn rest is fine; mixing three providers inside one set is not: the looks diverge).

## The ladder (take the first rung that works)

| # | Capability | How to detect | Notes |
|---|---|---|---|
| 1 | `premium-web-imagegen` MCP | its tools appear in the session tool list (`list_providers`, `art_direct`, `generate_image`, `compare`, `optimise`, `record_review`) | Best: art direction, idempotent names, manifest, optimise built in. Server lives in `mcp/imagegen/`; see `providers.md` to register it. |
| 2 | Any other image / video generation MCP | scan the session tool list for names containing `image`, `imagen`, `flux`, `video`, `gen` | Use as-is. Still apply the style sheet and post-processing from this skill. |
| 3 | Codex image generation | `command -v codex`, then `python3 template/pipeline.py detect` | `codex exec` with an image tool, ChatGPT login. Quota applies, see `providers.md`. |
| 4 | Provider API | a key in the environment or a secrets manager: `OPENAI_API_KEY`, `GEMINI_API_KEY`, `FAL_KEY`, `TOGETHER_API_KEY`, `REPLICATE_API_TOKEN` | Keys never enter prompts, logs or the page. Only a child process sees them. |
| 5 | Local model (FLUX.2-klein, Z-Image-Turbo and similar) | a CLI on PATH, or `IMAGEGEN_LOCALGEN=/path/to/cli` | Offline, no quota, slow (minutes per image), needs RAM headroom. Fine for plates and backdrops, weaker for photoreal heroes. |
| 6 | Browser handoff to a consumer web UI | a browser-automation tool in the session and the user's own logged-in session | Last resort, grey area on ToS, see `providers.md`. |
| 7 | None | all of the above absent | Procedural path below. This is a normal outcome, not a failure. |

## One-shot probe

```bash
python3 skills/premium-web-imagery/template/pipeline.py detect   # binaries + env keys + a fallback line
```

It cannot see MCP tools (those are session-level): read your own tool list for rungs 1 and 2.

## Record the decision

Write one line into the asset plan: `generation: <rung>, provider <name>, seed <n>, style sheet <file>`. If rung 7: `generation: none, procedural`.
The report to the user must say which rung was used. Never imply generated imagery when assets are code-drawn.

## Rung 7: procedural path (nothing can generate)

Do not wait, do not ask the user to install something first, do not ship empty frames. Classify every image slot:

| Slot wants | Draw it with | Skill |
|---|---|---|
| hero subject, atmosphere, depth | shader field or point scene behind the DOM | `premium-web-webgl` |
| diagram, data figure, icon, pattern, annotated process | code-drawn SVG with real labels and values | `premium-web-svg` |
| soft background plate, grain, light field | `template/pipeline.py fallback <id>` (palette light field + vignette + grain) then `post` | this skill |
| scroll-scrubbed footage | a canvas or WebGL render exported frame-by-frame (headless capture), then `template/scrub.sh` | this skill + `premium-web-webgl` |
| photographic proof (a real product, a real person) | cannot be faked: leave an honest labelled placeholder and tell the user to supply it | none |

Tell the user in one line what was drawn instead of generated and how to upgrade later (register the MCP, rerun the pipeline).

## Failure behaviour (all rungs)

- A provider that returns no file, a quota message, or a login prompt = failed. Fall to the next rung; do not retry in a loop.
- Never adopt an image you did not name. Shared output folders can hold other agents' files; only take the path the tool reported.
- Keep the failed attempt in the manifest with the reason (`record_review verdict=cut`), so the next run does not repeat it.
