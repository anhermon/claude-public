// Selftest for new-piece.mjs: generate the documented example into a temp dir and check the write-policy contracts.
// Offline (no font fetch). Exit code 0 = all checks passed.
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { generate } from './new-piece.mjs';
import { sha } from './lib/manifest.mjs';
import { MANIFEST_FILE } from './lib/const.mjs';
import { grammarSelftest } from './grammar-selftest.mjs';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const EXAMPLE = path.join(HERE, '..', 'example.spec.json');
const EDIT_TARGET = 'css/sections.css', USER_FILE = 'bespoke/index.js', USER_MARK = '// hand-written bespoke beat';
const OPTS = { fetchFonts: false };

export async function selftest() {
  const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'factory-selftest-'));
  const out = path.join(tmp, 'piece'), failures = [];
  const check = (name, ok, detail = '') => { console.log(`${ok ? 'ok  ' : 'FAIL'} ${name}${ok ? '' : ' ' + detail}`); if (!ok) failures.push(name); };
  const counts = (r) => r.report.reduce((m, [k]) => ({ ...m, [k.split(' ')[0]]: (m[k.split(' ')[0]] || 0) + 1 }), {});
  try {
    const r1 = generate(EXAMPLE, out, OPTS);
    check('first run creates files', counts(r1).created === r1.files, JSON.stringify(counts(r1)));
    const man = JSON.parse(fs.readFileSync(path.join(out, MANIFEST_FILE), 'utf8'));
    const bad = Object.entries(man.files).filter(([rel, f]) => sha(fs.readFileSync(path.join(out, rel))) !== f.sha256).map(([rel]) => rel);
    check('manifest hashes match disk', bad.length === 0 && Object.keys(man.files).length > 10, bad.join(','));
    check('index.html + vendored three present', fs.existsSync(path.join(out, 'index.html')) && fs.existsSync(path.join(out, 'gl', 'vendor', 'three.module.min.js')));
    check('no CDN: no external src/href in html', !/(?:src|href)="https?:/.test(fs.readFileSync(path.join(out, 'index.html'), 'utf8')));

    const r2 = generate(EXAMPLE, out, OPTS), c2 = counts(r2);
    check('second run is idempotent (all unchanged)', c2.unchanged + (c2.kept || 0) === r2.files && !c2.updated && !c2.created, JSON.stringify(c2));

    fs.writeFileSync(path.join(out, USER_FILE), USER_MARK + '\n');
    const r3 = generate(EXAMPLE, out, OPTS);
    check('user-owned bespoke file is never overwritten', fs.readFileSync(path.join(out, USER_FILE), 'utf8').startsWith(USER_MARK) && counts(r3).kept >= 1);

    const edited = path.join(out, EDIT_TARGET), orig = fs.readFileSync(edited, 'utf8');
    fs.writeFileSync(edited, orig + '\n/* hand edit */\n');
    let refused = false;
    try { generate(EXAMPLE, out, OPTS); } catch (e) { refused = /hand-edited/.test(e.message); }
    check('hand-edited generated file is refused', refused && fs.readFileSync(edited, 'utf8').includes('hand edit'));
    generate(EXAMPLE, out, { ...OPTS, force: true });
    check('--force restores the generated file', fs.readFileSync(edited, 'utf8') === orig);

    const pre = path.join(tmp, 'prefetched'); fs.mkdirSync(path.join(pre, 'fonts'), { recursive: true }); fs.writeFileSync(path.join(pre, 'fonts', 'x.woff2'), 'x');
    let fresh = true;
    try { generate(EXAMPLE, pre, OPTS); } catch { fresh = false; }
    check('a fresh dir holding only prefetched fonts/ is accepted', fresh);

    const badSpec = path.join(tmp, 'bad.spec.json'), spec = JSON.parse(fs.readFileSync(EXAMPLE, 'utf8'));
    spec.chapters[1].archetype = 'no-such-archetype';
    fs.writeFileSync(badSpec, JSON.stringify(spec));
    let rejected = false;
    try { generate(badSpec, path.join(tmp, 'bad'), OPTS); } catch { rejected = true; }
    check('invalid spec is rejected', rejected);
    check('deterministic: same spec -> same spec hash', JSON.parse(fs.readFileSync(path.join(out, MANIFEST_FILE), 'utf8')).specHash === man.specHash);
    await grammarSelftest(tmp, check);
  } finally { fs.rmSync(tmp, { recursive: true, force: true }); }
  console.log(failures.length ? `SELFTEST FAILED: ${failures.length} check(s)` : 'SELFTEST OK');
  return failures.length ? 1 : 0;
}
