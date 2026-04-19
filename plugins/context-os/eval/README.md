# context-os eval (quickstart harness)

Run from the **plugin root** (directory containing `eval/` and `bin/`):

```bash
cd /path/to/claude-public/plugins/context-os
python3 eval/eval_quickstart.py
```

Optional: set `PLUGIN_ROOT` if your cwd differs:

```bash
PLUGIN_ROOT=/path/to/context-os-plugin python3 /path/to/context-os-plugin/eval/eval_quickstart.py
```

The CLI package lives under `context_os/`; after `uv tool install .` or `pip install -e .`, use `context-os` or `python3 -m context_os` from anywhere.

Results are written under `eval/` per the script’s `output_path`.
