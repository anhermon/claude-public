# context-os hooks

Merge `settings-snippet.json` into your **Claude Code** project hooks (or user settings), and set:

```bash
export CONTEXT_OS_PLUGIN_ROOT="/absolute/path/to/context-os-plugin"
```

Replace the path with the directory containing this `hooks/` folder.

Hooks are **non-destructive**: they print hints to stderr. For automatic session nodes, set `CONTEXT_OS_SESSION_INGEST=1` and run `context-os ingest session` manually or from automation.
