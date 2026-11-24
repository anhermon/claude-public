#!/bin/bash
# Live DOM check of the tells.js app profile and the marketing profile on real pages (needs Chrome; prints SKIP when absent).
#   scripts/test_app_live.sh        fixtures/app-good.html must pass app mode; fixtures/app-bad.html and the marketing skeleton must hit page_shaped_mismatch etc.;
#                                   the skeleton must still fail marketing mode exactly as before (scale_change craft_fail, templaty).
set -eu
HERE=$(cd "$(dirname "$0")" && pwd); SK="$HERE/../assets/skeleton/index.html"; FX="$HERE/fixtures"
[ -x "${CHROME_PATH:-/Applications/Google Chrome.app/Contents/MacOS/Google Chrome}" ] || { echo "SKIP: Chrome not found (set CHROME_PATH)"; exit 0; }
T=$(mktemp -d); mkdir -p "$T/a" "$T/m"
printf '## Step 0 classification\nmode: app\nclassification: WORK\nusers: on-call engineers\nfrequency: daily, 30 opens each\nevidence: they find, compare and trigger deploys\ndensity_target: 20 rows\nprimary_tasks:\n- find last night deploy\n' > "$T/a/NOTES.md"
printf '## Step 0 classification\nmode: marketing\nclassification: READ\nusers: prospects from search\nfrequency: first visit\nevidence: the page sells the product; nobody operates it\n' > "$T/m/NOTES.md"
scan() { # mode notes-dir file -> JSON eval on stdout
  MODE=$1 PW_NOTES=$2/NOTES.md EVAL="$HERE/tells.js" SHOTS=0 node "$HERE/chrome-shot.mjs" "file://$3" "$T/o$$_$RANDOM" 1440 >/dev/null 2>&1 || true
  python3 -c 'import json,sys,glob,os; d=sorted(glob.glob(sys.argv[1]+"/o*"),key=os.path.getmtime)[-1]; print(json.dumps(list(json.load(open(d+"/report.json")).values())[0]["eval"]))' "$T"
}
check() { python3 -c "import json,sys; e=json.loads(sys.argv[1]); $1" "$2"; }
good=$(scan app "$T/a" "$FX/app-good.html"); check 'assert e["mode"]=="app" and e["craft_fail"]==[], e["craft_fail"]; assert e["tells"]["density"]["measured"]>=20 and e["tells"]["state_coverage"]["missing"]==[]' "$good"
bad=$(scan tool "$T/a" "$FX/app-bad.html");  check 'assert e["mode"]=="app"; c=e["craft_fail"]; [ (_ for _ in ()).throw(AssertionError(k)) for k in ("density","interactive_affordance","state_coverage","page_shaped_mismatch","data_wow_in_app") if k not in c ]' "$bad"
sk=$(scan app "$T/a" "$SK");                 check 'assert "page_shaped_mismatch" in e["craft_fail"] and "WRONG-MODE" in e["tells"]["page_shaped_mismatch"]["reason"], e["craft_fail"]' "$sk"
mk=$(scan marketing "$T/m" "$SK");           check 'assert e["mode"]=="marketing" and e["craft_fail"]==["scale_change"] and e["templaty"] and "density" not in e["tells"], (e["craft_fail"],)' "$mk"
echo "test_app_live ok"
