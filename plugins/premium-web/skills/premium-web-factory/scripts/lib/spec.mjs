// Spec loading, schema validation (tiny JSON-schema subset, no dependencies) and normalisation into the PIECE config.
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { ARCHETYPES } from '../../archetypes/index.mjs';
import { SUBJECT_DEFAULTS, DEFAULT_PLACE, MOBILE_MAX_W_DEFAULT, DEFAULT_BUDGETS, WORLD_STOPS, GRAMMAR_MORPH, GRAMMAR_RAIL, HERO_DEFAULTS, SCROLL_DEFAULTS, READOUT_DEFAULT, RAIL_DEFAULTS, MORPH_MIN_CHAPTERS } from './const.mjs';

const HERE = path.dirname(fileURLToPath(import.meta.url));
export const SCHEMA_PATH = path.join(HERE, '..', '..', 'spec.schema.json');

/** Validate `v` against `schema`; returns an array of "path: message" strings. */
export function validate(v, schema, root = schema, at = '$') {
  const errs = [];
  if (schema.$ref) return validate(v, schema.$ref.split('/').slice(1).reduce((s, k) => s[k], root), root, at);
  for (const s of schema.allOf || []) errs.push(...validate(v, s, root, at));
  if (schema.if) {
    const branch = validate(v, schema.if, root, at).length ? schema.else : schema.then;
    if (branch) errs.push(...validate(v, branch, root, at));
  }
  if ('const' in schema && v !== schema.const) errs.push(`${at}: expected ${JSON.stringify(schema.const)}`);
  const t = schema.type;
  const tn = Array.isArray(v) ? 'array' : v === null ? 'null' : typeof v;
  if (t && !(t === tn || (t === 'integer' && Number.isInteger(v)) || (t === 'number' && tn === 'number'))) return [`${at}: expected ${t}, got ${tn}`];
  if (schema.enum && !schema.enum.includes(v)) errs.push(`${at}: ${JSON.stringify(v)} not in [${schema.enum.join(', ')}]`);
  if (typeof v === 'string') {
    if (schema.pattern && !new RegExp(schema.pattern).test(v)) errs.push(`${at}: does not match ${schema.pattern}`);
    if (schema.minLength && v.length < schema.minLength) errs.push(`${at}: shorter than ${schema.minLength}`);
  }
  if (typeof v === 'number') {
    if (schema.minimum != null && v < schema.minimum) errs.push(`${at}: below ${schema.minimum}`);
    if (schema.maximum != null && v > schema.maximum) errs.push(`${at}: above ${schema.maximum}`);
  }
  if (Array.isArray(v)) {
    if (schema.minItems && v.length < schema.minItems) errs.push(`${at}: needs >= ${schema.minItems} items`);
    if (schema.maxItems && v.length > schema.maxItems) errs.push(`${at}: needs <= ${schema.maxItems} items`);
    if (schema.items) v.forEach((x, i) => errs.push(...validate(x, schema.items, root, `${at}[${i}]`)));
  }
  if (tn === 'object') {
    for (const k of schema.required || []) if (!(k in v)) errs.push(`${at}: missing "${k}"`);
    for (const k of Object.keys(v)) {
      if (schema.properties?.[k]) errs.push(...validate(v[k], schema.properties[k], root, `${at}.${k}`));
      else if (schema.additionalProperties === false) errs.push(`${at}: unknown key "${k}"`);
    }
  }
  return errs;
}

const SHADER_MAX_ITEMS = 64;   // = MAX_WELLS in runtime/subjects/shader-field.js (GLSL uniform array size)
const merge = (d, o) => ({ ...d, ...(o || {}) });
const titleCase = (s) => s.split('-').map((w) => w[0].toUpperCase() + w.slice(1)).join(' ');
const FONT_FALLBACK = { display: 'sans-serif', body: 'sans-serif', mono: 'monospace' };

/** Read, validate and normalise. Throws Error with all problems listed. Returns { spec, piece, warnings }. */
export function loadSpec(file) {
  const spec = JSON.parse(fs.readFileSync(file, 'utf8'));
  const schema = JSON.parse(fs.readFileSync(SCHEMA_PATH, 'utf8'));
  const errs = validate(spec, schema);
  if (errs.length) throw new Error('spec invalid:\n  ' + errs.join('\n  '));
  const rail = spec.grammar === GRAMMAR_RAIL;
  const warnings = [];
  const ids = new Set();
  (spec.chapters || []).forEach((c, i) => {
    if (ids.has(c.id)) errs.push(`chapters[${i}]: duplicate id "${c.id}"`);
    ids.add(c.id);
    const a = ARCHETYPES[c.archetype];
    if (!a) return;
    for (const k of a.meta.copyRequired) if (c.copy?.[k] == null) errs.push(`chapters[${i}] (${c.archetype}).copy: missing "${k}"`);
    if (!rail && a.meta.needsTarget && !c.target) errs.push(`chapters[${i}] (${c.archetype}): needs a "target" layout`);
    if (a.meta.needsCommerce && !spec.commerce) errs.push(`chapters[${i}] (${c.archetype}): needs top-level "commerce"`);
    if (rail && !['pricing', 'faq'].includes(c.archetype)) errs.push(`chapters[${i}]: rail accepts only pricing and faq after its panels`);
  });
  if (!rail && spec.chapters?.length < MORPH_MIN_CHAPTERS) errs.push(`chapters: needs >= ${MORPH_MIN_CHAPTERS} items`);
  if (!rail && spec.chapters && spec.chapters[0]?.archetype !== 'hero') errs.push('chapters[0]: must be the hero archetype');
  if (!rail && spec.rail) errs.push('rail: only valid for grammar rail');
  if (rail) {
    for (const k of ['subject', 'hero', 'readout', 'scroll']) if (spec[k]) errs.push(`${k}: not used by grammar rail; omit it`);
    spec.rail.panels.forEach((p, i) => {
      if (ids.has(p.id)) errs.push(`rail.panels[${i}]: duplicate id "${p.id}"`);
      ids.add(p.id);
      if (['timeline', 'diagram'].includes(p.figure.kind) && !p.figure.items) errs.push(`rail.panels[${i}].figure: ${p.figure.kind} needs items`);
      if (p.figure.kind === 'stat' && !p.figure.value) errs.push(`rail.panels[${i}].figure: stat needs value`);
    });
  }
  if (spec.subject?.kind === 'custom-module' && !spec.subject.module) errs.push('subject.module is required for custom-module');
  if (spec.subject?.kind === 'shader-field' && (spec.subject.items ?? SUBJECT_DEFAULTS['shader-field'].items) > SHADER_MAX_ITEMS) errs.push(`subject.items: shader-field supports at most ${SHADER_MAX_ITEMS} wells`);
  if (errs.length) throw new Error('spec invalid:\n  ' + errs.join('\n  '));
  return { spec, ...normalise(spec, warnings), warnings };
}

function normalise(spec, warnings) {
  const rail = spec.grammar === GRAMMAR_RAIL, subject = spec.subject || { kind: 'none' };
  const kind = subject.kind, sd = SUBJECT_DEFAULTS[kind] || SUBJECT_DEFAULTS['glass-lattice'];
  const items = subject.items ?? sd.items;
  const slug = spec.slug || spec.name.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
  const pal = spec.direction.palette;
  const palette = { ...pal, accentText: pal.accentText || pal.accent, light: merge({ ground: '#e6ecea', ink: '#0b1218', inkSoft: '#3d5361', accentText: pal.accent }, pal.light) };
  // acts: chapters with a target, in order; others hold the previous act
  let act = -1;
  const chapters = (spec.chapters || []).map((c, i) => {
    if (c.target || rail) act += 1;
    const place = merge(DEFAULT_PLACE, c.place);
    const textSide = place.desktop === 'left' ? 'right' : place.desktop === 'right' ? 'left' : 'center';
    return { ...c, index: i, act: Math.max(act, 0), hasTarget: !!c.target, place, textSide, copy: c.copy || {}, params: merge(ARCHETYPES[c.archetype].meta.params, c.params) };
  });
  const nActs = rail ? spec.rail.panels.length + chapters.length : act + 1;
  if (spec.direction.ground.length < nActs) warnings.push(`ground has ${spec.direction.ground.length} entries for ${nActs} acts: last entry repeats`);
  const worlds = Array.from({ length: nActs }, (_, k) => spec.direction.ground[Math.min(k, spec.direction.ground.length - 1)]).map((g) => ({
    base: g.base, accent: g.accent || palette.accent, grain: g.light ? 0.04 : 0.05, light: !!g.light,
    glows: [{ at: g.glow.at || [0.5, 1.0], radius: g.glow.radius || [0.9, 0.6], stops: WORLD_STOPS.map((p, j) => [p, j < 3 ? g.glow.colors[j] : g.base]) }],
    x: { dust: g.light ? 0 : 1, halo: g.light ? 0.15 : 1, key: g.light ? 0.85 : 1 },
  }));
  const fonts = {};
  for (const role of ['display', 'body', 'mono']) {
    const f = spec.direction.fonts[role] || (role === 'mono' ? { id: spec.direction.fonts.body.id } : null);
    fonts[role] = { ...f, family: f.family || titleCase(f.id), fallback: f.fallback || FONT_FALLBACK[role], mono: role === 'mono' && !spec.direction.fonts.mono };
  }
  const piece = {
    name: spec.name, slug, lang: spec.lang || 'en', wordmark: spec.name.toUpperCase(),
    concept: { ...spec.concept, noticeShort: spec.concept.noticeShort || spec.concept.notice.split(/\s+/).slice(0, 3).join(' ') },
    palette, fonts,
    subject: { kind, items, count: subject.count ?? sd.count, seed: subject.seed ?? sd.seed, params: merge(sd.params, subject.params), wordmark: subject.wordmark !== false, module: subject.module },
    interaction: merge({ title: 'Nearest to your cursor', unit: '', names: [], groups: [], scanLabel: 'items scanned in', footnote: '' }, spec.interaction),
    commerce: spec.commerce ? merge({ currency: '$' }, spec.commerce) : null,
    chapters, worlds, nActs,
    assets: spec.assets?.plan || [],
    budgets: merge(DEFAULT_BUDGETS, spec.budgets),
    mobileMaxW: spec.budgets?.mobileMaxWidth ?? MOBILE_MAX_W_DEFAULT,
  };
  // Omitted grammar stays non-enumerable: legacy client config and manifest bytes remain identical.
  Object.defineProperty(piece, 'grammar', { value: spec.grammar || GRAMMAR_MORPH, enumerable: !!spec.grammar });
  if (spec.hero || spec.scroll || spec.readout) {
    piece.hero = merge({ ...HERO_DEFAULTS, wordmark: subject.wordmark !== false }, spec.hero);
    piece.scroll = merge(SCROLL_DEFAULTS, spec.scroll);
    piece.readout = piece.hero.layout === 'type-only' ? 'none' : spec.readout || READOUT_DEFAULT;
    piece.subject.wordmark = piece.hero.wordmark;
    if (piece.scroll.mode === 'static') {
      const firstPlace = chapters[0].place;
      for (const ch of chapters.slice(1)) {
        ch.place = { ...firstPlace };
        ch.textSide = firstPlace.desktop === 'left' ? 'right' : 'left';
      }
    }
  }
  if (rail) {
    delete piece.subject;
    piece.rail = { panels: spec.rail.panels, params: merge(RAIL_DEFAULTS, spec.rail.params) };
  }
  return { piece };
}
