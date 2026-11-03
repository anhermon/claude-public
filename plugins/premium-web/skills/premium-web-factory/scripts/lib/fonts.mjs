// Fonts are the one network step: premium-web/scripts/get-font.sh fetches open-licence woff2 files into <out>/fonts/.
// Results are cached in <out>/fonts/fonts.json + fonts.css; an existing cache is reused so regeneration is offline and stable.
import fs from 'node:fs';
import path from 'node:path';
import { execFileSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
export const GET_FONT = path.join(HERE, '..', '..', '..', 'premium-web', 'scripts', 'get-font.sh');
const FETCH_TIMEOUT_MS = 90000, DISPLAY_HEAVY = 700;   // heavy static weight for the wordmark when the font is not variable
const FAMILY_RE = /font-family:\s*"([^"]+)"/;
const FILE_RE = /url\("([^"]+)"\)/g;

/** Returns { css, files, byId } or null (offline / skipped). Never throws: a missing font degrades to the fallback stack. */
export function ensureFonts(outDir, piece, { fetchFonts, warn }) {
  const dir = path.join(outDir, 'fonts'), jsonP = path.join(dir, 'fonts.json'), cssP = path.join(dir, 'fonts.css');
  if (fs.existsSync(jsonP) && fs.existsSync(cssP)) return { ...JSON.parse(fs.readFileSync(jsonP, 'utf8')), css: fs.readFileSync(cssP, 'utf8') };
  if (!fetchFonts) return null;
  if (!fs.existsSync(GET_FONT)) { warn(`get-font.sh not found at ${GET_FONT}; using fallback stacks`); return null; }
  const byId = {}, cssParts = [], files = [];
  const wanted = new Map();
  for (const role of ['display', 'body', 'mono']) {
    const f = piece.fonts[role];
    if (role === 'mono' && f.mono) continue;
    if (!wanted.has(f.id)) wanted.set(f.id, new Set());
    wanted.get(f.id).add(f.weight || 400); wanted.get(f.id).add(400); if (role === 'display') wanted.get(f.id).add(DISPLAY_HEAVY);
  }
  fs.mkdirSync(dir, { recursive: true });
  for (const [id, weights] of wanted) {
    try {
      const out = execFileSync('bash', [GET_FONT, id, dir, [...weights].sort((a, b) => a - b).join(',')], { encoding: 'utf8', timeout: FETCH_TIMEOUT_MS, stdio: ['ignore', 'pipe', 'ignore'] });
      const fam = (out.match(FAMILY_RE) || [])[1];
      const got = [...out.matchAll(FILE_RE)].map((m) => m[1]);
      if (!fam || !got.length) { warn(`font ${id}: no @font-face produced`); continue; }
      byId[id] = { family: fam, files: got }; cssParts.push(out.trim()); files.push(...got);
    } catch (e) { warn(`font ${id}: fetch failed (${String(e.message).split('\n')[0]}); using fallback stack`); }
  }
  if (!files.length) return null;
  const res = { byId, files };
  fs.writeFileSync(jsonP, JSON.stringify(res, null, 2) + '\n');
  fs.writeFileSync(cssP, cssParts.join('\n') + '\n');
  return { ...res, css: cssParts.join('\n') };
}

/** Apply fetched family names + preload list to the piece (mutates). */
export function applyFonts(piece, fonts) {
  if (!fonts) return;
  for (const role of ['display', 'body', 'mono']) {
    const hit = fonts.byId[piece.fonts[role].id];
    if (hit) piece.fonts[role].family = hit.family;
  }
  piece.fontFiles = fonts.files.filter((f) => /wght-normal|-400-normal/.test(f)).slice(0, 2);
  piece.hasFontCss = true;
}
