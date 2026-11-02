// Headless check of the motion template: entrance, reveals, pinned stage (chapters, rail, stepper), curtain overlap,
// reduced-motion path, mobile viewport, frame times. Frames go to ./.selftest/ (git-ignored): LOOK at them.
// Run: PLAYWRIGHT_NODE=<dir with node_modules/playwright> node selftest.mjs
import { spawn } from 'node:child_process';
import { mkdirSync, rmSync } from 'node:fs';
import { createRequire } from 'node:module';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const OUT = path.join(HERE, '.selftest');
const PORT = 8742;
const CHROME = process.env.CHROME || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const PW = process.env.PLAYWRIGHT_NODE || process.cwd();
const { chromium } = createRequire(path.join(PW, 'x.js'))('playwright');
const DESKTOP = { width: 1280, height: 720 }, MOBILE = { width: 390, height: 844 };
const CPU_THROTTLE = 4, SETTLE_MS = 1600, SWEEP_MS = 3000, MAX_P99_MS = 34;   // p99 <= 2 frames at 60 Hz even throttled
rmSync(OUT, { recursive: true, force: true }); mkdirSync(OUT, { recursive: true });

const srv = spawn('python3', ['-m', 'http.server', String(PORT), '--bind', '127.0.0.1'], { cwd: HERE, stdio: 'ignore' });
await new Promise((r) => setTimeout(r, 800));
const browser = await chromium.launch({ executablePath: CHROME, headless: true });
let failed = 0;
const check = (label, ok, info = '') => { console.log(`${ok ? 'PASS' : 'FAIL'}  ${label}${info ? '  [' + info + ']' : ''}`); if (!ok) failed++; };
const url = (q = '') => `http://127.0.0.1:${PORT}/index.html${q}`;
async function open(viewport, q = '', extra = {}) {
  const ctx = await browser.newContext({ viewport, deviceScaleFactor: 1, ...extra });
  const page = await ctx.newPage(); const errs = [];
  page.on('pageerror', (e) => errs.push(String(e)));
  page.on('console', (m) => m.type() === 'error' && errs.push(m.text()));
  await page.goto(url(q));
  return { ctx, page, errs };
}
const scrollStage = (page, p) => page.evaluate((f) => { const s = document.querySelector('[data-stage]'); window.scrollTo(0, s.offsetTop + f * (s.offsetHeight - innerHeight)); }, p);
const shot = (page, name) => page.screenshot({ path: `${OUT}/${name}.png` });

try {
  // 1. entrance chapter + hero reveals (real time)
  let { ctx, page, errs } = await open(DESKTOP);
  await page.waitForTimeout(350); await shot(page, '1-loader-start');
  await page.waitForTimeout(900); await shot(page, '2-loader-lift');
  await page.waitForSelector('html[data-ready="1"]', { timeout: 10000 });
  check('loader finished and removed itself', await page.evaluate(() => !document.querySelector('[role=status]')));
  await page.waitForTimeout(SETTLE_MS); await shot(page, '3-hero');
  check('hero reveals left no hidden state', await page.evaluate(() => document.querySelectorAll('#hero [data-ck-hidden]').length === 0));
  check('hero count-up ends on the authored value', await page.evaluate(() => document.querySelector('[data-motion=count-up]').textContent.trim() === '1,240'));
  check('hero clip-path cleared after fullbleed', await page.evaluate(() => document.getElementById('hero').style.clipPath === ''));

  // 1b. the other two entrance variants (frames mid-entrance, then removal)
  for (const type of ['hole-expand', 'slab-to-node']) {
    const o = await open(DESKTOP, `?loader=${type}`);
    await o.page.waitForTimeout(type === 'hole-expand' ? 1300 : 350); await shot(o.page, `1b-${type}-mid`);
    await o.page.waitForSelector('html[data-ready="1"]', { timeout: 10000 });
    check(`${type}: loader removed, no console errors`, await o.page.evaluate(() => !document.querySelector('[role=status]')) && o.errs.length === 0, o.errs.join(' | '));
    await o.ctx.close();
  }

  // 2. pinned stage: chapters, hand-off, stepper, rail
  const seen = [];
  for (const p of [0.05, 0.45, 0.9]) {
    await scrollStage(page, p); await page.waitForTimeout(SETTLE_MS + 500);
    const s = await page.evaluate(() => { const e = document.querySelector('[data-stage]'); const a = e.querySelector('[data-step][data-active]'); return { ch: e.dataset.chapter, bg: getComputedStyle(e).backgroundColor, step: a && a.textContent, rail: document.querySelector('[data-rail]').style.transform }; });
    seen.push(s); await shot(page, `4-stage-${p}`);
  }
  check('chapters advance arrival -> method -> proof', seen.map((s) => s.ch).join() === 'arrival,method,proof', seen.map((s) => s.ch).join());
  check('palette hand-off changed the stage background', new Set(seen.map((s) => s.bg)).size === 3, seen.map((s) => s.bg).join(' | '));
  check('stepper shows one step per slice', seen.map((s) => s.step).join() === 'Arrive.,Shift the light.,Show the proof.', seen.map((s) => s.step).join());
  check('rail travelled left', parseFloat(/translate3d\((-?[\d.]+)px/.exec(seen[2].rail)?.[1] ?? '0') < -200, seen[2].rail);

  // 3. curtain overlap
  await page.evaluate(() => document.getElementById('stack').scrollIntoView()); await page.waitForTimeout(500);
  await page.evaluate(() => window.scrollBy(0, innerHeight * 0.55)); await page.waitForTimeout(SETTLE_MS); await shot(page, '5-curtain-mid');
  await page.evaluate(() => window.scrollBy(0, innerHeight * 0.6)); await page.waitForTimeout(SETTLE_MS);
  check('curtain active panel advanced', await page.evaluate(() => Number(document.getElementById('stack').dataset.ckActive) >= 1));
  check('no console errors (desktop)', errs.length === 0, errs.slice(0, 2).join(' | '));
  await ctx.close();

  // 4. reduced motion: final state, no pin, no loader, no animations
  ({ ctx, page, errs } = await open(DESKTOP, '?reduced=1', { reducedMotion: 'reduce' }));
  await page.waitForSelector('html[data-ready="1"]', { timeout: 5000 }); await page.waitForTimeout(500);
  const red = await page.evaluate(() => ({ hidden: document.querySelectorAll('[data-ck-hidden]').length, anims: document.getAnimations().length, loader: !!document.querySelector('[role=status]'), h: document.querySelector('[data-stage]').style.height, cursor: !!document.querySelector('[data-cursor-ring]') }));
  await shot(page, '6-reduced');
  check('reduced motion: final state, no animations, no loader, stage unpinned, no cursor', !red.hidden && !red.anims && !red.loader && red.h === 'auto' && !red.cursor, JSON.stringify(red));
  check('no console errors (reduced)', errs.length === 0, errs.join(' | '));
  await ctx.close();

  // 5. mobile 390 + 4x CPU throttle: frames + scroll sweep timings
  ({ ctx, page, errs } = await open(MOBILE, '?noloader=1', { isMobile: true, hasTouch: true }));
  const cdp = await ctx.newCDPSession(page); await cdp.send('Emulation.setCPUThrottlingRate', { rate: CPU_THROTTLE });
  await page.waitForTimeout(SETTLE_MS); await shot(page, '7-mobile-hero');
  await scrollStage(page, 0.5); await page.waitForTimeout(SETTLE_MS); await shot(page, '8-mobile-stage');
  const perf = await page.evaluate(async (dur) => {
    const d = []; let last = performance.now(); const t0 = last; const max = document.documentElement.scrollHeight - innerHeight;
    await new Promise((res) => { const f = (n) => { d.push(n - last); last = n; const k = (n - t0) / dur; scrollTo(0, Math.min(1, k) * max); k < 1 ? requestAnimationFrame(f) : res(); }; requestAnimationFrame(f); });
    d.shift(); const s = [...d].sort((a, b) => a - b); return { p50: s[Math.floor(s.length * 0.5)], p99: s[Math.floor(s.length * 0.99)], n: d.length };
  }, SWEEP_MS);
  console.log(`INFO  mobile 390x844, ${CPU_THROTTLE}x CPU throttle, scroll sweep: p50 ${perf.p50.toFixed(1)} ms, p99 ${perf.p99.toFixed(1)} ms over ${perf.n} frames`);
  check(`scroll sweep p99 <= ${MAX_P99_MS} ms`, perf.p99 <= MAX_P99_MS, `p99 ${perf.p99.toFixed(1)}`);
  check('no horizontal page scroll at 390', await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1));
  check('no console errors (mobile)', errs.length === 0, errs.slice(0, 2).join(' | '));
  await ctx.close();
} catch (e) { check('selftest threw', false, String(e.stack || e).slice(0, 500)); }
await browser.close(); srv.kill();
console.log(failed ? `SELFTEST FAILED (${failed})` : 'SELFTEST OK', '(frames in .selftest/)');
process.exit(failed ? 1 : 0);
