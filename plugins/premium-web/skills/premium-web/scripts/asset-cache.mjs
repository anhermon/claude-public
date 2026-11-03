#!/usr/bin/env node
// asset-cache.mjs: shared cache for GENERATED imagery, so the same prompt is never generated twice across pieces or rounds.
//   node asset-cache.mjs get <prompt-file> [--provider P] [--size WxH] [--out FILE]
//   node asset-cache.mjs put <key> <file>
//   node asset-cache.mjs key <prompt-file> [--provider P] [--size WxH]     (print the key only)
//   node asset-cache.mjs --selftest | --help
// key = sha256(prompt text + provider + size). Cache dir = $PREMIUM_WEB_ASSET_CACHE (default ~/.cache/premium-web/assets); never inside the plugin.
// get: HIT -> prints the cached path (copies to --out when given), exit 0. MISS -> prints the exact generation instruction for the
//   premium-web-imagery sub-skill and exits 10. This script NEVER calls a provider; the agent generates, then runs `put`.
import crypto from "node:crypto";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";

const DEFAULT_CACHE = path.join(os.homedir(), ".cache", "premium-web", "assets");
const DEFAULT_PROVIDER = "default", DEFAULT_SIZE = "unspecified", EXIT_MISS = 10, EXIT_USAGE = 2, SEP = "\u0000";
const cacheDir = () => process.env.PREMIUM_WEB_ASSET_CACHE || DEFAULT_CACHE;
const HELP = fs.readFileSync(new URL(import.meta.url), "utf8").split("\n").slice(1, 10).map((l) => l.replace(/^\/\/ ?/, "")).join("\n");

export const keyOf = (prompt, provider = DEFAULT_PROVIDER, size = DEFAULT_SIZE) => crypto.createHash("sha256").update([prompt.trim(), provider, size].join(SEP)).digest("hex");
export const find = (key) => { try { const f = fs.readdirSync(cacheDir()).find((n) => n.startsWith(key + ".") && !n.endsWith(".json")); return f && path.join(cacheDir(), f); } catch { return undefined; } };
export function put(key, file, meta = {}) {
  if (!/^[0-9a-f]{64}$/.test(key)) throw new Error("key must be a 64-hex sha256 (use `key` or `get` to obtain it)");
  fs.mkdirSync(cacheDir(), { recursive: true });
  const dst = path.join(cacheDir(), key + path.extname(file).toLowerCase());
  fs.copyFileSync(file, dst); fs.writeFileSync(path.join(cacheDir(), key + ".json"), JSON.stringify({ ...meta, bytes: fs.statSync(dst).size, stored: new Date().toISOString() }, null, 1));
  return dst;
}
const opt = (a, n, d) => (a.includes(n) ? a[a.indexOf(n) + 1] : d);

function main(a) {
  const [cmd, arg1, arg2] = a;
  if (!cmd || cmd === "--help") { console.log(HELP); return cmd ? 0 : EXIT_USAGE; }
  if (cmd === "--selftest") {
    process.env.PREMIUM_WEB_ASSET_CACHE = fs.mkdtempSync(path.join(os.tmpdir(), "pw-ac-"));
    const k = keyOf("a prompt"), t = path.join(process.env.PREMIUM_WEB_ASSET_CACHE, "x.png"); fs.writeFileSync(t, "png");
    const ok = k === keyOf("a prompt\n") && k !== keyOf("a prompt", "codex") && k !== keyOf("a prompt", DEFAULT_PROVIDER, "1x1") && !find(k) && (put(k, t), find(k)?.endsWith(k + ".png"));
    console.log(ok ? "selftest ok" : "selftest FAILED"); fs.rmSync(process.env.PREMIUM_WEB_ASSET_CACHE, { recursive: true, force: true }); return ok ? 0 : 1;
  }
  if (cmd === "put") { if (!arg1 || !arg2 || !fs.existsSync(arg2)) { console.error(HELP); return EXIT_USAGE; } console.log(put(arg1, arg2, { provider: opt(a, "--provider"), size: opt(a, "--size") })); return 0; }
  if (cmd === "key" || cmd === "get") {
    if (!arg1 || !fs.existsSync(arg1)) { console.error("prompt file not found\n" + HELP); return EXIT_USAGE; }
    const provider = opt(a, "--provider", DEFAULT_PROVIDER), size = opt(a, "--size", DEFAULT_SIZE), key = keyOf(fs.readFileSync(arg1, "utf8"), provider, size);
    if (cmd === "key") { console.log(key); return 0; }
    const hit = find(key), out = opt(a, "--out");
    if (hit) { if (out) fs.copyFileSync(hit, out); console.log(out || hit); return 0; }
    console.log(`MISS ${key}\nGenerate it ONCE with the premium-web-imagery sub-skill (provider ${provider}, size ${size}) from the prompt in ${path.resolve(arg1)}, then register it:\n  node ${path.relative(process.cwd(), process.argv[1]) || "asset-cache.mjs"} put ${key} <generated-file> --provider ${provider} --size ${size}\nand re-run get${out ? "" : " (with --out to place it in the piece)"}.`);
    return EXIT_MISS;
  }
  console.error(HELP); return EXIT_USAGE;
}
process.exit(main(process.argv.slice(2)));
