#!/bin/bash
# Screenshot a page in Chrome (1440 + 390) AND real Mobile Safari (iOS Simulator), plus checks.
# Usage: shoot.sh <url-served-by-serve.mjs> <outdir> [selectors...]
#   selectors: CSS selectors to scroll to in the Simulator (via serve.mjs's ?sel= probe), e.g. "#features" "form".
#   Without selectors the Simulator takes SIM_STEPS (default 6) shots, one viewport height apart (?vh=).
# env: DEVICE="iPhone 17 Pro" (any name from `xcrun simctl list devices available`), WIDTHS=1440,390,
#      SIM=0 to skip the Simulator, CHROME=0 to skip Chrome, WAIT=7 seconds between openurl and screenshot.
# Shared machine: other agents may drive the same Simulator at the same time (their openurl lands in your shot).
# Default is therefore a PRIVATE throwaway device (created from DEVICE's type, deleted on exit). OWN=0 reuses the
# named shared device instead (faster, but check every shot is your page).
# The page MUST be served by scripts/serve.mjs: it stubs analytics (the Simulator can't block requests itself),
# sends no-store (Simulator Safari caches hard) and runs the scroll probe.
set -u
URL=${1:?url}; OUT=${2:?outdir}; shift 2
HERE=$(cd "$(dirname "$0")" && pwd)
mkdir -p "$OUT/chrome" "$OUT/safari"
rc=0
echo "page title: $(curl -s "${URL%%\?*}" | grep -o '<title>[^<]*' | cut -c8-)   <- check this is YOUR page (other agents run serve.mjs too)"
curl -s "${URL%%\?*}" | grep -q __analyticsBlocked || { echo "!! $URL is not served by serve.mjs (no probe): wrong port or someone else's server?"; exit 1; }

if [ "${CHROME:-1}" != 0 ]; then
  echo "== Chrome (${WIDTHS:-1440,390})"
  sep='?'; case "$URL" in *\?*) sep='&';; esac
  node "$HERE/chrome-shot.mjs" "${URL}${sep}noprobe" "$OUT/chrome" "${WIDTHS:-1440,390}" || rc=1
fi

if [ "${SIM:-1}" != 0 ]; then
  DEVICE=${DEVICE:-iPhone 17 Pro}
  if [ "${OWN:-1}" != 0 ]; then
    RT=$(xcrun simctl list runtimes available | grep -o 'com.apple.CoreSimulator.SimRuntime.iOS-[0-9-]*' | tail -1)
    D=$(xcrun simctl create "premium-web-$$" "$DEVICE" "$RT") || { echo "could not create a '$DEVICE' on $RT"; exit 1; }
    trap 'xcrun simctl shutdown "$D" 2>/dev/null; xcrun simctl delete "$D"' EXIT
    DEVICE="$DEVICE (private premium-web-$$)"
  else
    # Resolve the UDID by exact name (never hard-code it; names repeat across runtimes, take the first available).
    D=$(xcrun simctl list devices available | grep -F "    $DEVICE (" | head -1 | sed -E 's/.*\(([0-9A-F-]{36})\).*/\1/')
    if [ -z "$D" ]; then echo "no simulator named '$DEVICE'; see: xcrun simctl list devices available"; exit 1; fi
  fi
  echo "== Mobile Safari: $DEVICE ($D)"
  xcrun simctl boot "$D" 2>/dev/null || true          # already booted is fine
  xcrun simctl bootstatus "$D" -b >/dev/null
  open -a Simulator                                     # harmless if open; keeps the device window alive
  PORT=$(python3 -c 'import sys,urllib.parse;print(urllib.parse.urlparse(sys.argv[1]).port or 80)' "$URL")
  LOG=$(node -e 'console.log(require("path").join(require("os").tmpdir(), "premium-web-serve-" + process.argv[1] + ".jsonl"))' "$PORT"); : > "$LOG"   # serve.mjs writes here
  sep='?'; case "$URL" in *\?*) sep='&';; esac
  shot() { # name, extra query
    xcrun simctl openurl "$D" "${URL}${sep}r=$RANDOM$2"      # cache-bust every open
    sleep "${WAIT:-7}"                                         # load + fonts + probe scroll (d=600ms) + reveal

    xcrun simctl io "$D" screenshot --type=png "$OUT/safari/$1.png" >/dev/null 2>&1 && echo "   $OUT/safari/$1.png"
  }
  if [ "${OWN:-1}" != 0 ]; then  # fresh device: first Safari launch shows tips + a system notification; burn it off
    xcrun simctl openurl "$D" "${URL}${sep}warmup=1"; sleep 12
    xcrun simctl terminate "$D" com.apple.mobilesafari 2>/dev/null; sleep 1
  fi
  shot 00-top ""
  if [ $# -gt 0 ]; then
    i=1; for sel in "$@"; do
      enc=$(python3 -c 'import sys,urllib.parse;print(urllib.parse.quote(sys.argv[1]))' "$sel")
      shot "$(printf %02d $i)-$(echo "$sel" | tr -dc 'a-zA-Z0-9-')" "&sel=$enc&off=-16"; i=$((i+1))
    done
  else
    for i in $(seq 1 "${SIM_STEPS:-6}"); do shot "$(printf %02d $i)-vh$i" "&vh=$(python3 -c "print($i*0.85)")"; done
  fi
  echo "   probe reports (one per shot): w, scrollWidth, fonts, errors"
  python3 - "$LOG" <<'EOF' || true
import json, sys
for line in open(sys.argv[1]):
    try: d = json.loads(line)
    except Exception: continue
    bad = [f for f in d["fonts"] if f.endswith(" error")]
    flag = "PROBLEM" if d["sw"] > d["w"] or d["errs"] or bad else "ok"
    print(f"   {flag} w={d['w']} sw={d['sw']} y={d['y']} rm={d['rm']} dark={d['dark']} fonts={sorted(set(d['fonts']))[:4]} errs={d['errs'][:3]} wide={d['wide'][:3]}")
EOF
  python3 -c "import json,sys;l=[json.loads(x) for x in open(sys.argv[1]) if x.strip()];sys.exit(any(d['sw']>d['w'] or d['errs'] for d in l))" "$LOG" || rc=1
  echo "   UA (frozen by Safari, do not trust the iOS version in it): $(head -1 "$LOG" | python3 -c 'import json,sys;print(json.loads(sys.stdin.read() or "{}").get("ua","?")[:80])' 2>/dev/null)"
fi
echo "Done. Now Read every PNG in $OUT — a passing build is not a passing render."
exit $rc
