# claude-public

Public Claude Code plugins, installed from this repo as a marketplace.

```bash
claude plugin marketplace add anhermon/claude-public
claude plugin install <plugin>@claude-public
```

## Plugins

| Plugin | Version | Category | What it does |
|---|---|---|---|
| [premium-web](plugins/premium-web) | 2.1.0 | design | Build premium, studio-quality web pages and tool UIs (app mode) as several candidates (default 3) you browse and pick from in a Claude Code mod pane (needs Claude Code 2.1.287+), then finish the winner: section rubric, mandatory signature "wow" moment, calibrated critic loop, optional image generation. |
| [llm-wiki](plugins/llm-wiki) | 1.1.0 | productivity | Maintain a markdown wiki: ingest sources, query with citations, lint for drift, publish as HTML (`kb-to-wiki`). |
| [research](plugins/research) | 1.0.0 | research | Research a topic as a fast web-backed brief, or drive an AutoResearchClaw run that ends in a paper. |
| [agent-repo-search](plugins/agent-repo-search) | 0.1.0 | development | Ingest a large repo with `rendergit` and read only the index and the chunks you need. |
| [context-os](plugins/context-os) | 2.2.0 | development | Session and token analytics (cc-lens, ccusage), token-efficiency playbook, local knowledge graph. |
| [skill-creator-plus](plugins/skill-creator-plus) | 0.2.0 | development | Anthropic's skill-creator (claude.ai version) plus per-stage timing and a duration waterfall in evals; resyncs from upstream. |

## What belongs here

A plugin stays only if it meets all four:

1. No official or built-in Claude Code equivalent.
2. Works on a clean machine, with no personal paths, ports or private project names.
3. Has a README with an install line and an example.
4. Has tests or evals.

`research`, `llm-wiki`, `agent-repo-search` and `context-os` are on probation against item 4 and are tracked as follow-ups.

## Removed

Removed 2026-11-16 because each is redundant with a built-in or official plugin, or only works on one machine's stack. Never installed or invoked from this repo.

| Removed | Use instead |
|---|---|
| commit | official `commit-commands` plugin |
| code-review | built-in `/code-review`; official `code-review` and `pr-review-toolkit` |
| review-agents | official `pr-review-toolkit` and `code-review` |
| search | built-in Grep/Glob and Explore agent; official `*-lsp` plugins |
| memory | built-in auto-memory (`MEMORY.md`); official `claude-md-management` |
| pm | the BMAD-METHOD project itself; official `feature-dev` |
| dev-guidelines | none (guidance prose); official `plugin-dev` / `feature-dev` for plugin work |
| setup-telemetry | built-in OpenTelemetry export; official `session-report`; Langfuse's own Claude Code integration |
| image-gen | none official; hard-coded to one machine's paths |
| observability | none official; only worked against one private Grafana/Loki stack |

Old versions remain available in git history.

## Validate

```bash
sh scripts/validate.sh
```

Runs `claude plugin validate` on the marketplace and every plugin and checks categories and versions agree. GitHub Actions is not used on this repo; run it locally.

## Contributing

See [CONTRIBUTING.md](./CONTRIBUTING.md). Code of conduct: [CODE_OF_CONDUCT.md](./CODE_OF_CONDUCT.md). License: MIT.
