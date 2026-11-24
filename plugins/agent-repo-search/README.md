# Agent Repo Search Plugin

A Claude plugin for efficiently searching and ingesting large codebases using structural indexing and CXML chunking.

## Features
- Structural indexing of repository paths.
- Token-aware CXML chunking.
- Strategic probing for on-the-fly semantic understanding.

## Usage
This plugin fetches [`rendergit`](https://github.com/karpathy/rendergit) (Andrej Karpathy, 0BSD) from upstream at a pinned commit at run time — see `skills/agent-repo-search/SKILL.md` — rather than vendoring a copy.

## Install and example

```bash
claude plugin marketplace add anhermon/claude-public
claude plugin install agent-repo-search@claude-public
```

Example: "ingest https://github.com/karpathy/rendergit and tell me how the HTML is generated". The skill runs `rendergit` into `repo_context/`, reads `index.txt`, then loads only the relevant `.cxml` chunks.

Requirements: `curl`, `uv`, Python 3.10+, network access to GitHub.
