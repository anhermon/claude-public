#!/bin/bash
# CLI front for the imagegen MCP core (same code path as the MCP tools).
#   gen-image.sh providers
#   gen-image.sh art "brief that says what the image must communicate" --slot hero --style-preset dark-studio
#   gen-image.sh gen "brief" --aspect 3:2 --style-preset dark-studio --name hero --out-dir src-img [--variants 2] [--provider codex]
#   gen-image.sh compare src-img/*.png --aspect 3:2      # contact sheet + near-duplicate/aspect checks
#   gen-image.sh review src-img/hero-xxxx.png cut --note "does not explain the section"
# Names are idempotent (<name>-<hash>.png): re-running never regenerates; delete the file to force a new one.
set -eu
HERE=$(cd "$(dirname "$0")/.." && pwd)
if python3 -c "import PIL" 2>/dev/null; then exec python3 "$HERE/mcp/imagegen/core.py" "$@"; fi
exec uv run --with pillow==12.3.0 python "$HERE/mcp/imagegen/core.py" "$@"
