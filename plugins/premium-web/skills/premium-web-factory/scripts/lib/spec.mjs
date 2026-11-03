// Spec loading, schema validation (tiny JSON-schema subset, no dependencies) and normalisation into the PIECE config.
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { ARCHETYPES } from '../../archetypes/index.mjs';
import { SUBJECT_DEFAULTS, DEFAULT_PLACE, MOBILE_MAX_W_DEFAULT, DEFAULT_BUDGETS, WORLD_STOPS } from './const.mjs';

const HERE = path.dirname(fileURLToPath(import.meta.url));
export const SCHEMA_PATH = path.join(HERE, '..', '..', 'spec.schema.json');

/** Validate `v` against `schema`; returns an array of "path: message" strings. */
export function validate(v, schema, root = schema, at = '$') {
  const errs = [];
  if (schema.$ref) return validate(v, schema.$ref.split('/').slice(1).reduce((s, k) => s[k], root), root, at);
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
  if (tn === 'object' && schema.properties) {
    for (const k of schema.required || []) if (!(k in v)) errs.push(`${at}: missing "${k}"`);
    for (const k of Object.keys(v)) {
      if (schema.properties[k]) errs.push(...validate(v[k], schema.properties[k], root, `${at}.${k}`));
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
  const warnings = [];
  const ids = new Set();
  (spec.chapters || []).forEach((c, i) => {
    if (ids.has(c.id)) errs.push(`chapters[${i}]: duplicate id "${c.id}"`);
    ids.add(c.id);
    const a = ARCHETYPES[c.archetype];
    if (!a) return;
    for (const k of a.meta.copyRequired) if (c.copy?.[k] == null) errs.push(`chapters[${i}] (${c.archetype}).copy: missing "${k}"`);
    if (a.meta.needsTarget && !c.target) errs.push(`chapters[${i}] (${c.archetype}): needs a "target" layout`);
    if (a.meta.needsCommerce && !spec.commerce) errs.push(`chapters[${i}] (${c.archetype}): needs top-level "commerce"`);
  });
  if (spec.chapters && spec.chapters[0]?.archetype !== 'hero') errs.push('chapters[0]: must be the hero archetype');
  if (spec.subject?.kind === 'custom-module' && !spec.subject.module) errs.push('subject.module is required for custom-module');
  if (spec.subject?.kind === 'shader-field' && (spec.subject.items ?? SUBJECT_DEFAULTS['shader-field'].items) > SHADER_MAX_ITEMS) errs.push(`subject.items: shader-field supports at most ${SHADER_MAX_ITEMS} wells`);
  if (errs.length) throw new Error('spec invalid:\n  ' + errs.join('\n  '));
  return { spec, ...normalise(spec, warnings), warnings };
}

function normalise(spec, warnings) {
  const kind = spec.subject.kind, sd = SUBJECT_DEFAULTS[kind] || SUBJECT_DEFAULTS['glass-lattice'];
  const items = spec.subject.items ?? sd.items;
  const slug = spec.slug || spec.name.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
  const pal = spec.direction.palette;
  const palette = { ...pal, accentText: pal.accentText || pal.accent, light: merge({ ground: '#e6ecea', ink: '#0b1218', inkSoft: '#3d5361', accentText: pal.accent }, pal.light) };
  // acts: chapters with a target, in order; others hold the previous act
  let act = -1;
  const chapters = spec.chapters.map((c, i) => {
    if (c.target) act += 1;
    const place = merge(DEFAULT_PLACE, c.place);
    const textSide = place.desktop === 'left' ? 'right' : place.desktop === 'right' ? 'left' : 'center';
    return { ...c, index: i, act: Math.max(act, 0), hasTarget: !!c.target, place, textSide, copy: c.copy || {}, params: merge(ARCHETYPES[c.archetype].meta.params, c.params) };
  });
  const nActs = act + 1;
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
    subject: { kind, items, count: spec.subject.count ?? sd.count, seed: spec.subject.seed ?? sd.seed, params: merge(sd.params, spec.subject.params), wordmark: spec.subject.wordmark !== false, module: spec.subject.module },
    interaction: merge({ title: 'Nearest to your cursor', unit: '', names: [], groups: [], scanLabel: 'items scanned in', footnote: '' }, spec.interaction),
    commerce: spec.commerce ? merge({ currency: '$' }, spec.commerce) : null,
    chapters, worlds, nActs,
    assets: spec.assets?.plan || [],
    budgets: merge(DEFAULT_BUDGETS, spec.budgets),
    mobileMaxW: spec.budgets?.mobileMaxWidth ?? MOBILE_MAX_W_DEFAULT,
  };
  return { piece };
}
