# Agent Repo Search Plugin

A Claude plugin for efficiently searching and ingesting large codebases using structural indexing and CXML chunking.

## Features
- Structural indexing of repository paths.
- Token-aware CXML chunking.
- Strategic probing for on-the-fly semantic understanding.

## Usage
This plugin fetches [`rendergit`](https://github.com/karpathy/rendergit) (Andrej Karpathy, 0BSD) from upstream at run time — see `skills/agent-repo-search/SKILL.md` — rather than vendoring a copy, so it always uses the latest version.
