// Headless check of the WebGL template: stage modes (gl, ?nogl poster, ?rm static), point-morph at three scroll states,
// shader field, governor (?slow), context loss and restore, mobile viewport, frame times.
// Frames go to ./.selftest/ (git-ignored): LOOK at them; a passing assertion does not prove the picture is right.
// Run: PLAYWRIGHT_NODE=<dir with node_modules/playwright> node selftest.mjs
// GPU flags are required for real WebGL in headless Chrome: --use-angle=metal --ignore-gpu-blocklist (macOS).
import { spawn } from 'node:child_process';
import { mkdirSync, rmSync } from 'node:fs';
import { createRequire } from 'node:module';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const OUT = path.join(HERE, '.selftest');
const PORT = 8743;
const CHROME = process.env.CHROME || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const GPU_ARGS = (process.env.GPU_ARGS || '--use-angle=metal --ignore-gpu-blocklist').split(' ');
const PW = process.env.PLAYWRIGHT_NODE || process.cwd();
const { chromium } = createRequire(path.join(PW, 'x.js'))('playwright');
const DESKTOP = { width: 1280, height: 720 }, MOBILE = { width: 390, height: 844 };
const MIN_PICTURE_BYTES = 30000;   // a flat colour PNG at 1280x720 is a few KB; a lit point cloud on a glow is far larger
const SETTLE_MS = 2200, SWEEP_MS = 3500, LOST_WAIT_MS = 600;
const MAX_P50_MS = 20, MAX_P99_MS = 34, MOBILE_DPR_CAP = 1.5;
rmSync(OUT, { recursive: true, force: true }); mkdirSync(OUT, { recursive: true });

const srv = spawn('python3', ['-m', 'http.server', String(PORT), '--bind', '127.0.0.1'], { cwd: HERE, stdio: 'ignore' });
await new Promise((r) => setTimeout(r, 800));
const browser = await chromium.launch({ executablePath: CHROME, headless: true, args: GPU_ARGS });
let failed = 0;
const check = (label, ok, info = '') => { console.log(`${ok ? 'PASS' : 'FAIL'}  ${label}${info ? '  [' + info + ']' : ''}`); if (!ok) failed++; };
async function open(viewport, q = '', extra = {}) {
  const ctx = await browser.newContext({ viewport, deviceScaleFactor: 1, ...extra });
  const page = await ctx.newPage(); const errs = [];
  page.on('pageerror', (e) => errs.push(String(e)));
  page.on('console', (m) => m.type() === 'error' && errs.push(m.text()));
  await page.goto(`http://127.0.0.1:${PORT}/index.html${q}`);
  return { ctx, page, errs };
}
const scrollTo = (page, f) => page.evaluate((p) => scrollTo(0, p * (document.documentElement.scrollHeight - innerHeight)), f);
const shot = async (page, name) => { const b = await page.screenshot({ path: `${OUT}/${name}.png` }); return b; };
const mode = (page) => page.evaluate(async () => { await window.stage.ready; return window.stage.mode; });

try {
  // 1. GL path, three scroll states
  let { ctx, page, errs } = await open(DESKTOP);
  check('stage reaches gl mode with the GPU flags', (await mode(page)) === 'gl', await page.evaluate(() => window.stage.mode));
  const bufs = [];
  await page.addStyleTag({ content: '.copy { visibility: hidden !important }' });   // judge the canvas alone: copy would make any two frames differ
  for (const [p, name] of [[0, '1-sphere'], [0.5, '2-torus'], [1, '3-galaxy']]) {
    await scrollTo(page, p); await page.waitForTimeout(SETTLE_MS); bufs.push(await shot(page, name));
  }
  check('canvas frames are real pictures (not flat) and differ per scroll state', bufs.every((b) => b.length > MIN_PICTURE_BYTES) && !bufs[0].equals(bufs[1]) && !bufs[1].equals(bufs[2]) && !bufs[0].equals(bufs[2]), bufs.map((b) => b.length).join('/'));
  await page.addStyleTag({ content: '.copy { visibility: visible !important }' });
  await scrollTo(page, 0.5); await page.waitForTimeout(SETTLE_MS); await shot(page, '2b-torus-with-copy');
  check('poster layer faded out after the first frame', await page.evaluate(() => document.querySelector('.gl-stage-poster').style.opacity === '0'));

  // 2. shader field + frame times over a scroll sweep
  await page.evaluate(() => window.stage.resetStats());
  await page.evaluate(() => document.querySelector('[data-field]').scrollIntoView({ block: 'center' })); await page.waitForTimeout(SETTLE_MS);
  await shot(page, '4-field');
  check('shader field is live (no fallback)', await page.evaluate(() => window.field && !window.field.fallback));
  await scrollTo(page, 0);
  const t0 = Date.now();
  while (Date.now() - t0 < SWEEP_MS) { await scrollTo(page, ((Date.now() - t0) / SWEEP_MS)); await page.waitForTimeout(50); }
  const st = await page.evaluate(() => window.stage.stats());
  check(`frame time p50 <= ${MAX_P50_MS} ms, p99 <= ${MAX_P99_MS} ms`, st.p50 <= MAX_P50_MS && st.p99 <= MAX_P99_MS, `p50 ${st.p50.toFixed(1)} p99 ${st.p99.toFixed(1)} frames ${st.frames} dpr ${st.dpr}`);
  check('no console errors', errs.length === 0, errs.join(' | '));

  // 3. context loss and restore
  await page.evaluate(() => { const g = window.stage.canvas.getContext('webgl2') || window.stage.canvas.getContext('webgl'); window.__lose = g.getExtension('WEBGL_lose_context'); window.__lose.loseContext(); });
  await page.waitForTimeout(LOST_WAIT_MS);
  check('context loss shows the poster and stops the loop', await page.evaluate(() => document.querySelector('.gl-stage-poster').style.opacity === '1' && !window.stage.stats().running));
  await page.evaluate(() => window.__lose.restoreContext()); await page.waitForTimeout(SETTLE_MS);
  check('context restore resumes rendering', await page.evaluate(() => window.stage.stats().running && document.querySelector('.gl-stage-poster').style.opacity === '0'));
  await ctx.close();

  // 4. ?nogl poster path
  ({ ctx, page, errs } = await open(DESKTOP, '?nogl'));
  check('?nogl -> poster mode, field falls back, copy visible', (await mode(page)) === 'poster' && await page.evaluate(() => window.field.fallback === true && getComputedStyle(document.querySelector('h1')).visibility === 'visible'));
  await page.waitForTimeout(400); await shot(page, '5-nogl-poster');
  check('?nogl has no console errors', errs.length === 0, errs.join(' | '));
  await ctx.close();

  // 5. ?rm static path: one frame, no loop
  ({ ctx, page, errs } = await open(DESKTOP, '?rm'));
  await mode(page); await page.waitForTimeout(SETTLE_MS); await shot(page, '6-reduced');
  check('?rm -> static mode, loop not running', await page.evaluate(() => window.stage.mode === 'static' && !window.stage.stats().running), await page.evaluate(() => window.stage.mode));
  await ctx.close();

  // 6. governor: ?slow forces a 1 ms budget, so DPR then point count must step down
  ({ ctx, page, errs } = await open(DESKTOP, '?slow'));
  await mode(page); await page.waitForTimeout(SETTLE_MS * 2);
  const gv = await page.evaluate(() => window.stage.stats());
  check('governor degrades quality when the budget is blown', gv.degrades > 0 && (gv.quality.dprScale < 1 || gv.quality.count < 1), JSON.stringify(gv.quality));
  await ctx.close();

  // 6b. the other field kind
  ({ ctx, page, errs } = await open(DESKTOP, '?field=ribbon'));
  await mode(page); await page.evaluate(() => document.querySelector('[data-field]').scrollIntoView({ block: 'center' })); await page.waitForTimeout(SETTLE_MS); await shot(page, '4b-ribbon');
  check('ribbon field compiles and runs, no console errors', await page.evaluate(() => window.field && !window.field.fallback) && errs.length === 0, errs.join(' | '));
  await ctx.close();

  // 7. mobile: DPR cap, no overflow, upper-half composition
  ({ ctx, page, errs } = await open(MOBILE, '', { deviceScaleFactor: 3, hasTouch: true, isMobile: true }));
  await mode(page); await scrollTo(page, 0.5); await page.waitForTimeout(SETTLE_MS); await shot(page, '7-mobile');
  const mb = await page.evaluate(() => ({ dpr: window.stage.stats().dpr, over: document.documentElement.scrollWidth > innerWidth }));
  check(`mobile DPR capped at ${MOBILE_DPR_CAP}, no horizontal overflow`, mb.dpr <= MOBILE_DPR_CAP && !mb.over, JSON.stringify(mb));
  check('mobile has no console errors', errs.length === 0, errs.join(' | '));
  await ctx.close();
} catch (e) { console.error(e); failed++; }
finally { await browser.close(); srv.kill(); }
console.log(failed ? `SELFTEST FAILED (${failed})` : 'SELFTEST OK');
process.exit(failed ? 1 : 0);
