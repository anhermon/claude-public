# research plugin

Two ways to research a topic from Claude Code.

- **Regular research** (`regular-research`): web search plus Claude's own knowledge, returned as a structured brief (TL;DR, key findings, landscape, recommendation, caveats, sources).
- **AutoResearchClaw** (`researchclaw`): drives a local checkout of [AutoResearchClaw](https://github.com/aiming-lab/AutoResearchClaw), a 23-stage pipeline that produces a paper. Not vendored; the skill clones it into `$RESEARCHCLAW_DIR` (default `~/AutoResearchClaw`).

## Install

```bash
claude plugin marketplace add anhermon/claude-public
claude plugin install research@claude-public
```

## Use it when

You want a quick sourced brief on a topic (regular), or a long autonomous run that ends in a paper with citations (AutoResearchClaw). The `research` skill asks which mode to use.

## Example

> research "state of local LLM inference on Apple silicon"

Choose mode 2 and you get a brief in the format above in about half a minute.

## Requirements

- Regular research: a web-search tool is recommended.
- AutoResearchClaw: `git`, Python 3 with `venv`, and whatever LLM backend AutoResearchClaw's config needs. Pipeline gates (stages 5, 9, 20) pause for `researchclaw approve` / `reject`.
