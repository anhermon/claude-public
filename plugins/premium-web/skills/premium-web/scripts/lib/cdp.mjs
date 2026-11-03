// Minimal raw-CDP helper shared by verify-piece.mjs and package-piece.mjs (Node 22+, zero deps, throwaway profile).
// open(opts) -> { send, evaluate, shot, setViewport, goto, settle, close }
import { spawn } from "node:child_process";
import crypto from "node:crypto";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";

const DEFAULT_CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
const BOOT_POLLS = 100, BOOT_POLL_MS = 100, LOAD_TIMEOUT_MS = 20000;
const SCREENCAST_QUALITY = 90;
const SETTLE_POLL_MS = 250, SETTLE_CAP_MS = 2500, SETTLE_MIN_MS = 300;
export const TRACKER_BLOCKLIST = ["*posthog*", "*googletagmanager*", "*google-analytics*", "*plausible.io*", "*segment.io*", "*mixpanel*", "*hotjar*", "*clarity.ms*"];
export const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

export async function open({ chromePath = process.env.CHROME_PATH || DEFAULT_CHROME, flags = (process.env.CHROME_FLAGS || "").split(/\s+/).filter(Boolean) } = {}) {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), "pw-cdp-"));
  const chrome = spawn(chromePath, ["--headless=new", "--remote-debugging-port=0", "--remote-allow-origins=*", `--user-data-dir=${dir}`, "--no-first-run",
    "--no-default-browser-check", "--hide-scrollbars", "--enable-webgl", "--ignore-gpu-blocklist", ...flags, "about:blank"], { stdio: "ignore" });
  let port;
  for (let i = 0; i < BOOT_POLLS && !port; i++) { await sleep(BOOT_POLL_MS); try { port = fs.readFileSync(path.join(dir, "DevToolsActivePort"), "utf8").split("\n")[0]; } catch {} }
  if (!port) { chrome.kill(); throw new Error("Chrome did not start (set CHROME_PATH)"); }
  const target = (await (await fetch(`http://127.0.0.1:${port}/json/list`)).json()).find((t) => t.type === "page");
  const sock = new WebSocket(target.webSocketDebuggerUrl);
  await new Promise((r) => (sock.onopen = r));
  let id = 0; const pending = new Map(); const listeners = [];
  sock.onmessage = (m) => { const d = JSON.parse(m.data); if (d.id && pending.has(d.id)) { pending.get(d.id)(d); pending.delete(d.id); } else listeners.forEach((l) => l(d)); };
  const send = (method, params = {}) => new Promise((res, rej) => { const i = ++id; pending.set(i, (d) => (d.error ? rej(new Error(method + ": " + d.error.message)) : res(d.result))); sock.send(JSON.stringify({ id: i, method, params })); });
  const evaluate = async (expr) => { const r = await send("Runtime.evaluate", { expression: expr, awaitPromise: true, returnByValue: true }); if (r.exceptionDetails) throw new Error(r.exceptionDetails.exception?.description || r.exceptionDetails.text); return r.result.value; };
  for (const m of ["Page.enable", "Runtime.enable", "Network.enable"]) await send(m);
  await send("Network.setBlockedURLs", { urls: TRACKER_BLOCKLIST });
  await send("Network.setCacheDisabled", { cacheDisabled: true });
  const api = {
    send, evaluate, on: (fn) => listeners.push(fn), sleep,
    setViewport: async (w, h, mobile) => { await send("Emulation.setDeviceMetricsOverride", { width: w, height: h, deviceScaleFactor: mobile ? 2 : 1, mobile }); await send("Emulation.setTouchEmulationEnabled", { enabled: mobile }); },
    async goto(url) {
      const loaded = new Promise((r) => listeners.push((d) => d.method === "Page.loadEventFired" && r()));
      const nav = await send("Page.navigate", { url });
      if (nav.errorText) throw new Error(`navigation failed (${nav.errorText}): ${url}`);
      await Promise.race([loaded, sleep(LOAD_TIMEOUT_MS)]);
    },
    // screenshot to file; returns sha1 of the pixels (used by settle)
    async shot(file, clip) {
      const b64 = (await send("Page.captureScreenshot", { format: "png", ...(clip ? { clip: { ...clip, scale: 1 } } : {}) })).data;
      if (file) fs.writeFileSync(file, Buffer.from(b64, "base64"));
      return crypto.createHash("sha1").update(b64).digest("hex");
    },
    // wait until two consecutive frames are pixel-identical (damped scroll, morphs, reveals) and CSS animations are done
    async settle() {
      const t0 = Date.now(); await sleep(SETTLE_MIN_MS); let prev = await api.shot(null);
      while (Date.now() - t0 < SETTLE_CAP_MS) { await sleep(SETTLE_POLL_MS); const cur = await api.shot(null); if (cur === prev) return true; prev = cur; }
      return false; // never settled: continuous animation (e.g. a live canvas); the caller keeps the last frame and notes it
    },
    // real-time screencast of the page: resolves to [{ file, t }] (jpeg frames written to dir, t in seconds) after run() finishes
    async screencast(dir, w, h, dpr, run) {
      fs.mkdirSync(dir, { recursive: true }); const frames = [];
      api.on((d) => { if (d.method !== "Page.screencastFrame") return; const n = String(frames.length).padStart(5, "0"), f = path.join(dir, `${n}.jpg`); fs.writeFileSync(f, Buffer.from(d.params.data, "base64")); frames.push({ file: f, t: d.params.metadata.timestamp }); send("Page.screencastFrameAck", { sessionId: d.params.sessionId }).catch(() => {}); });
      await send("Page.startScreencast", { format: "jpeg", quality: SCREENCAST_QUALITY, maxWidth: w * dpr, maxHeight: h * dpr, everyNthFrame: 1 });
      await run(); await send("Page.stopScreencast"); return frames;
    },
    close() { try { sock.close(); } catch {} chrome.kill(); try { fs.rmSync(dir, { recursive: true, force: true }); } catch {} },
  };
  return api;
}
