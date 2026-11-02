// Headless check of scrub-player + scrub.sh + pipeline.py. Needs ffmpeg, python3+Pillow, Chrome and Playwright.
// Run: PLAYWRIGHT_NODE=<dir containing node_modules/playwright> node selftest.mjs   (outputs frames to ./.selftest/, git-ignored)
import { execFileSync, spawn } from 'node:child_process';
import { mkdirSync, rmSync, readFileSync } from 'node:fs';
import { createRequire } from 'node:module';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const OUT = path.join(HERE, '.selftest');
const PORT = 8731;
const CHROME = process.env.CHROME || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const PW = process.env.PLAYWRIGHT_NODE || process.cwd();
const { chromium } = createRequire(path.join(PW, 'x.js'))('playwright');
const CLIP = { seconds: 3, fps: 30, width: 960, seqFps: 12 };
const POSITIONS = [0, 0.5, 1];
const FRAME_TOLERANCE = 1;

rmSync(OUT, { recursive: true, force: true }); mkdirSync(OUT, { recursive: true });
execFileSync('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'lavfi', '-i', `testsrc2=size=1280x720:rate=${CLIP.fps}:duration=${CLIP.seconds}`, '-pix_fmt', 'yuv420p', `${OUT}/in.mp4`]);
execFileSync(path.join(HERE, 'scrub.sh'), [`${OUT}/in.mp4`, `${OUT}/media`, CLIP.width, CLIP.fps, CLIP.seqFps], { stdio: 'inherit' });
const manifest = JSON.parse(readFileSync(`${OUT}/media/manifest.json`, 'utf8'));
const keyflags = execFileSync('ffprobe', ['-v', 'error', '-show_entries', 'packet=flags', '-select_streams', 'v:0', '-of', 'csv=p=0', `${OUT}/media/scrub.mp4`]).toString().trim().split('\n');
if (!keyflags.every((f) => f.startsWith('K'))) throw new Error('scrub.mp4 is not all-intra');

const srv = spawn('node', [path.join(HERE, 'serve-range.mjs'), String(PORT), HERE], { stdio: 'ignore' });
await new Promise((r) => setTimeout(r, 800));
const browser = await chromium.launch({ executablePath: CHROME, headless: true });
let failed = 0;
try {
  for (const mode of ['sequence', 'video']) {
    const page = await browser.newPage({ viewport: { width: 1280, height: 720 } });
    const errors = [];
    page.on('pageerror', (e) => errors.push(String(e)));
    page.on('console', (m) => m.type() === 'error' && errors.push(m.text()));
    await page.goto(`http://127.0.0.1:${PORT}/demo.html?base=.selftest/media/&mode=${mode}`);
    await page.waitForSelector('html[data-ready="1"]', { timeout: 15000 });
    for (const p of POSITIONS) {
      await page.evaluate((frac) => { const s = document.querySelector('.scrub'); window.scrollTo(0, s.offsetTop + frac * (s.offsetHeight - innerHeight)); }, p);
      await page.waitForTimeout(1500);                   // let the damped lerp settle
      const frame = await page.evaluate(() => document.getElementById('c').dataset.frame);
      await page.screenshot({ path: `${OUT}/${mode}-${p}.png` });
      if (mode === 'video') {
        const t = await page.evaluate(() => document.getElementById('c').dataset.t);
        const want = p * (CLIP.seconds - 1 / CLIP.fps);
        const ok = t !== undefined && Math.abs(Number(t) - want) <= 0.15;
        console.log(`video p=${p}: currentTime ${t} (want ~${want.toFixed(2)}) ${ok ? 'OK' : 'FAIL'}`);
        if (!ok) failed++;
      }
      if (mode === 'sequence') {
        const want = Math.round(p * (manifest.frames - 1));
        const ok = Math.abs(Number(frame) - want) <= FRAME_TOLERANCE;
        console.log(`sequence p=${p}: frame ${frame} (want ${want}) ${ok ? 'OK' : 'FAIL'}`);
        if (!ok) failed++;
      }
    }
    if (errors.length) { console.log(mode, 'console errors:', errors); failed++; }
    await page.close();
  }
} finally { await browser.close(); srv.kill(); }
console.log(failed ? 'SELFTEST FAILED' : 'SELFTEST OK', '(frames in .selftest/)');
process.exit(failed ? 1 : 0);
