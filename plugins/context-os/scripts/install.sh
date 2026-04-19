#!/usr/bin/env bash
# Install the context-os CLI globally (Python entry point).
# Prefers: uv tool install  >  pip install -e  >  symlink bin/context-os
set -euo pipefail
PLUGIN_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PLUGIN_ROOT"

if command -v uv >/dev/null 2>&1; then
  echo "Installing with uv tool install ."
  uv tool install . --force
  echo "Done. Ensure your uv tool bin directory is on PATH (uv typically prints it after install)."
elif command -v pip3 >/dev/null 2>&1; then
  echo "Installing with pip install -e ."
  python3 -m pip install -e "$PLUGIN_ROOT"
  echo "Done. Ensure the pip user bin directory is on PATH if needed."
else
  TARGET="${1:-$HOME/.local/bin}"
  mkdir -p "$TARGET"
  ln -sf "$PLUGIN_ROOT/bin/context-os" "$TARGET/context-os"
  echo "Linked: $TARGET/context-os -> $PLUGIN_ROOT/bin/context-os"
  echo 'Add to PATH: export PATH="$HOME/.local/bin:$PATH"'
fi
