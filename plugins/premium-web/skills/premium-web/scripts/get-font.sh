#!/bin/bash
# Download a self-hosted latin woff2 subset of an open-licence font from Fontsource (no runtime CDN).
# Usage: get-font.sh <fontsource-id> <outdir> [weights=400,700]   e.g. get-font.sh fraunces fonts
#   Variable fonts: fetches latin-wght-normal.woff2 (+ italic if it exists) and ignores weights.
#   AXES=full fetches every axis (opsz, SOFT, WONK, ...) instead of wght only: larger file, more voice.
#   Prints the licence and an @font-face block to paste. Refuses non-OFL/Apache/MIT licences.
set -eu
ID=${1:?fontsource id, e.g. space-grotesk}; OUT=${2:?outdir}; W=${3:-400,700}
mkdir -p "$OUT"
META=$(curl -fsS --max-time 30 "https://api.fontsource.org/v1/fonts/$ID") || { echo "unknown font id: $ID (see https://fontsource.org)"; exit 1; }
read -r FAMILY LIC VAR < <(python3 -c 'import json,sys;d=json.loads(sys.argv[1]);print(d["family"].replace(" ","_"),d["license"],bool(d["variable"]))' "$META")
FAMILY=${FAMILY//_/ }
case "$LIC" in OFL*|Apache*|MIT*) ;; *) echo "licence $LIC: not open, pick another font"; exit 1;; esac
BASE="https://cdn.jsdelivr.net/fontsource/fonts/$ID"
if [ "$VAR" = True ]; then
  for st in normal italic; do
    ax=${AXES:-wght}; f="$OUT/$ID-latin-$ax-$st.woff2"
    if curl -fsS --max-time 30 -o "$f" "$BASE:vf@latest/latin-$ax-$st.woff2" 2>/dev/null; then
      printf '@font-face { font-family: "%s"; src: url("%s") format("woff2"); font-weight: 100 900; font-style: %s; font-display: swap; }\n' "$FAMILY" "$(basename "$f")" "$st"
    else rm -f "$f"; fi
  done
else
  for w in ${W//,/ }; do
    f="$OUT/$ID-latin-$w-normal.woff2"
    curl -fsS --max-time 30 -o "$f" "$BASE@latest/latin-$w-normal.woff2" || { rm -f "$f"; echo "/* no weight $w */"; continue; }
    printf '@font-face { font-family: "%s"; src: url("%s") format("woff2"); font-weight: %s; font-display: swap; }\n' "$FAMILY" "$(basename "$f")" "$w"
  done
fi
echo "/* $FAMILY, licence $LIC (Fontsource). Keep a licence note next to the files. */" >&2
ls -la "$OUT" | grep "$ID" >&2
