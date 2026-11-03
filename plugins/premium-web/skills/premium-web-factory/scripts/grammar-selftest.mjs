// Offline grammar checks. Mock DOM tests exercise the actual emitted controllers; no browser is launched.
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import vm from 'node:vm';
import assert from 'node:assert/strict';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { generate, buildFiles } from './new-piece.mjs';
import { loadSpec } from './lib/spec.mjs';
import { codeOnlySelftest } from './code-only-selftest.mjs';

const ROOT = path.join(path.dirname(fileURLToPath(import.meta.url)), '..');
const PROOFS = path.join(ROOT, '.proofs'), RUNTIME = path.join(ROOT, 'runtime');
const LEGACY_SHA = '0d593e3c1f5f24a046bb5982e7273bd9fd7647efa2513571d727ab92914ab932';
const EXAMPLE = path.join(ROOT, 'example.spec.json'), INDEX = 'index.html', SECTIONS = 'css/sections.css';
const LAYOUTS = ['split', 'stack', 'bleed', 'type-only'], MODES = ['morph', 'orbit', 'static'], READOUTS = ['card', 'inline', 'none'];
const TEST = { width: 1440, height: 900, mobile: 390, maxFrames: 1024, half: 0.5, overflow: 200, baseCost: '$5', bestCost: '$30', manualCost: '$65', usage: 40 };
const OFFLINE = { fetchFonts: false };
const CAMERA_TEST = { halfHeight: 5, aspect: 1.6, fov: 40, distance: 12, dt: 1 / 60, time: 10, act: 1.5 };
const walk = (dir) => fs.readdirSync(dir, { withFileTypes: true }).flatMap((e) => e.isDirectory() ? walk(path.join(dir, e.name)) : [path.join(dir, e.name)]);
const source = (rel) => fs.readFileSync(path.join(RUNTIME, rel), 'utf8');
const executable = (text) => text.replace(/^import .*;\n/gm, '').replace(/^export \{[^;]+;\n/gm, '').replace(/^export /gm, '');
const readProof = (name) => JSON.parse(fs.readFileSync(path.join(PROOFS, name, 'spec.json'), 'utf8'));

function legacyHash(dir) {
  const hash = crypto.createHash('sha256');
  for (const file of walk(dir).sort((a, b) => path.relative(dir, a).localeCompare(path.relative(dir, b)))) hash.update(path.relative(dir, file) + '\0').update(fs.readFileSync(file));
  return hash.digest('hex');
}

function style() { return { setProperty(key, value) { this[key] = String(value); } }; }
function node() {
  const events = {}, classes = new Set(), attrs = {};
  return {
    style: style(), events, attrs, dataset: {},
    addEventListener(event, callback) { events[event] = callback; },
    setAttribute(key, value) { attrs[key] = value; },
    classList: { add(c) { classes.add(c); }, remove(c) { classes.delete(c); }, contains(c) { return classes.has(c); }, toggle(c, on) { on ? classes.add(c) : classes.delete(c); } },
  };
}

async function mockRail(piece) {
  const state = { width: TEST.width, height: TEST.height, scroll: 0, overflow: false, time: 0, nextFrame: 1 };
  const frames = new Map(), events = {}, media = { matches: false, addEventListener() {} };
  const root = { ...node(), dataset: {} }, viewport = node(), track = node(), contours = node(), count = node();
  const panels = piece.rail.panels.map((p, i) => {
    const panel = node(), figure = node(), letters = [node(), node()]; panel.id = p.id;
    panel.querySelector = () => figure; panel.querySelectorAll = () => letters;
    Object.defineProperty(panel, 'scrollHeight', { get: () => state.height + (state.overflow ? TEST.overflow : 0) });
    Object.defineProperty(panel, 'offsetLeft', { get: () => i * state.width });
    panel.getBoundingClientRect = () => ({ top: (rail.classList.contains('is-pinned') ? 0 : i * state.height) - state.scroll });
    return panel;
  });
  const rail = node(); rail.getBoundingClientRect = () => ({ top: -state.scroll });
  Object.defineProperty(rail, 'scrollHeight', { get: () => state.height * panels.length });
  rail.querySelector = (sel) => ({ '.rail-viewport': viewport, '.rail-track': track, '[data-contours]': contours, '[data-panel-count]': count })[sel];
  track.querySelectorAll = () => panels;
  Object.defineProperty(track, 'scrollWidth', { get: () => state.width * panels.length });
  const links = panels.map((p) => ({ ...node(), hash: '#' + p.id, getAttribute() { return this.hash; } }));
  const document = { documentElement: root, fonts: { ready: Promise.resolve() }, querySelector: () => rail, querySelectorAll: () => links };
  const context = {
    document, window: {}, location: { search: '', hash: '' }, history: { replaceState() {} }, console, URLSearchParams,
    matchMedia: () => media, addEventListener: (event, fn) => { events[event] = fn; },
    requestAnimationFrame: (fn) => { const id = state.nextFrame++; frames.set(id, fn); return id; },
    cancelAnimationFrame: (id) => frames.delete(id), scrollTo: ({ top }) => { state.scroll = top; events.scroll?.(); },
  };
  for (const [key, field] of [['innerWidth', 'width'], ['innerHeight', 'height'], ['scrollY', 'scroll']]) Object.defineProperty(context, key, { get: () => state[field] });
  const boot = vm.runInNewContext(executable(source('grammars/rail/scroll.js')) + '\n' + executable(source('grammars/rail/boot.js')) + '\nboot;', context);
  const drain = () => {
    let n = 0;
    while (frames.size) {
      assert.ok(n++ < TEST.maxFrames, 'rail settles within the frame budget');
      const [id, callback] = frames.entries().next().value; frames.delete(id); state.time += 1000 / 60; callback(state.time);
    }
  };
  boot({ ...piece, chapters: [] }, {}, () => {}); await Promise.resolve(); drain();
  assert.equal(context.window.__piece.rail.pinned, true);
  const travel = state.width * (panels.length - 1);
  assert.equal(rail.style.height, `${state.height + travel * piece.rail.params.scrollRatio}px`);
  state.scroll = travel * piece.rail.params.scrollRatio * TEST.half; events.scroll();
  const [id, callback] = frames.entries().next().value; frames.delete(id); state.time += 1000 / 60; callback(state.time);
  const letter = panels[0].querySelectorAll()[0], skew = +letter.style.transform.match(/skewX\(([-\d.]+)/)[1];
  assert.ok(Math.abs(skew) <= piece.rail.params.velocityMax * 5 && Math.abs(skew) > 0);
  drain();
  assert.equal(track.style.transform, `translate3d(${-travel * TEST.half}px,0,0)`);
  assert.equal(viewport.style['--rail-progress'], String(TEST.half));
  let prevented = false; links[1].events.click({ preventDefault() { prevented = true; } }); drain();
  assert.equal(prevented, true); assert.equal(state.scroll, state.width * piece.rail.params.scrollRatio);
  state.scroll = travel * piece.rail.params.scrollRatio + TEST.height; events.scroll(); drain();
  assert.equal(viewport.style['--rail-progress'], '1');
  state.width = TEST.mobile; events.resize(); drain();
  assert.equal(context.window.__piece.rail.pinned, false); assert.equal(track.style.transform, ''); assert.equal(rail.style.height, '');
  assert.deepEqual(panels.map((p) => p.id), piece.rail.panels.map((p) => p.id));
  state.width = TEST.width; media.matches = true; events.resize(); drain();
  assert.equal(context.window.__piece.rail.pinned, false);
  media.matches = false; state.overflow = true; events.resize(); drain();
  assert.equal(context.window.__piece.rail.pinned, false);
}

function mockPricing() {
  const input = { ...node(), value: 10 }, output = node(), total = node(), line = node();
  const rows = [node(), node()];
  rows.forEach((r) => { r.parts = { cost: node(), bar: node(), note: node() }; r.querySelector = (selector) => r.parts[selector.match(/role=(\w+)/)[1]]; });
  const parts = { 'in-a': input, 'out-a': output, total, line };
  const el = { querySelector: (selector) => parts[selector.match(/role=([^\]]+)/)[1]], querySelectorAll: () => rows };
  const subject = { M: 1, setDrive() {}, setHover() {}, setCustom() {} };
  const piece = { commerce: { currency: '$', inputs: [{ id: 'a', min: 0, max: 100 }], tiers: [
    { name: 'Starter', fixed: 5, included: { a: 10 }, rates: { a: 2 }, cap: { a: 50 } },
    { name: 'Pro', fixed: 30, included: { a: 100 }, rates: { a: 0 } },
  ] } };
  const math = executable(source('grammars/rail/scroll.js')), utils = executable(source('grammars/rail/util.js')).replace(/^export \{.*$/gm, '');
  const mount = vm.runInNewContext(math + '\n' + utils + '\n' + executable(source('archetypes/pricing.js')) + '\nmount;');
  mount(el, { subject, piece }); assert.equal(total.textContent, TEST.baseCost);
  input.value = TEST.usage; input.events.input(); assert.equal(total.textContent, TEST.bestCost);
  assert.equal(rows[1].attrs['aria-checked'], 'true');
  rows[0].onclick(); assert.equal(total.textContent, TEST.manualCost);
}

function mockSubject(piece) {
  const fakeCore = ({ piece: composed }) => ({
    forms: composed.chapters.filter((c) => c.hasTarget).map((c) => c.target),
    keys: composed.chapters.filter((c) => c.hasTarget).map((c) => ({ at: [0, 0], ...c.place })),
    st: { act: 1 }, view: () => ({}), frame: () => ({ i0: 1, t: TEST.half }),
  });
  const createCore = vm.runInNewContext(executable(source('grammars/morph-subject/core.js')) + '\ncreateCore;', { originalCore: fakeCore });
  const core = createCore({ piece, mobile: false, N: piece.subject.items });
  assert.ok(core.forms.every((f) => f === core.forms[0]));
  assert.equal(core.frame({}, {}).t, 0);
  if (piece.scroll.mode === 'static') assert.ok(core.keys.every((k) => k === core.keys[0]));
  else {
    const camera = { position: { length: () => 12 }, lookAt() {} };
    core.view(camera); assert.ok(camera.position.x > 0);
  }
}

export async function grammarSelftest(tmp, check) {
  await codeOnlySelftest(tmp, check);
  async function test(label, fn) {
    try { await fn(); check(label, true); } catch (error) { check(label, false, error.message); }
  }
  const specFile = path.join(tmp, 'grammar.spec.json');
  const load = (spec) => { fs.writeFileSync(specFile, JSON.stringify(spec)); return loadSpec(specFile).piece; };
  await test('legacy example golden: every output byte remains unchanged', () => {
    const out = path.join(tmp, 'legacy-golden'); generate(EXAMPLE, out, OFFLINE); assert.equal(legacyHash(out), LEGACY_SHA);
  });
  await test('grammar validation: defaults, enums, cross-grammar fields and panel figures', () => {
    const legacy = JSON.parse(fs.readFileSync(EXAMPLE, 'utf8'));
    assert.equal(load(legacy).grammar, 'morph-subject');
    for (const value of ['unknown', false, {}]) assert.throws(() => load({ ...legacy, grammar: value }), /spec invalid/);
    assert.throws(() => load({ ...legacy, hero: { layout: 'unknown' } }), /spec invalid/);
    assert.throws(() => load({ ...legacy, scroll: { mode: 'unknown' } }), /spec invalid/);
    assert.throws(() => load({ ...legacy, readout: 'unknown' }), /spec invalid/);
    const rail = readProof('rail-demo');
    assert.throws(() => load({ ...rail, subject: legacy.subject }), /omit it/);
    assert.throws(() => load({ ...rail, rail: { panels: [] } }), /spec invalid/);
    const broken = structuredClone(rail); broken.rail.panels[1].id = broken.rail.panels[0].id;
    assert.throws(() => load(broken), /duplicate id/);
    broken.rail.panels[1].id = 'unique'; delete broken.rail.panels[1].figure.items;
    assert.throws(() => load(broken), /needs items/);
    assert.throws(() => load({ ...rail, grammar: 'morph-subject' }), /missing/);
  });
  await test('all 12 hero-layout/scroll combinations render; readout and wordmark options', () => {
    let variant = 0;
    for (const layout of LAYOUTS) for (const mode of MODES) {
      const input = readProof('bleed-demo'); input.hero = { layout, wordmark: variant % 2 === 0 }; input.readout = READOUTS[variant++ % READOUTS.length]; input.scroll = { mode };
      const piece = load(input), files = buildFiles(piece, tmp, null), html = files.get(INDEX).data;
      assert.ok(html.includes(`data-layout="${layout}"`));
      assert.equal(html.includes('class="hero-word"'), input.hero.wordmark);
      assert.equal(html.includes('aria-label="Live query readout"'), layout !== 'type-only' && input.readout !== 'none');
      assert.ok(files.get(SECTIONS).data.includes('hero-poster'));
      if (mode === 'static') assert.ok(piece.chapters.every((c) => c.place.desktop === piece.chapters[0].place.desktop));
    }
  });
  const rail = load(readProof('rail-demo'));
  await test('rail is self-contained, no 3D/CDN; commerce after panels; no-JS vertical base', () => {
    const files = buildFiles(rail, tmp, null), names = [...files.keys()], html = files.get(INDEX).data;
    assert.equal(rail.subject, undefined);
    assert.ok(!names.some((n) => /^(gl|motion)\/|subjects\//.test(n)));
    assert.ok(![...files.values()].some((f) => /three\.module|(?:src|href)="https?:\/\/|(?:from|import)\s*['"]https?:\/\//.test(String(f.data))));
    assert.ok(html.indexOf('id="estimate"') > html.lastIndexOf('</article>'));
    assert.ok(!html.includes('foot-word')); assert.ok(!html.includes('class="readout'));
    assert.ok(files.get(SECTIONS).data.includes('.rail.is-pinned .rail-track'));
    assert.ok(files.get('js/runtime/archetypes/pricing.js').data.equals(fs.readFileSync(path.join(RUNTIME, 'archetypes/pricing.js'))));
    assert.ok(files.get('js/runtime/archetypes/faq.js').data.equals(fs.readFileSync(path.join(RUNTIME, 'archetypes/faq.js'))));
    const minimal = { ...readProof('rail-demo') }; delete minimal.chapters; delete minimal.commerce;
    assert.ok(buildFiles(load(minimal), tmp, null).get(INDEX).data.includes('rail-end'));
  });
  await test('mock rail: damped travel, safe kinetic bounds, anchor, unpin, mobile, reduced motion, overflow fallback', () => mockRail(rail));
  await test('shared rail pricing: live usage, cheapest fit, manual selection', mockPricing);
  await test('orbit preserves first form and moves camera; static freezes form and placement', () => {
    mockSubject(load(readProof('stack-demo'))); mockSubject(load(readProof('bleed-demo')));
  });
  await test('generated core modules import and keep real vertex arrays fixed in orbit/static', async () => {
    for (const name of ['stack-demo', 'bleed-demo']) {
      const out = path.join(tmp, 'core-' + name), result = generate(path.join(PROOFS, name, 'spec.json'), out, OFFLINE);
      const { createCore } = await import(pathToFileURL(path.join(out, 'js/runtime/subjects/core.js')).href);
      const core = createCore({ piece: result.piece, mobile: false, N: result.piece.subject.items });
      const initial = [...core.forms[0]];
      assert.ok(core.forms.every((f) => f === core.forms[0]));
      core.api.setAct(CAMERA_TEST.act); core.api.assemble();
      const camera = { fov: CAMERA_TEST.fov, aspect: CAMERA_TEST.aspect, position: { length: () => CAMERA_TEST.distance }, lookAt() {} };
      const view = core.view(camera), frame = core.frame({ dt: CAMERA_TEST.dt, time: CAMERA_TEST.time, pointer: { x: 0, y: 0 } }, view);
      assert.equal(frame.i0, 0); assert.equal(frame.t, 0); assert.deepEqual([...core.forms[0]], initial);
      if (result.piece.scroll.mode === 'orbit') assert.ok(camera.position.x > 0);
      else assert.ok(core.keys.every((key) => key === core.keys[0]));
    }
  });
  await test('proofs regenerate idempotently', () => {
    for (const name of ['rail-demo', 'stack-demo', 'bleed-demo']) {
      const spec = path.join(PROOFS, name, 'spec.json'), out = path.join(tmp, name);
      generate(spec, out, OFFLINE); const result = generate(spec, out, OFFLINE);
      assert.ok(result.report.every(([status]) => ['unchanged', 'kept'].includes(status)));
    }
  });
}
