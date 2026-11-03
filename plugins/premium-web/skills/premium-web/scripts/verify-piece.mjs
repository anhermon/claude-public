#!/usr/bin/env node
// verify-piece.mjs: every MECHANICAL gate of a finished page in one headless command, compact output.
//   node verify-piece.mjs <piece-dir> [--url URL] [--fast] [--no-lighthouse] [--only 390|1440] [--selftest] [--help]
// Serves <piece-dir> (scripts/serve.mjs) unless --url. Reuses chrome-shot.mjs (console errors, overflow, fonts, tells.js),
// saturation.py, lighthouse.sh. Adds: stepped-scroll per-section stills with settle, void/collision/tap/min-font checks, scroll fps.
// Writes <piece-dir>/.verify/{report.json, sections/<nn-id>/{1440,390}.png, chrome/report.json, lh/}. Stdout stays <= ~40 lines and never
// contains images or logs: open ONLY the stills listed under "failing sections".
// Optional <piece-dir>/piece.json "verify": { "sections": CSS, "subject": CSS of the persistent subject, "subjectBox": JS expression
//   returning {x,y,w,h} in viewport px (needed when the subject is a full-viewport canvas), "ignore": CSS of text allowed over the subject }.
// Exit: 0 all hard gates pass, 1 a hard gate failed, 2 usage / infrastructure error.
import { spawn, spawnSync } from "node:child_process";
import fs from "node:fs";
import net from "node:net";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { open, sleep } from "./lib/cdp.mjs";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const VIEWPORTS = [{ w: 1440, h: 900, mobile: false }, { w: 390, h: 844, mobile: true }];
const DEFAULT_SECTIONS = "main > section, footer", OUT_DIR = ".verify", SERVE_BOOT_MS = 8000;
const BOOT_WAIT_MS = 2500, SCROLL_STEPS = 6, SCROLL_STEP_MS = 40, NAV_MAX_PX = 200;
const MIN_FONT_PX = 12, TAP_HARD_PX = 24, TAP_WARN_PX = 44, VOID_MAX_FRAC = 0.35, NAV_CLIP_FRAC = 0.08, NAV_TOP_MAX_PX = 120, NAV_MIN_WIDTH_FRAC = 0.5, COLLIDE_MAX_FRAC = 0.2, TEXT_MIN_OPACITY = 0.1;
const FPS_THROTTLE = 4, FPS_SCROLL_MS = 6000, LONG_FRAME_MS = 50, FPS_P95_WARN_MS = 50;
const LH_HARD_MIN = 80, LH_WARN_MIN = 90, LH_PERF_WARN = 85, MAX_LIST = 3, SUMMARY_MAX_LINES = 40;

const HELP = `usage: node verify-piece.mjs <piece-dir> [--url URL] [--fast] [--no-lighthouse] [--only 390|1440] [--selftest]
  --fast            skip Lighthouse and the fps measurement
  --selftest        no Chrome: checks the summary/gating logic on a synthetic report, then exits
env: CHROME_PATH, CHROME_FLAGS (e.g. --use-angle=metal for WebGL), PORT`;

// ---- in-page probes (strings, evaluated per section / once) -------------------------------------------------------------
const PAGE_HELPERS = `
const visible = (e) => { const r = e.getBoundingClientRect(), s = getComputedStyle(e); return r.width > 1 && r.height > 1 && s.visibility !== 'hidden' && s.display !== 'none' && +s.opacity > ${TEXT_MIN_OPACITY}; };
const ownText = (e) => [...e.childNodes].some((n) => n.nodeType === 3 && n.textContent.trim().length > 1);
const clipV = (r) => ({ x: r.left, y: Math.max(0, r.top), w: r.width, h: Math.min(innerHeight, r.bottom) - Math.max(0, r.top) });`;
const SECTION_PROBE = (secSel, idx, subjSel, boxExpr, ignoreSel) => `(() => { ${PAGE_HELPERS}
  const sec = document.querySelectorAll(${JSON.stringify(secSel)})[${idx}]; const sr = sec.getBoundingClientRect();
  const slice = { top: Math.max(0, sr.top), bottom: Math.min(innerHeight, sr.bottom) }; const vh = Math.max(1, slice.bottom - slice.top);
  let box = null; try { box = ${boxExpr ? `(${boxExpr})` : "null"}; } catch (e) {}
  if (!box && ${JSON.stringify(subjSel)}) { const s = document.querySelector(${JSON.stringify(subjSel)}); if (s && visible(s)) { const r = s.getBoundingClientRect(); if (r.width * r.height < innerWidth * innerHeight * 0.9) box = { x: r.left, y: r.top, w: r.width, h: r.height }; } }
  const texts = [...sec.querySelectorAll('*')].filter((e) => ownText(e) && visible(e) && !(${JSON.stringify(ignoreSel)} && e.closest(${JSON.stringify(ignoreSel)}))).map((e) => ({ e, r: clipV(e.getBoundingClientRect()) })).filter((t) => t.r.h > 0 && t.r.y < slice.bottom && t.r.y + t.r.h > slice.top);
  const media = [...sec.querySelectorAll('img, svg, video, picture, input, button, [data-wow]')].filter(visible).map((e) => clipV(e.getBoundingClientRect())).filter((r) => r.h > 0);
  const spans = texts.map((t) => t.r).concat(media).map((r) => [Math.max(slice.top, r.y), Math.min(slice.bottom, r.y + r.h)]);
  if (box) { const b = clipV({ left: box.x, top: box.y, bottom: box.y + box.h, width: box.w }); if (b.h > 0) spans.push([Math.max(slice.top, b.y), Math.min(slice.bottom, b.y + b.h)]); }
  spans.sort((a, b) => a[0] - b[0]); let cur = slice.top, gap = 0; for (const [a, b] of spans) { if (a > cur) gap = Math.max(gap, a - cur); cur = Math.max(cur, b); } gap = Math.max(gap, slice.bottom - cur);
  const hits = box ? texts.map((t) => { const ix = Math.max(0, Math.min(t.r.x + t.r.w, box.x + box.w) - Math.max(t.r.x, box.x)), iy = Math.max(0, Math.min(t.r.y + t.r.h, box.y + box.h) - Math.max(t.r.y, box.y)); return { t: t.e.textContent.trim().slice(0, 30), f: +(ix * iy / (t.r.w * t.r.h)).toFixed(2) }; }).filter((h) => h.f > ${COLLIDE_MAX_FRAC}) : null;
  let navClip = 0; if (box) { const navs = [...document.querySelectorAll('body *')].filter((e) => { const c = getComputedStyle(e), r = e.getBoundingClientRect(); return (c.position === 'fixed' || c.position === 'sticky') && r.top >= 0 && r.top <= ${NAV_TOP_MAX_PX} && r.height <= ${NAV_MAX_PX} && r.width >= innerWidth * ${NAV_MIN_WIDTH_FRAC} && e.matches('header, nav, [role=banner], header *, nav *'); });
    for (const n of navs) { const r = n.getBoundingClientRect(); const ix = Math.max(0, Math.min(r.right, box.x + box.w) - Math.max(r.left, box.x)), iy = Math.max(0, Math.min(r.bottom, box.y + box.h) - Math.max(r.top, box.y)); navClip = Math.max(navClip, ix * iy / (box.w * box.h)); } }
  return { gapFrac: +(gap / vh).toFixed(2), subjectBox: !!box, collisions: hits, navClip: +navClip.toFixed(2), texts: texts.length }; })()`;
const MOBILE_PROBE = `(() => { ${PAGE_HELPERS}
  const tap = [...document.querySelectorAll('a[href], button, input:not([type=hidden]), select, textarea, summary, [role=button]')].filter((e) => visible(e) && getComputedStyle(e).display !== 'inline').map((e) => { const r = e.getBoundingClientRect(); return { n: (e.tagName + '.' + String(e.className).split(' ')[0]).slice(0, 30) + ' "' + (e.textContent || e.ariaLabel || '').trim().slice(0, 14) + '"', m: Math.round(Math.min(r.width, r.height)) }; });
  const fonts = new Map(); document.querySelectorAll('body *').forEach((e) => { if (!ownText(e) || !visible(e)) return; const f = parseFloat(getComputedStyle(e).fontSize); if (f < ${MIN_FONT_PX}) fonts.set(e.tagName + '.' + String(e.className).split(' ')[0] + ' ' + f + 'px', 1); });
  return { tapHard: tap.filter((t) => t.m < ${TAP_HARD_PX}), tapWarn: tap.filter((t) => t.m >= ${TAP_HARD_PX} && t.m < ${TAP_WARN_PX}).length, tapTotal: tap.length, smallFonts: [...fonts.keys()] }; })()`;
const FPS_PROBE = `new Promise((done) => { const d = []; let last = performance.now(), t0 = last; const H = Math.max(0, document.documentElement.scrollHeight - innerHeight);
  document.documentElement.style.scrollBehavior = 'auto';
  (function f(now) { d.push(now - last); last = now; const p = Math.min(1, (now - t0) / ${FPS_SCROLL_MS}); scrollTo(0, H * p); if (p < 1) requestAnimationFrame(f); else { d.shift(); d.sort((a, b) => a - b); const q = (x) => d[Math.min(d.length - 1, Math.floor(d.length * x))];
    done({ frames: d.length, p50: +q(0.5).toFixed(1), p95: +q(0.95).toFixed(1), longPct: +(100 * d.filter((x) => x > ${LONG_FRAME_MS}).length / d.length).toFixed(1) }); } })(performance.now()); })`;

// ---- pure helpers (selftest-covered) --------------------------------------------------------------------------------
export function gate(report) { // -> { hard: [..], soft: [..] } from a populated report
  const hard = [], soft = [];
  for (const [vp, v] of Object.entries(report.viewports || {})) {
    (v.problems || []).slice(0, MAX_LIST).forEach((p) => hard.push(`${vp}: ${p}`));
    if (v.tapHard?.length) hard.push(`${vp}: ${v.tapHard.length} tap targets < ${TAP_HARD_PX}px e.g. ${v.tapHard.slice(0, MAX_LIST).map((t) => t.n + " " + t.m + "px").join("; ")}`);
    if (v.smallFonts?.length) hard.push(`${vp}: text < ${MIN_FONT_PX}px: ${v.smallFonts.slice(0, MAX_LIST).join("; ")}`);
    if (v.tapWarn) soft.push(`${vp}: ${v.tapWarn} tap targets between ${TAP_HARD_PX} and ${TAP_WARN_PX}px`);
    for (const s of v.sections || []) {
      if (s.collisions?.length) hard.push(`${vp} ${s.id}: subject overlaps text ${s.collisions.slice(0, MAX_LIST).map((c) => `"${c.t}" ${c.f}`).join(", ")}`);
      if (s.navClip > NAV_CLIP_FRAC) hard.push(`${vp} ${s.id}: subject clipped by the nav (${Math.round(s.navClip * 100)}% of its box)`);
      if (s.gapFrac > VOID_MAX_FRAC) soft.push(`${vp} ${s.id}: empty band ${Math.round(s.gapFrac * 100)}% of the viewport (void)`);
    }
    const unsettled = (v.sections || []).filter((s) => !s.settled).length; if (unsettled) soft.push(`${vp}: ${unsettled} stills never pixel-settled (live canvas animates): each is one frame, judge mid-motion with care`);
    if (v.fps && v.fps.p95 > FPS_P95_WARN_MS) soft.push(`${vp}: scroll p95 frame ${v.fps.p95}ms, ${v.fps.longPct}% > ${LONG_FRAME_MS}ms (4x CPU throttle, headless: relative signal)`);
  }
  if (report.tells?.templaty) soft.push(`tells: templaty (${report.tells.hits.join(", ")})`);
  if (report.tells?.craft_fail?.length) hard.push(`tells craft gate: ${report.tells.craft_fail.join(", ")}`);
  const sat = report.saturation; if (sat?.toy || sat?.pageFail) soft.push(`saturation: ${sat.toy} TOY frames, page mean ${sat.mean}`);
  for (const [k, c] of Object.entries(report.lighthouse || {})) {
    for (const cat of ["accessibility", "best-practices", "seo"]) { if (c[cat] < LH_HARD_MIN) hard.push(`lighthouse ${k} ${cat} ${c[cat]} < ${LH_HARD_MIN}`); else if (c[cat] < LH_WARN_MIN) soft.push(`lighthouse ${k} ${cat} ${c[cat]}`); }
    if (c.performance < LH_PERF_WARN) soft.push(`lighthouse ${k} performance ${c.performance} (localhost: relative)`);
  }
  return { hard, soft };
}
export function failingSections(report) {
  const ids = new Set();
  for (const v of Object.values(report.viewports || {})) for (const s of v.sections || []) if (s.collisions?.length || s.navClip > NAV_CLIP_FRAC || s.gapFrac > VOID_MAX_FRAC) ids.add(s.id);
  return [...ids].sort();
}
function selftest() {
  const r = { viewports: { 390: { problems: ["console.error: x"], tapHard: [{ n: "button.x", m: 10 }], smallFonts: ["P.a 9px"], sections: [{ id: "01-b", gapFrac: 0.6, collisions: [], settled: true }, { id: "02-c", gapFrac: 0.1, collisions: [{ t: "Hi", f: 0.5 }], settled: false }] } }, lighthouse: { mobile: { accessibility: 70, "best-practices": 100, seo: 100, performance: 60 } } };
  const g = gate(r), f = failingSections(r);
  const ok = g.hard.length === 5 && g.soft.length === 3 && f.join() === "01-b,02-c" && gate({}).hard.length === 0;
  console.log(ok ? "selftest ok" : "selftest FAILED " + JSON.stringify({ g, f })); process.exit(ok ? 0 : 1);
}

// ---- orchestration ------------------------------------------------------------------------------------------------------
const freePort = () => new Promise((res) => { const s = net.createServer().listen(0, () => { const { port } = s.address(); s.close(() => res(port)); }); });
async function startServer(dir) {
  const p = spawn("node", [path.join(HERE, "serve.mjs"), dir, process.env.PORT || String(await freePort())], { stdio: ["ignore", "pipe", "inherit"] });
  const url = await new Promise((res, rej) => { const t = setTimeout(() => rej(new Error("serve.mjs did not start")), SERVE_BOOT_MS); p.stdout.on("data", (d) => { const m = /on (http:\/\/localhost:\d+)/.exec(String(d)); if (m) { clearTimeout(t); res(m[1]); } }); });
  return { url: url + "/index.html", stop: () => p.kill() };
}
const withQuery = (u, q) => u + (u.includes("?") ? "&" : "?") + q;

async function main(argv) {
  if (argv.includes("--help") || argv.includes("-h")) { console.log(HELP); return 0; }
  if (argv.includes("--selftest")) return selftest();
  const flag = (n) => argv.includes(n), val = (n) => (argv.includes(n) ? argv[argv.indexOf(n) + 1] : undefined);
  const dir = path.resolve(argv.find((a, i) => !a.startsWith("--") && !["--url", "--only"].includes(argv[i - 1]) ) || "");
  if (!fs.existsSync(dir)) { console.error(HELP); return 2; }
  const fast = flag("--fast"), out = path.join(dir, OUT_DIR); fs.rmSync(out, { recursive: true, force: true }); fs.mkdirSync(out, { recursive: true });
  let cfg = {}; try { cfg = JSON.parse(fs.readFileSync(path.join(dir, "piece.json"), "utf8")).verify || {}; } catch {}
  const secSel = cfg.sections || DEFAULT_SECTIONS;
  const srv = val("--url") ? { url: val("--url"), stop() {} } : await startServer(dir);
  const t0 = Date.now(), report = { url: srv.url, fast, started: new Date().toISOString(), viewports: {} };
  const vps = VIEWPORTS.filter((v) => !val("--only") || String(v.w) === val("--only"));
  try {
    // 1) chrome-shot: console errors, overflow, font rendered, tells.js (both widths)
    const csOut = path.join(out, "chrome");
    spawnSync("node", [path.join(HERE, "chrome-shot.mjs"), withQuery(srv.url, "noprobe"), csOut, vps.map((v) => v.w).join(",")], { env: { ...process.env, EVAL: path.join(HERE, "tells.js"), SHOTS: "0" }, stdio: "ignore" });
    const cs = JSON.parse(fs.readFileSync(path.join(csOut, "report.json"), "utf8"));
    for (const v of vps) { const c = cs[v.w] || { problems: ["chrome-shot produced no report"] }; report.viewports[v.w] = { problems: c.problems, sw: c.sw, cw: c.cw, rendered: c.rendered }; if (c.eval?.tells && !report.tells) report.tells = { templaty: c.eval.templaty, hits: c.eval.hits, craft_fail: c.eval.craft_fail }; }
    // 2) own session per viewport: stepped-scroll stills with settle, per-section probes, mobile tap/font, fps
    for (const v of vps) {
      const cdp = await open(); const R = report.viewports[v.w]; R.sections = [];
      try {
        await cdp.setViewport(v.w, v.h, v.mobile); await cdp.goto(withQuery(srv.url, "noprobe")); await sleep(BOOT_WAIT_MS);
        const ids = await cdp.evaluate(`[...document.querySelectorAll(${JSON.stringify(secSel)})].map((e, i) => String(i).padStart(2, '0') + '-' + (e.id || e.getAttribute('aria-labelledby') || e.tagName.toLowerCase()).replace(/[^a-z0-9-]/gi, ''))`);
        await cdp.evaluate("document.documentElement.style.scrollBehavior = 'auto'");
        for (let i = 0; i < ids.length; i++) {
          const nav = await cdp.evaluate(`(() => { const hs = [...document.querySelectorAll('header, nav, [role=banner]')].filter((h) => { const c = getComputedStyle(h), b = h.getBoundingClientRect(); return (c.position === 'fixed' || c.position === 'sticky') && b.top <= 1 && b.height < ${NAV_MAX_PX}; }); return Math.max(0, ...hs.map((h) => h.getBoundingClientRect().height)); })()`);
          await cdp.evaluate(`(async () => { const t = document.querySelectorAll(${JSON.stringify(secSel)})[${i}].getBoundingClientRect().top + scrollY - ${nav}, f = scrollY; for (let k = 1; k <= ${SCROLL_STEPS}; k++) { scrollTo(0, f + (t - f) * k / ${SCROLL_STEPS}); await new Promise((r) => requestAnimationFrame(() => setTimeout(r, ${SCROLL_STEP_MS}))); } })()`);
          const settled = await cdp.settle();
          const sd = path.join(out, "sections", ids[i]); fs.mkdirSync(sd, { recursive: true });
          const file = path.join(sd, `${v.w}.png`); await cdp.shot(file);
          const probe = await cdp.evaluate(SECTION_PROBE(secSel, i, cfg.subject || "", cfg.subjectBox || "", cfg.ignore || ""));
          R.sections.push({ id: ids[i], file, settled, ...probe });
        }
        if (v.mobile) Object.assign(R, await cdp.evaluate(MOBILE_PROBE));
        if (!fast) { await cdp.send("Emulation.setCPUThrottlingRate", { rate: FPS_THROTTLE }); await cdp.evaluate("scrollTo(0,0)"); await sleep(BOOT_WAIT_MS / 2); R.fps = await cdp.evaluate(FPS_PROBE); await cdp.send("Emulation.setCPUThrottlingRate", { rate: 1 }); }
      } finally { cdp.close(); }
    }
    // 3) saturation over the desktop stills
    const sat = spawnSync("python3", ["-I", path.join(HERE, "saturation.py"), path.join(out, "sections")], { encoding: "utf8" });
    const lines = (sat.stdout || "").split("\n"); report.saturation = { toy: lines.filter((l) => l.startsWith("TOY")).length, loud: lines.filter((l) => l.startsWith("LOUD")).length, mean: (/mean vivid share ([\d.]+)/.exec(sat.stdout || "") || [])[1], pageFail: sat.status === 1 };
    // 4) lighthouse (not --fast)
    if (!fast && !flag("--no-lighthouse")) {
      const lhDir = path.join(out, "lh"); spawnSync("bash", [path.join(HERE, "lighthouse.sh"), srv.url, lhDir, "1"], { stdio: "ignore" }); report.lighthouse = {};
      for (const [k, f] of [["mobile", "mobile-1.json"], ["desktop", "desktop.json"]]) { try { const c = JSON.parse(fs.readFileSync(path.join(lhDir, f), "utf8")).categories; report.lighthouse[k] = Object.fromEntries(Object.entries(c).map(([n, x]) => [n, Math.round(x.score * 100)])); } catch { report.lighthouse[k] = { error: "lighthouse failed (network for npx?)" , accessibility: 0, "best-practices": 0, seo: 0, performance: 0 }; } }
    }
  } finally { srv.stop(); }
  const { hard, soft } = gate(report); report.hard = hard; report.soft = soft; report.failing_sections = failingSections(report); report.seconds = Math.round((Date.now() - t0) / 1000);
  fs.writeFileSync(path.join(out, "report.json"), JSON.stringify(report, null, 1));
  const L = [`verify-piece ${path.basename(dir)}  ${report.seconds}s  ${fast ? "--fast" : "full"}  ${srv.url}`];
  for (const [vp, v] of Object.entries(report.viewports)) L.push(`  ${vp}: ${v.sections.length} sections, sw ${v.sw}/${v.cw}, errors ${v.problems.length}${v.fps ? `, fps p50 ${v.fps.p50}ms p95 ${v.fps.p95}ms long ${v.fps.longPct}%` : ""}${v.tapTotal != null ? `, taps ${v.tapTotal} (<${TAP_HARD_PX}px: ${v.tapHard.length})` : ""}`);
  if (report.lighthouse) for (const [k, c] of Object.entries(report.lighthouse)) L.push(`  lighthouse ${k}: perf ${c.performance} a11y ${c.accessibility} bp ${c["best-practices"]} seo ${c.seo}`);
  L.push(`  tells: ${report.tells ? (report.tells.hits.join(",") || "none") + (report.tells.templaty ? " TEMPLATY" : "") : "n/a"}; saturation: ${report.saturation.toy} TOY, ${report.saturation.loud} LOUD, mean ${report.saturation.mean}`);
  if (!fast) L.push(`  caveat: fps is headless + ${FPS_THROTTLE}x CPU throttle, Lighthouse perf is localhost: relative signals, not device truth`);
  if (!report.viewports[vps[0].w].sections.some((s) => s.subjectBox)) L.push("  collision check SKIPPED: no subject box (set piece.json verify.subject or verify.subjectBox)");
  hard.slice(0, 12).forEach((h) => L.push("  FAIL " + h)); soft.slice(0, 10).forEach((s) => L.push("  warn " + s));
  const stills = report.failing_sections.map((id) => path.join(OUT_DIR, "sections", id));
  L.push(report.failing_sections.length ? `  failing sections (open only these): ${stills.join(" ")}` : "  failing sections: none");
  L.push(`${hard.length ? "FAIL" : "PASS"}: ${hard.length} hard, ${soft.length} warnings; report ${path.join(OUT_DIR, "report.json")} (paths relative to the piece dir); critic subset: node critic-batch.mjs <piece-dir>`);
  console.log(L.slice(0, SUMMARY_MAX_LINES).join("\n"));
  return hard.length ? 1 : 0;
}
if (import.meta.url === `file://${process.argv[1]}`) main(process.argv.slice(2)).then((c) => process.exit(c), (e) => { console.error("verify-piece error: " + e.message); process.exit(2); });
