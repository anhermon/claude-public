// Write policy: "fix at source, regenerate, diff". Every generated file is hashed in .factory-manifest.json; a regeneration
// overwrites only files that still match their recorded hash, refuses files someone edited (unless --force), and reports
// per file: created | updated | unchanged | kept (user-owned) | stale-removed | REFUSED.
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import { MANIFEST_FILE, FACTORY_VERSION } from './const.mjs';

const FONTS_DIR = 'fonts';

export const sha = (buf) => crypto.createHash('sha256').update(buf).digest('hex');
const readIf = (p) => (fs.existsSync(p) ? fs.readFileSync(p) : null);

/** files: Map<rel, { data: string|Buffer, mode: 'generated'|'copied'|'user'|'external' }> */
export function writePiece(outDir, files, { force = false, dryRun = false, specHash = '' } = {}) {
  const mpath = path.join(outDir, MANIFEST_FILE);
  const old = fs.existsSync(mpath) ? JSON.parse(fs.readFileSync(mpath, 'utf8')) : null;
  const existing = fs.existsSync(outDir) ? fs.readdirSync(outDir).filter((f) => f !== MANIFEST_FILE && f !== FONTS_DIR) : [];   // fonts/ is fetched before the write, so it never counts as foreign content
  const report = [], refused = [];
  if (!old && existing.length && !force) throw new Error(`${outDir} is not empty and has no ${MANIFEST_FILE}; refusing (use --force or pick a new dir)`);

  for (const [rel, f] of files) {
    const abs = path.join(outDir, rel), buf = Buffer.from(f.data), cur = readIf(abs), want = sha(buf), recorded = old?.files?.[rel]?.sha256;
    if (f.mode === 'user') { report.push([cur ? 'kept' : 'created', rel]); continue; }
    if (!cur) { report.push(['created', rel]); continue; }
    const curHash = sha(cur);
    if (curHash === want) { report.push(['unchanged', rel]); continue; }
    if (f.mode === 'external') { report.push(['kept', rel]); continue; }
    if (recorded && curHash !== recorded && !force) { refused.push(rel); report.push(['REFUSED (hand-edited)', rel]); continue; }
    report.push(['updated', rel]);
  }
  const stale = Object.keys(old?.files || {}).filter((r) => !files.has(r));
  for (const rel of stale) {
    const abs = path.join(outDir, rel), cur = readIf(abs);
    if (!cur) continue;
    if (sha(cur) === old.files[rel].sha256 || force) report.push(['stale-removed', rel]); else report.push(['stale-kept (hand-edited)', rel]);
  }
  if (refused.length) throw Object.assign(new Error(`refusing to overwrite hand-edited files (fix the spec/factory, or pass --force):\n  ${refused.join('\n  ')}`), { report });
  if (dryRun) return report;

  for (const [rel, f] of files) {
    const abs = path.join(outDir, rel), r = report.find((x) => x[1] === rel)[0];
    if (r === 'unchanged' || r === 'kept') continue;
    fs.mkdirSync(path.dirname(abs), { recursive: true });
    fs.writeFileSync(abs, f.data);
  }
  for (const [what, rel] of report) if (what === 'stale-removed') fs.rmSync(path.join(outDir, rel), { force: true });
  const manifest = { factory: FACTORY_VERSION, specHash, files: {} };
  for (const [rel, f] of [...files].sort((a, b) => a[0].localeCompare(b[0]))) {
    if (f.mode === 'user') continue;
    manifest.files[rel] = { sha256: sha(fs.readFileSync(path.join(outDir, rel))), mode: f.mode };
  }
  fs.mkdirSync(outDir, { recursive: true });
  fs.writeFileSync(mpath, JSON.stringify(manifest, null, 2) + '\n');
  return report;
}
