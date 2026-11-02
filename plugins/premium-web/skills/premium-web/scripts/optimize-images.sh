#!/bin/bash
# Source PNG -> responsive AVIF + WebP set (Pillow, via the premium-web-imagery core). Never upscales.
# Usage: optimize-images.sh <src.png> <outdir> [name] [widths=640,1024,1536] [budgetKB]
#   e.g. optimize-images.sh src/hero.png site/img hero 640,960,1536 180
# The implementation lives in the sibling skill (skills/premium-web-imagery/mcp/imagegen/core.py); override with IMAGEGEN_CORE.
set -eu
HERE=$(cd "$(dirname "$0")/.." && pwd)
CORE=${IMAGEGEN_CORE:-"$HERE/../premium-web-imagery/mcp/imagegen/core.py"}
[ -f "$CORE" ] || { echo "imagegen core not found at $CORE (install the premium-web-imagery skill or set IMAGEGEN_CORE)"; exit 1; }
SRC=${1:?src}; OUT=${2:?outdir}; NAME=${3:-}; W=${4:-640,1024,1536}; B=${5:-}
args=(optimise "$SRC" --out-dir "$OUT" --widths "$W"); [ -n "$NAME" ] && args+=(--name "$NAME"); [ -n "$B" ] && args+=(--budget-kb "$B")
if python3 -c "from PIL import features; assert features.check('avif')" 2>/dev/null; then
  python3 "$CORE" "${args[@]}"
else  # Pillow without AVIF (or missing): run in a throwaway uv env with a pinned wheel that has it
  uv run --with pillow==12.3.0 python "$CORE" "${args[@]}"
fi
