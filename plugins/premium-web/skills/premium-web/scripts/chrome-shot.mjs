// Zero-dependency Chrome capture + checks over raw CDP (Node 22+ global WebSocket). Throwaway profile, never your
// logged-in Chrome. Trackers are blocked BEFORE the first navigation.
// Usage: node chrome-shot.mjs <url> <outdir> [widths=1440,390]
//   env: CHROME_FLAGS="--use-angle=metal" (extra Chrome args; WebGL captures can be blank without a real GPU path), CHROME_PATH,
//        RM=1 (prefers-reduced-motion), SCHEME=light|dark, STEPS=n (max viewport shots per width, default 10),
//        EVAL=<file.js> (evaluate a script, e.g. measure-site.js, and save its result; SUMMARY=1 asks measure-site.js for its short form), SHOTS=0 (checks only)
//        SECTIONS=1 (or a selector; default "main > section, footer"): one dir per section in <outdir>/sections/<nn-id>/,
//          files <width>[-pN].png (tall sections split per viewport, max 3). Fixed and sticky headers hidden (WOW scroll offset = measured header height), reveals settled (waits for finite animations to finish, cap 5s).
//          Feed the dir to critic.py.
//        WOW=<selector>: reload, scroll to it, take 7 mid-animation frames (0.25-4.5s; after WOW_ACT=<js> if set) or,
//        for a [data-scene], beat 1 + each beat boundary at 250/700ms + the end (8 frames for 4 beats) -> sections/wow/<width>-tN.png (RM=1: <width>-rm-tN.png)
//          (with RM=1 they are named <width>-rm-tN.png: run once without and once with RM=1 so the critic sees the fallback)
// Writes <outdir>/<w>-NN.png (one per viewport while scrolling like a visitor) and <outdir>/report.json.
// Exit code 1 if any width has horizontal scroll, page errors, failed fonts or a custom font that never rendered.
import { spawn } from "node:child_process";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";

const [url, out = "shots", ws = "1440,390"] = process.argv.slice(2);
if (!url) { console.error("usage: node chrome-shot.mjs <url> <outdir> [widths]"); process.exit(2); }
const CHROME = process.env.CHROME_PATH || "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
const BLOCK = ["*posthog*", "*googletagmanager*", "*google-analytics*", "*plausible.io*", "*segment.io*", "*mixpanel*", "*hotjar*", "*clarity.ms*"];
const STEPS = +(process.env.STEPS || 10);
fs.mkdirSync(out, { recursive: true });
const wait = (ms) => new Promise((r) => setTimeout(r, ms));

const dir = fs.mkdtempSync(path.join(os.tmpdir(), "pw-chrome-"));
const chrome = spawn(CHROME, ["--headless=new", "--remote-debugging-port=0", "--remote-allow-origins=*", `--user-data-dir=${dir}`,
  "--no-first-run", "--no-default-browser-check", "--hide-scrollbars", "--enable-webgl", "--ignore-gpu-blocklist", ...(process.env.CHROME_FLAGS ? process.env.CHROME_FLAGS.split(/\s+/) : []), "about:blank"], { stdio: "ignore" });
let port;
for (let i = 0; i < 100 && !port; i++) { await wait(100); try { port = fs.readFileSync(path.join(dir, "DevToolsActivePort"), "utf8").split("\n")[0]; } catch {} }
if (!port) { console.error("Chrome did not start"); chrome.kill(); process.exit(2); }
const page = (await (await fetch(`http://127.0.0.1:${port}/json/list`)).json()).find((t) => t.type === "page");
const sock = new WebSocket(page.webSocketDebuggerUrl);
await new Promise((r) => (sock.onopen = r));
let id = 0; const pending = new Map(), listeners = [];
sock.onmessage = (m) => { const d = JSON.parse(m.data); if (d.id && pending.has(d.id)) { pending.get(d.id)(d); pending.delete(d.id); } else listeners.forEach((l) => l(d)); };
const send = (method, params = {}) => new Promise((res, rej) => { const i = ++id; pending.set(i, (d) => (d.error ? rej(new Error(method + ": " + d.error.message)) : res(d.result))); sock.send(JSON.stringify({ id: i, method, params })); });
const evaluate = async (expr) => (await send("Runtime.evaluate", { expression: expr, awaitPromise: true, returnByValue: true })).result.value;

const report = {};
let failed = false;
for (const w of ws.split(",").map(Number)) {
  const mobile = w < 768, h = +process.env.H || (mobile ? 844 : 900);
  const errs = [], blocked = [];
  listeners.length = 0;
  listeners.push((d) => {
    if (d.method === "Runtime.exceptionThrown") errs.push("exception: " + (d.params.exceptionDetails.exception?.description || d.params.exceptionDetails.text).split("\n")[0]);
    if (d.method === "Runtime.consoleAPICalled" && d.params.type === "error") errs.push("console.error: " + d.params.args.map((a) => a.value ?? a.description).join(" "));
    if (d.method === "Log.entryAdded" && d.params.entry.level === "error" && !/ERR_BLOCKED_BY_CLIENT/.test(d.params.entry.text)) errs.push("log: " + d.params.entry.text + " " + (d.params.entry.url || ""));
    if (d.method === "Network.loadingFailed" && d.params.blockedReason) blocked.push(d.params.requestId);
  });
  for (const m of ["Page.enable", "Runtime.enable", "Log.enable", "Network.enable", "DOM.enable", "CSS.enable"]) await send(m);
  await send("Network.setBlockedURLs", { urls: BLOCK });
  await send("Network.setCacheDisabled", { cacheDisabled: true });
  await send("Emulation.setDeviceMetricsOverride", { width: w, height: h, deviceScaleFactor: mobile ? 2 : 1, mobile });
  await send("Emulation.setTouchEmulationEnabled", { enabled: mobile });
  const media = [];
  if (process.env.RM === "1") media.push({ name: "prefers-reduced-motion", value: "reduce" });
  if (process.env.SCHEME) media.push({ name: "prefers-color-scheme", value: process.env.SCHEME });
  await send("Emulation.setEmulatedMedia", { features: media });
  const loaded = new Promise((r) => listeners.push((d) => d.method === "Page.loadEventFired" && r()));
  const nav = await send("Page.navigate", { url });
  if (nav.errorText) throw new Error(`navigation failed (${nav.errorText}): is the server running? ${url}`); // a dead server otherwise yields "valid" shots of Chrome's error page
  await Promise.race([loaded, wait(20000)]);
  await wait(2500);

  const shots = [];
  const H = await evaluate("document.documentElement.scrollHeight");
  const n = process.env.SHOTS === "0" ? 0 : Math.min(STEPS, Math.ceil(H / (h * 0.9)));
  for (let i = 0; i < n; i++) {
    await evaluate(`(async () => { document.documentElement.style.scrollBehavior = 'auto'; const to = ${Math.round(i * h * 0.9)}, from = scrollY;
      for (let k = 1; k <= 6; k++) { scrollTo(0, from + (to - from) * k / 6); await new Promise((r) => requestAnimationFrame(() => setTimeout(r, 40))); } })()`);
    await wait(900);
    const f = `${out}/${w}-${String(i).padStart(2, "0")}.png`;
    fs.writeFileSync(f, Buffer.from((await send("Page.captureScreenshot", { format: "png" })).data, "base64"));
    shots.push(f);
  }
  if (process.env.SECTIONS) {
    const sel = process.env.SECTIONS === "1" ? "main > section, footer" : process.env.SECTIONS;
    const secs = await evaluate(`[...document.querySelectorAll(${JSON.stringify(sel)})].map((e, i) => String(i).padStart(2, '0') + '-' + (e.id || e.getAttribute('aria-labelledby') || e.tagName.toLowerCase()).replace(/[^a-z0-9-]/gi, ''))`);
    await evaluate(`document.documentElement.style.scrollBehavior='auto';[...document.querySelectorAll('body *')].filter(e=>getComputedStyle(e).position==='fixed' || (getComputedStyle(e).position==='sticky' && e.matches('header, nav, [role=banner]') && e.getBoundingClientRect().top <= 1)).forEach(e=>e.style.visibility='hidden')`); // sticky headers too, else every section shot starts under the nav; scroll-scene stages (sticky, not headers) stay
    for (let i = 0; i < secs.length; i++) {
      const d = path.join(out, "sections", secs[i]); fs.mkdirSync(d, { recursive: true });
      const r = await evaluate(`(() => { const e = document.querySelectorAll(${JSON.stringify(sel)})[${i}], b = e.getBoundingClientRect(); return { top: b.top + scrollY, height: b.height, scene: e.matches('[data-scene]') }; })()`);
      // scroll scenes are tall by design and every beat gets judged: up to 6 parts; others max 3; short ones (footer) 1
      const parts = Math.max(1, Math.min(r.scene ? 6 : 3, Math.ceil(r.height / h - 0.15)));
      for (let k = 0; k < parts; k++) {
        await evaluate(`scrollTo(0, ${Math.round(r.top + k * h)})`); await wait(r.scene ? 1600 : 900); // reveals (0.6s) / scene easing settle
        // then until every finite CSS/WAAPI animation is done (cap 5s): staggered reveals (sieve chips at .8s + --d) were shot mid-fade
        await evaluate(`new Promise((ok) => { const t0 = performance.now(); (function poll() { const busy = document.getAnimations().some((a) => a.playState === "running" && a.effect && a.effect.getComputedTiming().endTime !== Infinity); if (!busy || performance.now() - t0 > 5000) ok(); else setTimeout(poll, 100); })(); })`);
        const y = await evaluate("scrollY"), clipH = Math.max(1, Math.min(h, r.top + r.height - y));
        const f = path.join(d, `${w}${parts > 1 ? "-p" + (k + 1) : ""}.png`);
        fs.writeFileSync(f, Buffer.from((await send("Page.captureScreenshot", { format: "png", clip: { x: 0, y: Math.round(y), width: w, height: Math.round(clipH), scale: 1 }, captureBeyondViewport: false })).data, "base64"));
      }
    }
    console.log(`${w}px: ${secs.length} sections -> ${path.join(out, "sections")}`);
  }
  if (process.env.WOW) {
    const d = path.join(out, "sections", "wow"); fs.mkdirSync(d, { recursive: true });
    await send("Page.navigate", { url }); await wait(300);
    await evaluate(`new Promise(r => { const go = () => { const e = document.querySelector(${JSON.stringify(process.env.WOW)}); if (e) { document.documentElement.style.scrollBehavior='auto'; const hs = [...document.querySelectorAll('header, nav, [role=banner]')].filter((h) => { const c = getComputedStyle(h), b = h.getBoundingClientRect(); return (c.position === 'fixed' || c.position === 'sticky') && b.top <= 1 && b.width > innerWidth * 0.6 && b.height < 200; }); scrollTo(0, e.getBoundingClientRect().top + scrollY - Math.max(0, ...hs.map((h) => h.getBoundingClientRect().height)) - 8); } r(); }; document.readyState === 'complete' ? go() : addEventListener('load', go); })`);
    // a scroll-driven scene ([data-scene]) is captured at 4 scroll positions (one per beat), not 4 moments:
    // time frames of a scroll scene are identical and the critic rightly scores them "nothing happens"
    const sc = await evaluate(`(() => { const e = document.querySelector(${JSON.stringify(process.env.WOW)}); if (!e || !e.matches('[data-scene]') || e.classList.contains('is-static')) return null; const b = e.getBoundingClientRect(); return { top: b.top + scrollY, span: Math.max(0, b.height - innerHeight), steps: e.querySelectorAll('.scene-step').length || 4 }; })()`);
    // WOW_ACT=<js> starts an interaction (click, replay, drag) and then frames are time-spaced from that moment.
    // Frames are MID-ANIMATION on purpose: polish is judged in motion, not at rest.
    let N; const act = process.env.WOW_ACT, times = [250, 500, 800, 1200, 1800, 2700, 4500]; N = process.env.RM === "1" ? 2 : times.length;
    // scroll scene: beat 1 at rest, then every beat boundary caught twice mid-transition (250ms, 700ms), then the end
    // at rest. Evenly spaced positions landed on settled beats and never showed the payoff transition.
    const plan = sc && !act && process.env.RM !== "1" ? [[0, 1600]].concat([...Array(sc.steps - 1)].flatMap((_, i) => [[(i + 1) / sc.steps + 0.01, 250], [null, 450]]), [[1, 1600]]) : null;
    if (plan) N = plan.length; // reduced motion: a static poster, 2 frames prove it holds still
    if (act) await evaluate(`(async () => { ${act} })()`);
    let t = 0;
    for (let k = 0; k < N; k++) {
      if (plan) { const [p, ms] = plan[k]; if (p !== null) await evaluate(`scrollTo(0, ${Math.round(sc.top + sc.span * Math.min(1, p))})`); await wait(ms); } // null = same position, later in the transition
      else if (sc && !act) { await evaluate(`scrollTo(0, ${Math.round(sc.top + sc.span * k / (N - 1))})`); await wait(1600); }
      else { await wait(times[k] - t); t = times[k]; }
      fs.writeFileSync(path.join(d, `${w}-${process.env.RM === "1" ? "rm-" : ""}t${k + 1}.png`), Buffer.from((await send("Page.captureScreenshot", { format: "png" })).data, "base64"));
    }
    console.log(`${w}px: wow frames -> ${d}`);
  }
  const checks = await evaluate(`(async () => { await document.fonts.ready; const faces = []; document.fonts.forEach((f) => faces.push(f.family.replace(/"/g, '') + ' ' + f.weight + ' ' + f.status));
    return { sw: document.documentElement.scrollWidth, cw: document.documentElement.clientWidth, height: document.documentElement.scrollHeight, faces,
      wide: [...document.querySelectorAll('body *')].filter((e) => { const r = e.getBoundingClientRect(); return r.width && r.right > innerWidth + 1 && getComputedStyle(e).position !== 'fixed'; }).slice(0, 6).map((e) => e.tagName + '.' + String(e.className).slice(0, 40)),
      title: document.title, lang: document.documentElement.lang, h1s: document.querySelectorAll('h1').length, imgsNoAlt: document.querySelectorAll('img:not([alt])').length, state: { ...document.documentElement.dataset } }; })()`);
  // Which font actually RENDERED (not just what CSS asked for): CDP CSS.getPlatformFontsForNode
  const { root } = await send("DOM.getDocument", { depth: -1 });
  const rendered = {};
  for (const sel of ["h1", "h2", "main p:not(:empty)", "button, .btn", "input", "code"]) {
    const { nodeId } = await send("DOM.querySelector", { nodeId: root.nodeId, selector: sel });
    if (!nodeId) continue;
    try { rendered[sel] = (await send("CSS.getPlatformFontsForNode", { nodeId })).fonts.map((f) => f.familyName + (f.isCustomFont ? " (webfont)" : " (system)")).join(", "); } catch {}
  }
  let evalResult;
  if (process.env.EVAL) { // scan a fully revealed page: scroll-reveals left at opacity 0 read as "no media" (false tells after the WOW reload)
    await evaluate(`(async () => { document.documentElement.style.scrollBehavior = 'auto'; for (let y = 0; y < document.documentElement.scrollHeight; y += innerHeight * 0.6) { scrollTo(0, y); await new Promise((r) => setTimeout(r, 120)); } await new Promise((r) => setTimeout(r, 900)); scrollTo(0, 0); })()`);
    evalResult = await evaluate((process.env.SUMMARY ? "window.__SUMMARY = true;\n" : "") + fs.readFileSync(process.env.EVAL, "utf8"));
  }
  const problems = [];
  if (checks.sw > checks.cw) problems.push(`horizontal scroll: scrollWidth ${checks.sw} > ${checks.cw}`, ...checks.wide.map((x) => "too wide: " + x));
  if (errs.length) problems.push(...errs);
  if (checks.faces.some((f) => / error$/.test(f))) problems.push("font failed to load: " + checks.faces.filter((f) => / error$/.test(f)).join("; "));
  if (checks.faces.length && !Object.values(rendered).some((v) => v.includes("(webfont)"))) problems.push("webfonts declared but none rendered on h1/h2/p/button");
  if (problems.length) failed = true;
  report[w] = { url, shots, ...checks, rendered, trackersBlocked: blocked.length, problems, eval: evalResult };
  console.log(`${w}px: ${problems.length ? "PROBLEMS" : "ok"} | sw ${checks.sw}/${checks.cw} | ${shots.length} shots | trackers blocked ${blocked.length} | rendered ${JSON.stringify(rendered)}`);
  problems.forEach((p) => console.log("   - " + p));
}
fs.writeFileSync(`${out}/report.json`, JSON.stringify(report, null, 2));
sock.close(); chrome.kill();
try { fs.rmSync(dir, { recursive: true, force: true }); } catch {}
console.log(`report: ${out}/report.json  — now OPEN every PNG and look at it.`);
process.exit(failed ? 1 : 0);
