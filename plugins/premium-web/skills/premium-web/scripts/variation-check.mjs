#!/usr/bin/env node
// Portfolio gate. Reads source specs, never executes a piece's JS.
import fs from 'node:fs';
import path from 'node:path';
import os from 'node:os';
import assert from 'node:assert/strict';
import { fileURLToPath } from 'node:url';

const HUE_LIMIT_DEG = 25, FULL_TURN = 360, HALF_TURN = FULL_TURN / 2;
const CHANNEL_MAX = 255, HEX_RADIX = 16, MIN_CHROMA = 0.08, HUE_SECTOR = FULL_TURN / 6;
const SCORE_MAX = 100, CELL_WIDTH = 9, LABEL_WIDTH = 24, HUE_DIGITS = 1;
const EXIT = { ok: 0, siblings: 1, usage: 2 };
const DEFAULTS = { grammar: 'morph-subject', subject: 'none', layout: 'split', scroll: 'morph', railScroll: 'rail' };
const REASON = { structure: 'same grammar + subject + hero layout + scroll mode', order: 'identical archetype order', hue: 'palette hues within 25° and same font pair' };
const PATHS = ['spec/piece.json', 'spec.json', 'piece.json', 'piece/spec/piece.json'];
const CONFIG_PATHS = ['js/piece.config.js', 'piece/js/piece.config.js'];
const REGISTRY_KEYS = ['pieces', 'entries', 'items'];
const ENTRY_PATHS = ['dir', 'path', 'outDir', 'output', 'spec', 'piece'];
const CONFIG_RE = /export const PIECE = ([\s\S]*);\s*$/;
const HELP = 'usage: node variation-check.mjs <registry.json-or-piece-dir...> | --selftest';
const hueDistance = (a, b) => Math.min(Math.abs(a - b), FULL_TURN - Math.abs(a - b));

function hue(hex) {
  if (!/^#[\da-f]{6}$/i.test(hex || '')) return null;
  const [r, g, b] = [1, 3, 5].map((offset) => parseInt(hex.slice(offset, offset + 2), HEX_RADIX) / CHANNEL_MAX);
  const hi = Math.max(r, g, b), lo = Math.min(r, g, b), delta = hi - lo;
  if (delta < MIN_CHROMA) return null;
  const sector = hi === r ? ((g - b) / delta) % 6 : hi === g ? (b - r) / delta + 2 : (r - g) / delta + 4;
  return (sector * HUE_SECTOR + FULL_TURN) % FULL_TURN;
}

function paletteFingerprint(palette) {
  const colors = [...Object.values(palette || {}), ...Object.values(palette?.light || {})].filter((v) => typeof v === 'string');
  const hues = [...new Set(colors.map(hue).filter((v) => v != null))].sort((a, b) => a - b);
  const gaps = hues.map((v, i) => ((hues[(i + 1) % hues.length] - v + FULL_TURN) % FULL_TURN) || FULL_TURN);
  return { hues, spread: hues.length > 1 ? FULL_TURN - Math.max(...gaps) : 0 };
}

export function fingerprint(spec, label = spec.name) {
  const direction = spec.direction || spec, fonts = direction.fonts;
  if (!spec.name || !direction.palette || !fonts?.display || !fonts?.body) throw new Error(`${label}: missing piece name, palette or font pair`);
  const grammar = spec.grammar || DEFAULTS.grammar, rail = grammar === 'rail';
  if (rail && !spec.rail?.panels?.length) throw new Error(`${label}: rail has no panels`);
  if (!rail && !spec.chapters?.length) throw new Error(`${label}: no chapter order`);
  const font = (f) => (f.id || f.family).toLowerCase().replace(/\s+/g, '-');
  const order = [...(rail ? spec.rail.panels.map((p) => `panel:${p.figure.kind}`) : []), ...(spec.chapters || []).map((c) => c.archetype)];
  return {
    label, grammar, subject: spec.subject?.kind || DEFAULTS.subject,
    heroLayout: spec.hero?.layout || DEFAULTS.layout,
    scrollMode: rail ? DEFAULTS.railScroll : spec.scroll?.mode || DEFAULTS.scroll,
    order, grounds: (direction.ground || spec.worlds || []).map((g) => `${g.base}/${g.accent || direction.palette.accent}/${!!g.light}`),
    palette: paletteFingerprint(direction.palette), fonts: [font(fonts.display), font(fonts.body)],
  };
}

const equal = (a, b) => JSON.stringify(a) === JSON.stringify(b);
function closeHues(a, b) {
  if (!a.length || !b.length) return !a.length && !b.length;
  return a.every((h) => b.some((k) => hueDistance(h, k) <= HUE_LIMIT_DEG)) && b.every((h) => a.some((k) => hueDistance(h, k) <= HUE_LIMIT_DEG));
}

export function compare(a, b) {
  const structure = ['grammar', 'subject', 'heroLayout', 'scrollMode'].map((k) => a[k] === b[k]);
  const order = equal(a.order, b.order), fonts = equal(a.fonts, b.fonts), hues = closeHues(a.palette.hues, b.palette.hues);
  const traits = [...structure, order, equal(a.grounds, b.grounds), hues, fonts];
  const reasons = [];
  if (structure.every(Boolean)) reasons.push(REASON.structure);
  if (order) reasons.push(REASON.order);
  if (hues && fonts) reasons.push(REASON.hue);
  return { score: Math.round(SCORE_MAX * traits.filter(Boolean).length / traits.length), reasons };
}

function parsePiece(file) {
  const text = fs.readFileSync(file, 'utf8');
  return file.endsWith('.js') ? JSON.parse(text.match(CONFIG_RE)?.[1] || 'null') : JSON.parse(text);
}

export function readInputs(inputs) {
  const pieces = [], visited = new Set();
  function read(input, base = process.cwd()) {
    const file = path.resolve(base, input), real = fs.realpathSync(file);
    if (visited.has(real)) return;
    visited.add(real);
    if (fs.statSync(real).isDirectory()) {
      for (const rel of [...PATHS, ...CONFIG_PATHS]) {
        const candidate = path.join(real, rel);
        if (!fs.existsSync(candidate)) continue;
        const spec = parsePiece(candidate);
        if (spec?.direction || spec?.palette) { pieces.push(fingerprint(spec, `${spec.name} (${path.basename(real)})`)); return; }
      }
      throw new Error(`${input}: no factory spec or piece config found`);
    }
    const data = parsePiece(real);
    if (data?.direction || data?.palette) { pieces.push(fingerprint(data)); return; }
    const registry = REGISTRY_KEYS.reduce((found, key) => found || data?.[key], null) || data;
    if (!registry || typeof registry !== 'object') throw new Error(`${input}: expected a piece spec or registry`);
    const entries = Array.isArray(registry) ? registry : Object.values(registry);
    if (!entries.length) throw new Error(`${input}: empty registry`);
    for (const entry of entries) {
      const target = typeof entry === 'string' ? entry : ENTRY_PATHS.map((key) => entry?.[key]).find((v) => typeof v === 'string');
      if (!target) throw new Error(`${input}: registry entry needs a local dir/path/spec`);
      read(target, path.dirname(real));
    }
  }
  inputs.forEach((input) => read(input));
  return pieces;
}

export function matrix(pieces) {
  const rows = [], failures = [];
  rows.push('Similarity % (matching fingerprint traits; X = rejected pair)');
  rows.push(''.padEnd(LABEL_WIDTH) + pieces.map((_, i) => String(i + 1).padStart(CELL_WIDTH)).join(''));
  pieces.forEach((p, i) => {
    rows.push(`${i + 1}. ${p.label}`.slice(0, LABEL_WIDTH).padEnd(LABEL_WIDTH) + pieces.map((q, j) => {
      if (i === j) return '—'.padStart(CELL_WIDTH);
      const result = compare(p, q);
      if (i < j && result.reasons.length) failures.push(`${i + 1} × ${j + 1}: ${result.reasons.join('; ')}`);
      return `${result.score}${result.reasons.length ? ' X' : ''}`.padStart(CELL_WIDTH);
    }).join(''));
    rows.push(`   ${p.grammar}/${p.subject}/${p.heroLayout}/${p.scrollMode}; ${p.order.join(' > ')}; ground ${p.grounds.join(' > ')}; hue spread ${p.palette.spread.toFixed(HUE_DIGITS)}°; fonts ${p.fonts.join(' + ')}`);
  });
  rows.push(...failures, failures.length ? `FAIL: ${failures.length} sibling pair(s)` : `PASS: ${pieces.length} piece(s), no structural siblings`);
  return { output: rows.join('\n'), failures };
}

export function selftest() {
  const TEST = { name: 'Sample', blue: '#3355ff', orange: '#ff8833', nearRed: '#ff0011', red: '#ff1100', neutral: '#101010' };
  const fixture = (accent = TEST.blue) => ({ name: TEST.name, direction: { palette: { ground: TEST.neutral, accent }, fonts: { display: { id: 'alpha' }, body: { id: 'beta' } }, ground: [] }, subject: { kind: 'point-cloud' }, chapters: [{ archetype: 'hero' }, { archetype: 'claim' }] });
  const a = fixture(), b = fixture(TEST.orange); b.hero = { layout: 'stack' }; b.scroll = { mode: 'orbit' }; b.chapters.reverse();
  assert.equal(compare(fingerprint(a), fingerprint(b)).reasons.length, 0);
  assert.ok(compare(fingerprint(a), fingerprint(a)).reasons.includes(REASON.structure));
  const order = { ...b, chapters: a.chapters };
  assert.deepEqual(compare(fingerprint(a), fingerprint(order)).reasons, [REASON.order]);
  const redA = fixture(TEST.nearRed), redB = { ...b, direction: fixture(TEST.red).direction };
  assert.deepEqual(compare(fingerprint(redA), fingerprint(redB)).reasons, [REASON.hue]);
  assert.ok(paletteFingerprint({ accent: TEST.nearRed, other: TEST.red }).spread < HUE_LIMIT_DEG);
  assert.ok(hueDistance(0, FULL_TURN - 1) < HUE_LIMIT_DEG);
  assert.equal(hueDistance(0, HALF_TURN), HALF_TURN);
  assert.throws(() => fingerprint({ name: TEST.name }), /missing/);
  const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'variation-check-'));
  try {
    const specDir = path.join(tmp, 'piece', 'spec'); fs.mkdirSync(specDir, { recursive: true });
    fs.writeFileSync(path.join(specDir, 'piece.json'), JSON.stringify(a));
    fs.writeFileSync(path.join(tmp, 'registry.json'), JSON.stringify({ pieces: [{ dir: 'piece' }] }));
    assert.equal(readInputs([path.join(tmp, 'registry.json')]).length, 1);
    assert.equal(matrix([fingerprint(a), fingerprint(b)]).failures.length, 0);
    assert.equal(matrix([fingerprint(a), fingerprint(a)]).failures.length, 1);
  } finally { fs.rmSync(tmp, { recursive: true, force: true }); }
  console.log('variation-check SELFTEST OK: structure, order, circular hues, fonts, registry, matrix');
  return EXIT.ok;
}

function main(args) {
  if (args.includes('--selftest')) return selftest();
  if (!args.length || args.some((a) => a.startsWith('--'))) { console.error(HELP); return EXIT.usage; }
  try {
    const result = matrix(readInputs(args)); console.log(result.output);
    return result.failures.length ? EXIT.siblings : EXIT.ok;
  } catch (error) { console.error(error.message); return EXIT.usage; }
}
if (process.argv[1] && fs.realpathSync(process.argv[1]) === fileURLToPath(import.meta.url)) process.exitCode = main(process.argv.slice(2));
