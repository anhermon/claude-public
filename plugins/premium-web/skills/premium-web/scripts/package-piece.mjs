#!/usr/bin/env node
// package-piece.mjs: portfolio deliverables for a VERIFIED piece, deterministic and idempotent.
//   node package-piece.mjs <piece-dir> [--url URL] [--force] [--webm] [--selftest] [--help]
// Needs <piece-dir>/piece.json and <piece-dir>/.verify/sections/<nn-id>/{1440,390}.png (run verify-piece.mjs first).
// Writes <piece-dir>/media/: poster.webp (1440x900), og.jpg (1200x630), loop-desktop.mp4, loop-mobile.mp4 (+ .webm with --webm),
//   shots/<slug>-<section>-{1440,390}.png (8 sections). Each loop is encoded down a quality LADDER until it fits LOOP_BUDGET_BYTES.
// Then merges files.{poster,og,loops,shots} and media.* into piece.json. Existing outputs are reused (no re-record) unless --force,
// so running twice yields a byte-identical piece.json. The loop is a scripted scroll tour that ends back on the hero (seamless seam).
// No provider is called; nothing is written inside the plugin.
import { spawn, spawnSync } from "node:child_process";
import fs from "node:fs";
import net from "node:net";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { open, sleep } from "./lib/cdp.mjs";

// ---- budget block (override per run with the env var in the comment) -------------------------------------------------
const MB = 1024 * 1024;
const LOOP_BUDGET_BYTES = Number(process.env.PW_LOOP_BUDGET_MB || 2.5) * MB;   // per mp4 / webm
const OG_BUDGET_BYTES = 300 * 1024, OG_W = 1200, OG_H = 630, OG_QUALITY_LADDER = [88, 80, 70, 60];
const POSTER_W = 1440, POSTER_H = 900, POSTER_QUALITY = 84, SHOT_COUNT = 8;
const LOOP_FPS = 24, TOUR_MAX_S = 8, TOUR_SECTIONS = 6, TOUR_INTRO_MS = 1200, TOUR_SCROLL_MS = 700, TOUR_HOLD_MS = 300, TOUR_RETURN_MS = 900, TOUR_BOOT_MS = 2500;
// ladder: tried in order, first that fits the budget wins; w = output width cap (px), crf = x264 quality (higher = smaller), fps
const LADDER = { desktop: [{ w: 1280, crf: 24, fps: 24 }, { w: 1280, crf: 28, fps: 24 }, { w: 1280, crf: 32, fps: 24 }, { w: 1100, crf: 34, fps: 20 }, { w: 960, crf: 36, fps: 20 }, { w: 800, crf: 38, fps: 15 }],
  mobile: [{ w: 780, crf: 24, fps: 24 }, { w: 780, crf: 28, fps: 24 }, { w: 640, crf: 32, fps: 20 }, { w: 540, crf: 34, fps: 20 }, { w: 480, crf: 36, fps: 15 }] };
const WEBM_CRF = 36;
const VIEWS = { desktop: { w: 1440, h: 900, dpr: 1, mobile: false }, mobile: { w: 390, h: 844, dpr: 2, mobile: true } };
const MEDIA_DIR = "media", VERIFY_SECTIONS = path.join(".verify", "sections"), BOOT_SERVE_MS = 8000;
const HERE = path.dirname(fileURLToPath(import.meta.url));
const HELP = `usage: node package-piece.mjs <piece-dir> [--url URL] [--force] [--webm] [--selftest]
  Budget: PW_LOOP_BUDGET_MB (default 2.5) per loop file; ladder of width/crf/fps tried until it fits, else exit 1.
  --selftest  no Chrome: ladder + idempotent merge + (if ffmpeg) a tiny encode`;

const run = (cmd, args, opts = {}) => { const r = spawnSync(cmd, args, { encoding: "utf8", ...opts }); if (r.status !== 0) throw new Error(`${cmd} failed: ${(r.stderr || "").trim().split("\n").slice(-3).join(" | ")}`); return r.stdout; };
const sizeOf = (f) => fs.statSync(f).size;
const probe = (f) => { const [w, h, d] = run("ffprobe", ["-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height:format=duration", "-of", "csv=p=0:s=,", f]).trim().split(/[\n,]/); return { w: +w, h: +h, s: +(+d).toFixed(1) }; };
const PIL = (code, ...args) => run("python3", ["-I", "-c", code, ...args]);

// ---- pure/small pieces (selftest-covered) ------------------------------------------------------------------------------
// frames [{file,t}] -> ffmpeg concat list (each frame shown until the next); last frame gets one frame period
export function concatList(frames, fps = LOOP_FPS) { return frames.map((f, i) => `file '${f.file.replace(/'/g, "'\\''")}'\nduration ${(((frames[i + 1]?.t ?? f.t + 1 / fps) - f.t) || 1 / fps).toFixed(4)}`).join("\n") + `\nfile '${frames.at(-1).file}'\n`; }
// try rungs until encodeFn(rung) -> bytes fits budget. returns { rung, bytes } or null
export function pickRung(rungs, budget, encodeFn) { for (const rung of rungs) { const bytes = encodeFn(rung); if (bytes <= budget) return { rung, bytes }; } return null; }
export function mergePiece(piece, entries) { // idempotent: only the keys we own, stable order
  const out = { ...piece }; out.files = { ...(piece.files || {}), ...entries.files }; out.media = { ...(piece.media || {}), ...entries.media }; return out;
}
function encodeLoop(listFile, out, rung, webm) {
  const vf = `fps=${rung.fps},scale='min(${rung.w},iw)':-2:flags=lanczos,format=yuv420p`;
  run("ffmpeg", ["-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", listFile, "-vf", vf, ...(webm ? ["-c:v", "libvpx-vp9", "-crf", String(WEBM_CRF), "-b:v", "0", "-row-mt", "1"] : ["-c:v", "libx264", "-crf", String(rung.crf), "-preset", "slow", "-movflags", "+faststart"]), "-an", out]);
  return sizeOf(out);
}
function selftest() {
  const frames = [{ file: "/x/a.jpg", t: 0 }, { file: "/x/b.jpg", t: 0.5 }];
  const lst = concatList(frames); let ok = lst.includes("duration 0.5000");
  ok &&= pickRung([{ a: 1 }, { a: 2 }, { a: 3 }], 10, (r) => 30 / r.a)?.rung.a === 3 && pickRung([{ a: 1 }], 1, () => 5) === null;
  const m1 = mergePiece({ slug: "x", files: { entry: "index.html" } }, { files: { poster: "media/poster.webp" }, media: { n: 1 } });
  ok &&= JSON.stringify(mergePiece(m1, { files: { poster: "media/poster.webp" }, media: { n: 1 } })) === JSON.stringify(m1) && m1.files.entry === "index.html";
  if (spawnSync("ffmpeg", ["-version"]).status === 0) {
    const tmp = fs.mkdtempSync(path.join(process.env.TMPDIR || "/tmp", "pp-")), jpg = path.join(tmp, "a.jpg");
    run("ffmpeg", ["-y", "-v", "error", "-f", "lavfi", "-i", "testsrc=size=640x360:rate=1", "-frames:v", "1", jpg]);
    const fr = [{ file: jpg, t: 0 }, { file: jpg, t: 1 }], list = path.join(tmp, "l.txt"); fs.writeFileSync(list, concatList(fr, 24));
    const r = pickRung(LADDER.desktop, 1e9, (g) => encodeLoop(list, path.join(tmp, "o.mp4"), g, false)); const pr = probe(path.join(tmp, "o.mp4"));
    ok &&= !!r && pr.w === 640; fs.rmSync(tmp, { recursive: true, force: true });
  } else console.log("  (ffmpeg missing: encode part of selftest skipped)");
  console.log(ok ? "selftest ok" : "selftest FAILED"); process.exit(ok ? 0 : 1);
}

// ---- recording ------------------------------------------------------------------------------------------------------------
const freePort = () => new Promise((res) => { const s = net.createServer().listen(0, () => { const { port } = s.address(); s.close(() => res(port)); }); });
async function startServer(dir) {
  const p = spawn("node", [path.join(HERE, "serve.mjs"), dir, String(await freePort())], { stdio: ["ignore", "pipe", "inherit"] });
  const url = await new Promise((res, rej) => { const t = setTimeout(() => rej(new Error("serve.mjs did not start")), BOOT_SERVE_MS); p.stdout.on("data", (d) => { const m = /on (http:\/\/localhost:\d+)/.exec(String(d)); if (m) { clearTimeout(t); res(m[1]); } }); });
  return { url: url + "/index.html?noprobe", stop: () => p.kill() };
}
async function recordTour(url, view, framesDir, secSel) {
  const v = VIEWS[view], cdp = await open();
  try {
    await cdp.setViewport(v.w, v.h, v.mobile); await cdp.goto(url); await sleep(TOUR_BOOT_MS);
    const tops = await cdp.evaluate(`(() => { document.documentElement.style.scrollBehavior = 'auto'; const hs = [...document.querySelectorAll('header, nav')].filter((h) => ['fixed', 'sticky'].includes(getComputedStyle(h).position)); const nav = Math.max(0, ...hs.map((h) => h.getBoundingClientRect().height)); return [...document.querySelectorAll(${JSON.stringify(secSel)})].map((e) => Math.round(e.getBoundingClientRect().top + scrollY - nav)).filter((t) => t > 0); })()`);
    const pick = tops.filter((_, i) => i % Math.max(1, Math.ceil(tops.length / TOUR_SECTIONS)) === 0).slice(0, TOUR_SECTIONS);
    const planned = (TOUR_INTRO_MS + pick.length * (TOUR_SCROLL_MS + TOUR_HOLD_MS) + TOUR_RETURN_MS) / 1000;
    if (planned > TOUR_MAX_S) console.log(`  warn: planned tour ${planned.toFixed(1)}s > ${TOUR_MAX_S}s target (lower TOUR_SECTIONS)`);
    const glide = (y, ms) => cdp.evaluate(`new Promise((ok) => { const f = scrollY, t0 = performance.now(); (function s(n) { const p = Math.min(1, (n - t0) / ${ms}), e = p < .5 ? 2 * p * p : 1 - Math.pow(-2 * p + 2, 2) / 2; scrollTo(0, f + (${y} - f) * e); p < 1 ? requestAnimationFrame(s) : ok(); })(t0); })`);
    const frames = await cdp.screencast(framesDir, v.w, v.h, v.dpr, async () => { await sleep(TOUR_INTRO_MS); for (const y of pick) { await glide(y, TOUR_SCROLL_MS); await sleep(TOUR_HOLD_MS); } await glide(0, TOUR_RETURN_MS); await sleep(TOUR_HOLD_MS); });
    return { frames, planned };
  } finally { cdp.close(); }
}

async function main(argv) {
  if (argv.includes("--help") || argv.includes("-h")) { console.log(HELP); return 0; }
  if (argv.includes("--selftest")) return selftest();
  const val = (n) => (argv.includes(n) ? argv[argv.indexOf(n) + 1] : undefined), force = argv.includes("--force"), webm = argv.includes("--webm");
  const dir = path.resolve(argv.find((a, i) => !a.startsWith("--") && argv[i - 1] !== "--url") || "");
  const pj = path.join(dir, "piece.json");
  if (!fs.existsSync(pj)) { console.error("piece.json missing\n" + HELP); return 2; }
  const piece = JSON.parse(fs.readFileSync(pj, "utf8")), slug = piece.slug || path.basename(dir), cfg = piece.verify || {};
  const secRoot = path.join(dir, VERIFY_SECTIONS);
  if (!fs.existsSync(secRoot)) { console.error(`no ${VERIFY_SECTIONS}: run verify-piece.mjs first`); return 2; }
  const media = path.join(dir, MEDIA_DIR), shotsDir = path.join(media, "shots"), rel = (f) => path.relative(dir, f);
  fs.mkdirSync(shotsDir, { recursive: true });
  const L = []; const entries = { files: {}, media: {} };
  // 1) section stills: footer dropped, then evenly sampled down to SHOT_COUNT
  const ids = fs.readdirSync(secRoot).sort().filter((d) => !/footer|foot$/i.test(d) && fs.existsSync(path.join(secRoot, d, "1440.png")));
  const step = ids.length / Math.min(SHOT_COUNT, ids.length), chosen = [...Array(Math.min(SHOT_COUNT, ids.length))].map((_, i) => ids[Math.floor(i * step)]);
  const shots = [];
  for (const id of chosen) for (const w of [1440, 390]) { const src = path.join(secRoot, id, `${w}.png`); if (!fs.existsSync(src)) continue; const dst = path.join(shotsDir, `${slug}-${id.replace(/^\d+-/, "")}-${w}.png`); fs.copyFileSync(src, dst); shots.push(rel(dst)); }
  entries.files.shots = shots.sort(); L.push(`  stills: ${chosen.length} sections -> ${shots.length} files in ${rel(shotsDir)}`);
  // 2) poster + og from the hero still
  const hero = path.join(secRoot, chosen[0], "1440.png"), poster = path.join(media, "poster.webp"), og = path.join(media, "og.jpg");
  PIL("import sys;from PIL import Image;im=Image.open(sys.argv[1]).convert('RGB');W,H=int(sys.argv[3]),int(sys.argv[4]);s=max(W/im.width,H/im.height);im=im.resize((round(im.width*s),round(im.height*s)),Image.LANCZOS);l,t=(im.width-W)//2,(im.height-H)//2;im.crop((l,t,l+W,t+H)).save(sys.argv[2],'WEBP',quality=int(sys.argv[5]),method=6)", hero, poster, String(POSTER_W), String(POSTER_H), String(POSTER_QUALITY));
  let ogBytes = 0; for (const q of OG_QUALITY_LADDER) { PIL("import sys;from PIL import Image;im=Image.open(sys.argv[1]).convert('RGB');W,H=int(sys.argv[3]),int(sys.argv[4]);s=max(W/im.width,H/im.height);im=im.resize((round(im.width*s),round(im.height*s)),Image.LANCZOS);l,t=(im.width-W)//2,(im.height-H)//2;im.crop((l,t,l+W,t+H)).save(sys.argv[2],'JPEG',quality=int(sys.argv[5]),optimize=True)", hero, og, String(OG_W), String(OG_H), String(q)); ogBytes = sizeOf(og); if (ogBytes <= OG_BUDGET_BYTES) break; }
  entries.files.poster = rel(poster); entries.files.og = rel(og); entries.media.og = `${OG_W}x${OG_H}, ${Math.round(ogBytes / 1024)} KB`;
  L.push(`  poster ${rel(poster)} ${Math.round(sizeOf(poster) / 1024)} KB; og ${rel(og)} ${Math.round(ogBytes / 1024)} KB`);
  // 3) loops (record only when missing or --force)
  entries.files.loops = {}; let srv = null, failed = false;
  for (const view of ["desktop", "mobile"]) {
    const mp4 = path.join(media, `loop-${view}.mp4`), wm = mp4.replace(".mp4", ".webm");
    if (force || !fs.existsSync(mp4)) {
      srv ||= val("--url") ? { url: val("--url"), stop() {} } : await startServer(dir);
      const framesDir = path.join(media, `.frames-${view}`); fs.rmSync(framesDir, { recursive: true, force: true });
      const { frames } = await recordTour(srv.url, view, framesDir, cfg.sections || "main > section");
      if (frames.length < 2) { L.push(`  FAIL ${view}: screencast produced ${frames.length} frames (Chrome flags? CHROME_FLAGS=--use-angle=metal)`); failed = true; continue; }
      const list = path.join(framesDir, "list.txt"); fs.writeFileSync(list, concatList(frames));
      const win = pickRung(LADDER[view], LOOP_BUDGET_BYTES, (r) => encodeLoop(list, mp4, r, false));
      if (!win) { L.push(`  FAIL ${view}: no ladder rung fits ${(LOOP_BUDGET_BYTES / MB).toFixed(1)} MB (record a shorter tour)`); fs.rmSync(mp4, { force: true }); failed = true; fs.rmSync(framesDir, { recursive: true, force: true }); continue; }
      if (webm) { encodeLoop(list, wm, win.rung, true); if (sizeOf(wm) > LOOP_BUDGET_BYTES) { fs.rmSync(wm); L.push(`  note: webm for ${view} over budget, dropped`); } }
      fs.rmSync(framesDir, { recursive: true, force: true }); L.push(`  recorded ${view} ${JSON.stringify(win.rung)}`);
    } else L.push(`  reused ${rel(mp4)} (--force to re-record)`);
    const pr = probe(mp4); entries.files.loops[view] = [rel(mp4), ...(fs.existsSync(wm) ? [rel(wm)] : [])]; entries.media[`${view}_loop`] = `${pr.w}x${pr.h}, ${pr.s} s, ${(sizeOf(mp4) / MB).toFixed(2)} MB`;
    L.push(`  ${view} loop ${entries.media[`${view}_loop`]} (budget ${(LOOP_BUDGET_BYTES / MB).toFixed(1)} MB)`);
  }
  srv?.stop();
  if (!failed) fs.writeFileSync(pj, JSON.stringify(mergePiece(piece, entries), null, 2) + "\n");
  console.log(`package-piece ${slug}\n${L.join("\n")}\n${failed ? "FAILED: piece.json not updated" : "piece.json updated"}`);
  return failed ? 1 : 0;
}
if (import.meta.url === `file://${process.argv[1]}`) main(process.argv.slice(2)).then((c) => process.exit(c), (e) => { console.error("package-piece error: " + e.message); process.exit(2); });
