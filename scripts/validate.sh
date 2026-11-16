#!/bin/sh
# Validate the marketplace and every plugin; exit non-zero on any failure.
set -u
cd "$(dirname "$0")/.." || exit 1
fail=0
check() {
  if claude plugin validate "$1"; then :; else echo "FAIL: $1"; fail=1; fi
}
check .claude-plugin/marketplace.json
for d in plugins/*/; do check "${d%/}"; done
# every marketplace entry needs a matching plugin dir, a category, and a version equal to plugin.json
python3 - <<'PY' || fail=1
import json, sys
m = json.load(open(".claude-plugin/marketplace.json"))
bad = 0
for p in m["plugins"]:
    v = json.load(open("plugins/%s/.claude-plugin/plugin.json" % p["name"])).get("version")
    if not p.get("category"):
        print("no category:", p["name"]); bad = 1
    if v != p.get("version"):
        print("version mismatch:", p["name"], p.get("version"), v); bad = 1
sys.exit(bad)
PY
[ "$fail" -eq 0 ] && echo "validate: OK" || echo "validate: FAILED"
exit "$fail"
