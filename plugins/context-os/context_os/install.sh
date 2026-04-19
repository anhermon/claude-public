#!/usr/bin/env bash
# Symlink bundled context-os CLI into ~/.local/bin (or TARGET dir).
set -euo pipefail
PLUGIN_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TARGET="${1:-$HOME/.local/bin}"
mkdir -p "$TARGET"
ln -sf "$PLUGIN_ROOT/bin/context-os" "$TARGET/context-os"
echo "Linked: $TARGET/context-os -> $PLUGIN_ROOT/bin/context-os"
echo 'Ensure ~/.local/bin is on PATH, e.g.: export PATH="$HOME/.local/bin:$PATH"'
