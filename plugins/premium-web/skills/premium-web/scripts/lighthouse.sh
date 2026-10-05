#!/bin/bash
# Lighthouse mobile + desktop against a LOCAL url, trackers blocked. Usage: lighthouse.sh <url> <outdir> [runs=1]
# First run downloads lighthouse via npx (needs network). Scores on localhost: trust a11y/SEO/BP and CLS fully;
# treat perf as relative (no CDN, no HTTP/2, local disk). Mobile perf varies run to run: use runs=3, read the median.
set -u
URL=${1:?url}; OUT=${2:?outdir}; RUNS=${3:-1}; mkdir -p "$OUT"
export CHROME_PATH=${CHROME_PATH:-"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"}
BLOCK=(--blocked-url-patterns='*posthog*' --blocked-url-patterns='*googletagmanager*' --blocked-url-patterns='*google-analytics*' --blocked-url-patterns='*plausible.io*')
run() { npx -y lighthouse@12 "$URL" --quiet --chrome-flags="--headless=new" "${BLOCK[@]}" $2 \
  --only-categories=performance,accessibility,best-practices,seo --output=json --output-path="$OUT/$1.json" >/dev/null 2>&1 \
  || echo "lighthouse failed for $1"; }
for i in $(seq 1 "$RUNS"); do run "mobile-$i" ""; done
run desktop "--preset=desktop"
node -e '
const fs=require("fs"),d=process.argv[1];
for (const f of fs.readdirSync(d).filter(f=>f.endsWith(".json")).sort()) {
  const r=JSON.parse(fs.readFileSync(d+"/"+f)),c=r.categories,a=r.audits;
  const fails=Object.values(a).filter(x=>x.score!==null&&x.score<0.9&&x.scoreDisplayMode==="binary").map(x=>x.id);
  console.log(f.padEnd(14),["performance","accessibility","best-practices","seo"].map(k=>Math.round(c[k].score*100)).join("/"),
    "LCP",a["largest-contentful-paint"].displayValue,"CLS",a["cumulative-layout-shift"].displayValue,"TBT",a["total-blocking-time"].displayValue,
    "weight",a["total-byte-weight"].displayValue, fails.length?"FAILING: "+fails.join(","):"");
}' "$OUT"
