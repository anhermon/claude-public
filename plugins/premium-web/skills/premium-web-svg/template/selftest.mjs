// Headless check of the SVG template: generated figures are valid and accessible, draw-on plays and ends in the final state,
// reduced motion and no-JS show the final state at once, labels fit their boxes, icons inherit currentColor, filters render.
// Frames go to ./.selftest/ (git-ignored): LOOK at them. Run: PLAYWRIGHT_NODE=<dir with node_modules/playwright> node selftest.mjs
import { spawn } from 'node:child_process';
import { mkdirSync, rmSync, writeFileSync, readFileSync } from 'node:fs';
import { createRequire } from 'node:module';
import { fileURLToPath } from 'node:url';
import path from 'node:path';
import { render } from './svgfig.mjs';
import { sprite, ICON_CSS } from './sprite.mjs';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const OUT = path.join(HERE, '.selftest');
const PORT = 8744, CHROME = process.env.CHROME || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const PW = process.env.PLAYWRIGHT_NODE || process.cwd();
const { chromium } = createRequire(path.join(PW, 'x.js'))('playwright');
const VIEW = { width: 900, height: 700 }, MID_MS = 700, END_MS = 4200, MAX_SVG_BYTES = 12000, FIT_PAD = 12, SPACER_PX = 1200;
rmSync(OUT, { recursive: true, force: true }); mkdirSync(OUT, { recursive: true });

const j = (f) => JSON.parse(readFileSync(path.join(HERE, f), 'utf8'));
const figs = [render(j('diagram.config.json')), render(j('bars.config.json'))];
writeFileSync(path.join(OUT, 'diagram.svg'), render({ ...j('diagram.config.json'), trigger: 'load' }));   // standalone file: plays on load
const icons = Object.keys(j('icons.json'));
const page = `<!doctype html><html lang="en"><head><meta charset="utf-8"><title>svg selftest</title><link rel="icon" href="data:,"><style>
html{background:#f6f4ef}body{margin:0;padding:24px;font:16px system-ui;color:#16181d}.spacer{height:${SPACER_PX}px}svg[data-fig]{max-width:760px;width:100%;display:block;margin:24px 0}
${ICON_CSS}.row{display:flex;gap:16px;align-items:center}.row.b{color:#e4572e}</style></head><body>
${sprite(j('icons.json'))}<div class="row" id="r1">${icons.map((n) => `<svg class="icon" aria-hidden="true"><use href="#i-${n}"/></svg>`).join('')}</div>
<div class="row b" id="r2">${icons.map((n) => `<svg class="icon" aria-hidden="true"><use href="#i-${n}"/></svg>`).join('')}</div>
<div class="spacer"></div>${figs.join('\n')}<div class="spacer"></div><script src="../figure.js"></script></body></html>`;
writeFileSync(path.join(OUT, 'page.html'), page);

const srv = spawn('python3', ['-m', 'http.server', String(PORT), '--bind', '127.0.0.1'], { cwd: HERE, stdio: 'ignore' });
await new Promise((r) => setTimeout(r, 800));
const browser = await chromium.launch({ executablePath: CHROME, headless: true });
let failed = 0;
const check = (label, ok, info = '') => { console.log(`${ok ? 'PASS' : 'FAIL'}  ${label}${info ? '  [' + info + ']' : ''}`); if (!ok) failed++; };
const url = `http://127.0.0.1:${PORT}/.selftest/page.html`;
async function open(extra = {}, emulate = {}) {
  const ctx = await browser.newContext({ viewport: VIEW, deviceScaleFactor: 1, ...extra });
  const p = await ctx.newPage(); const errs = [];
  p.on('pageerror', (e) => errs.push(String(e))); p.on('console', (m) => m.type() === 'error' && errs.push(m.text()));
  if (emulate.reducedMotion) await p.emulateMedia({ reducedMotion: emulate.reducedMotion });
  await p.goto(url); return { ctx, p, errs };
}
const toFig = (p, i) => p.evaluate((k) => document.querySelectorAll('svg[data-fig]')[k].scrollIntoView({ block: 'center' }), i);
const minOpacity = (p, i) => p.evaluate((k) => Math.min(...[...document.querySelectorAll('svg[data-fig]')[k].querySelectorAll('.node,.note')].map((e) => +getComputedStyle(e).opacity)), i);
const maxDash = (p, i) => p.evaluate((k) => Math.max(...[...document.querySelectorAll('svg[data-fig]')[k].querySelectorAll('.draw')].map((e) => parseFloat(getComputedStyle(e).strokeDashoffset) || 0)), i);
const minDash = (p, i) => p.evaluate((k) => Math.min(...[...document.querySelectorAll('svg[data-fig]')[k].querySelectorAll('.draw')].map((e) => parseFloat(getComputedStyle(e).strokeDashoffset) || 0)), i);
const shotEl = (p, i, name) => p.locator('svg[data-fig]').nth(i).screenshot({ path: `${OUT}/${name}.png` });

try {
  // 1. static validity and size
  figs.forEach((f, i) => check(`figure ${i} is under ${MAX_SVG_BYTES} bytes`, f.length < MAX_SVG_BYTES, `${f.length} bytes`));
  let { ctx, p, errs } = await open();
  const valid = await p.evaluate((svgs) => svgs.every((s) => !new DOMParser().parseFromString(s, 'image/svg+xml').querySelector('parsererror')), figs);
  check('figures parse as XML (no parsererror)', valid);
  check('every figure has role=img, a title and a desc that its aria-labelledby points at', await p.evaluate(() => [...document.querySelectorAll('svg[data-fig]')].every((s) => {
    const ids = s.getAttribute('aria-labelledby').split(' '); return s.getAttribute('role') === 'img' && ids.length === 2 && ids.every((id) => (document.getElementById(id)?.textContent || '').trim().length > 10);
  })));
  check('every node label fits inside its box', await p.evaluate((pad) => [...document.querySelectorAll('svg[data-fig] .node')].every((g) => { const r = g.querySelector('rect').getBBox(); return [...g.querySelectorAll('text')].every((t) => t.getBBox().width <= r.width - pad); }), FIT_PAD));

  check('edge labels do not touch any node box', await p.evaluate(() => [...document.querySelectorAll('svg[data-fig]')].every((svg) => [...svg.querySelectorAll('g.note.sub')].every((g) => {
    const t = g.getBBox(); return [...svg.querySelectorAll('.node rect')].every((r) => { const b = r.getBBox(); return t.x + t.width <= b.x || t.x >= b.x + b.width || t.y + t.height <= b.y || t.y >= b.y + b.height; }); }))));

  // 2. icons: sprite renders and inherits currentColor
  const ic = await p.evaluate(() => { const a = document.querySelector('#r1 .icon'), b = document.querySelector('#r2 .icon'); return { w: a.getBoundingClientRect().width, sa: getComputedStyle(a).stroke, sb: getComputedStyle(b).stroke }; });
  check('icons render at 1.5em and take their colour from the parent', ic.w > 16 && ic.sa !== ic.sb && ic.sb === 'rgb(228, 87, 46)', JSON.stringify(ic));
  await p.locator('#r1').screenshot({ path: `${OUT}/1-icons-ink.png` }); await p.locator('#r2').screenshot({ path: `${OUT}/1-icons-accent.png` });

  // 3. inview draw-on: hidden before, mid-animation, final
  check('figure below the fold starts hidden (pending)', (await minOpacity(p, 0)) === 0 && (await maxDash(p, 0)) > 0.9);
  await toFig(p, 0); await p.waitForTimeout(MID_MS); await shotEl(p, 0, '2-diagram-mid');
  const [lo, hi] = [await minDash(p, 0), await maxDash(p, 0)];
  check('draw-on is mid-flight shortly after entering the view (some edges drawn, some not)', lo < 1 && hi > 0, `dashoffset min ${lo} max ${hi}`);
  await p.waitForTimeout(END_MS); await shotEl(p, 0, '3-diagram-end');
  check('diagram ends in its final state', (await minOpacity(p, 0)) === 1 && (await maxDash(p, 0)) === 0);
  await toFig(p, 1); await p.waitForTimeout(MID_MS); await shotEl(p, 1, '4-bars-mid'); await p.waitForTimeout(END_MS); await shotEl(p, 1, '5-bars-end');
  check('bars end in their final state', (await minOpacity(p, 1)) === 1);
  check('no console errors', errs.length === 0, errs.join(' | '));
  await ctx.close();

  // 4. reduced motion: final state immediately
  ({ ctx, p } = await open({}, { reducedMotion: 'reduce' }));
  await toFig(p, 0); await p.waitForTimeout(100);
  check('reduced motion: final state at once', (await minOpacity(p, 0)) === 1 && (await maxDash(p, 0)) === 0);
  await ctx.close();

  // 5. no JS: visible
  ({ ctx, p } = await open({ javaScriptEnabled: false }));
  check('no JS: figures are fully visible', (await minOpacity(p, 0)) === 1 && (await minOpacity(p, 1)) === 1);
  await ctx.close();

  // 6. standalone file plays on load, filters demo renders
  ({ ctx, p, errs } = await open()); await p.goto(`http://127.0.0.1:${PORT}/.selftest/diagram.svg`); await p.waitForTimeout(MID_MS); await p.screenshot({ path: `${OUT}/6-standalone-mid.png` });
  await p.waitForTimeout(END_MS); await p.screenshot({ path: `${OUT}/6-standalone-end.png` });
  check('standalone SVG (trigger load) ends in its final state', await p.evaluate(() => [...document.querySelectorAll('.node')].every((e) => getComputedStyle(e).opacity === '1')));
  errs.length = 0; await p.goto(`http://127.0.0.1:${PORT}/filters.html`); await p.waitForTimeout(300); await p.screenshot({ path: `${OUT}/7-filters.png` });
  check('filters demo has no console errors', errs.length === 0, errs.join(' | '));
  await ctx.close();
} catch (e) { console.error(e); failed++; }
finally { await browser.close(); srv.kill(); }
console.log(failed ? `SELFTEST FAILED (${failed})` : 'SELFTEST OK');
process.exit(failed ? 1 : 0);
