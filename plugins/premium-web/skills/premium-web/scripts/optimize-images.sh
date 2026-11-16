#!/bin/bash
# Source PNG -> responsive AVIF + WebP set (Pillow, via the imagegen core). Never upscales.
# Usage: optimize-images.sh <src.png> <outdir> [name] [widths=640,1024,1536] [budgetKB]
#   e.g. optimize-images.sh src/hero.png site/img hero 640,960,1536 180
# Crops: call the core directly: python3 <skill>/mcp/imagegen/core.py optimise src.png --crop left,top,w,h ...
set -eu
HERE=$(cd "$(dirname "$0")/.." && pwd)
SRC=${1:?src}; OUT=${2:?outdir}; NAME=${3:-}; W=${4:-640,1024,1536}; B=${5:-}
args=(optimise "$SRC" --out-dir "$OUT" --widths "$W"); [ -n "$NAME" ] && args+=(--name "$NAME"); [ -n "$B" ] && args+=(--budget-kb "$B")
if python3 -c "from PIL import features; assert features.check('avif')" 2>/dev/null; then
  python3 "$HERE/mcp/imagegen/core.py" "${args[@]}"
else  # Pillow without AVIF (or missing): run in a throwaway uv env with a pinned wheel that has it
  uv run --with pillow==12.3.0 python "$HERE/mcp/imagegen/core.py" "${args[@]}"
fi
