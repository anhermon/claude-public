import fs from 'node:fs';
import path from 'node:path';
import vm from 'node:vm';
import assert from 'node:assert/strict';
import { fileURLToPath } from 'node:url';
import { loadSpec } from './lib/spec.mjs';
import { buildFiles, generate } from './new-piece.mjs';
import { fingerprint } from './variation-check.mjs';

const ROOT = path.join(path.dirname(fileURLToPath(import.meta.url)), '..');
const GRAMMARS = ['terminal', 'collage'], OFFLINE = { fetchFonts:false };
const TEST = { width:1440, mobile:390, height:900, commandChars:3, beforeChar:34, exactChar:35, huge:1e6, far:20, half:.5, maxFrames:200 };
const source = (grammar, file) => fs.readFileSync(path.join(ROOT, 'runtime', 'grammars', grammar, file), 'utf8');
const executable = (source) => source.replace(/^import .*;\n/gm, '').replace(/^export /gm, '');
const proof = (grammar) => JSON.parse(fs.readFileSync(path.join(ROOT, '.proofs', grammar + '-demo', 'spec.json'), 'utf8'));
function element() {
  const classes = new Set(), attrs = {}, events = {};
  return { textContent:'', dateTime:'', dataset:{}, events, attrs,
    style:{ setProperty(k,v) { this[k] = v; } },
    classList:{ add(k) { classes.add(k); }, remove(k) { classes.delete(k); }, contains(k) { return classes.has(k); }, toggle(k) { classes.has(k) ? classes.delete(k) : classes.add(k); } },
    addEventListener(k,fn) { events[k] = fn; }, setAttribute(k,v) { attrs[k] = v; }, getAttribute(k) { return attrs[k]; },
  };
}

function harness() {
  const root = element(), events = {}, frames = new Map(), timers = new Map();
  const state = { time:0, next:0, width:TEST.width, reduced:false, scroll:0 };
  const media = { get matches() { return state.reduced; }, addEventListener(k,fn) { events.media = fn; } };
  const document = { documentElement:root, hidden:false, addEventListener(k,fn) { events['doc-' + k] = fn; } };
  const context = { document, window:{}, URLSearchParams, location:{ search:'' }, Date, console,
    performance:{ now:() => state.time }, matchMedia:(query) => query.includes('pointer:fine') ? { matches:true } : media,
    addEventListener(k,fn) { events[k] = fn; },
    requestAnimationFrame(fn) { const id = ++state.next; frames.set(id,fn); return id; }, cancelAnimationFrame(id) { frames.delete(id); },
    setTimeout(fn) { const id = ++state.next; timers.set(id,fn); return id; }, clearTimeout(id) { timers.delete(id); },
    setInterval() { return ++state.next; }, clearInterval() {}, innerHeight:TEST.height,
  };
  Object.defineProperty(context, 'innerWidth', { get:() => state.width });
  const advance = (ms) => { state.time += ms; const pending = [...frames.values()]; frames.clear(); pending.forEach((fn) => fn(state.time)); };
  return { root, events, frames, state, context, document, advance };
}

function terminalBehavior(piece) {
  const h = harness();
  const sections = piece.terminal.session.map((entry,i) => {
    const parts = Object.fromEntries(['[data-command]', '[data-output]', '[data-session-state]', '.terminal-window'].map((key) => [key,element()]));
    return { parts, querySelector: (s) => parts[s], getBoundingClientRect: () => ({ top:i * TEST.height - h.state.scroll }) };
  });
  h.document.querySelectorAll = (s) => s === '[data-session]' ? sections : [];
  const code = executable(source('terminal','session.js')) + '\n' + executable(source('terminal','boot.js')) + '\nboot;';
  vm.runInNewContext(code,h.context)({ ...piece, chapters:[] },{},() => {});
  const first = sections[0].parts;
  assert.equal(first['[data-command]'].textContent,'');
  h.advance(TEST.beforeChar); assert.equal(first['[data-command]'].textContent,'');
  h.advance(TEST.exactChar - TEST.beforeChar); assert.equal(first['[data-command]'].textContent,piece.terminal.session[0].cmd.slice(0,1));
  assert.equal(first['[data-output]'].textContent,'');
  h.advance(TEST.huge); assert.equal(first['[data-output]'].textContent,piece.terminal.session[0].output.join('\n'));
  h.state.scroll = TEST.height; h.events.scroll(); assert.equal(h.context.window.__piece.terminal.active,1);
  assert.equal(sections[1].parts['[data-command]'].textContent,'');
  h.state.scroll = 0; h.events.scroll(); assert.equal(first['[data-command]'].textContent,'');
  h.state.reduced = true; h.events.media();
  sections.forEach((s,i) => { assert.equal(s.parts['[data-command]'].textContent,piece.terminal.session[i].cmd); assert.equal(s.parts['[data-output]'].textContent,piece.terminal.session[i].output.join('\n')); });
  assert.equal(h.frames.size,0); assert.ok('staticSession' in h.root.dataset);
  h.state.width = TEST.mobile; h.events.resize(); assert.equal(h.frames.size,0);
}

function collageBehavior(piece) {
  const h = harness(), block = element(); block.attrs['aria-expanded'] = 'false';
  const chapters = piece.chapters.map((_,i) => ({ ...element(), words:piece.collage.words.map(element),
    querySelectorAll() { return this.words; }, getBoundingClientRect:() => ({ top:i * TEST.height - h.state.scroll,height:TEST.height }) }));
  h.document.querySelectorAll = (s) => s === '[data-collage]' ? chapters : [block];
  block.closest = () => chapters[0];
  const code = executable(source('collage','motion.js')) + '\n' + executable(source('collage','boot.js')) + '\nboot;';
  vm.runInNewContext(code,h.context)(piece,{},() => {});
  h.state.reduced = false;
  h.events.pointermove({ clientX:TEST.width * TEST.far,clientY:TEST.height * TEST.far });
  let n = 0;
  while(h.frames.size) { assert.ok(n++ < TEST.maxFrames); h.advance(TEST.exactChar); }
  const word = chapters[0].words[0];
  assert.ok(Math.abs(parseFloat(word.style['--word-x'])) <= TEST.far);
  assert.ok(parseFloat(word.style['--word-x']) < parseFloat(chapters[0].words[1].style['--word-x']));
  assert.ok(+word.style['--word-scale'] > 1);
  block.events.click(); assert.equal(block.attrs['aria-expanded'],'true');
  block.events.click(); assert.equal(block.attrs['aria-expanded'],'false');
  h.state.width = TEST.mobile; h.events.resize(); h.advance(TEST.exactChar); assert.equal(word.style['--word-x'],'0px');
  block.events.click(); assert.ok(chapters[0].classList.contains('is-reflowed'));
  h.state.reduced = true; h.events.media(); assert.equal(h.frames.size,0); assert.ok('staticCollage' in h.root.dataset);
}

export async function codeOnlySelftest(tmp, check) {
  const test = async (label,fn) => { try { await fn(); check(label,true); } catch(error) { check(label,false,error.stack); } };
  const specFile = path.join(tmp,'code-only.json');
  const load = (spec) => { fs.writeFileSync(specFile,JSON.stringify(spec)); return loadSpec(specFile).piece; };
  for (const grammar of GRAMMARS) {
    const spec = proof(grammar), piece = load(spec);
    await test(grammar + ': portfolio includes authored chapter order', () => {
      const result = fingerprint(spec), list = grammar === 'terminal' ? spec.terminal.session : spec.chapters;
      assert.equal(result.order.length,list.length);
      assert.equal(result.heroLayout,grammar === 'terminal' ? 'window' : 'type');
    });
    await test(grammar + ': schema rejects cross-grammar fields, missing data and duplicate ids', () => {
      assert.throws(() => load({ ...spec, subject:{ kind:'glass-lattice' } }), /omit it/);
      const missing = structuredClone(spec); delete missing[grammar]; assert.throws(() => load(missing), /missing/);
      const duplicate = structuredClone(spec), list = grammar === 'terminal' ? duplicate.terminal.session : duplicate.chapters;
      list[1].id = list[0].id; assert.throws(() => load(duplicate), /duplicate id/);
      if (grammar === 'terminal') {
        const bad = structuredClone(spec); delete bad.terminal.session[1].pane.items; assert.throws(() => load(bad), /needs items/);
        bad.terminal.theme.screen = 'red'; assert.throws(() => load(bad), /does not match/);
      } else {
        const bad = structuredClone(spec); bad.collage.blocks[0].color = TEST.far; assert.throws(() => load(bad), /above/);
        bad.collage.blocks[0].color = bad.collage.palette.length; assert.throws(() => load(bad), /out of range/);
        delete bad.chapters[0].copy.deck; assert.throws(() => load(bad), /title and deck/);
      }
    });
    await test(grammar + ': six chapters, escaped copy, no media/CDN/3D, complete no-JS frames, idempotence', () => {
      const files = buildFiles(piece,tmp,null), names = [...files.keys()], html = files.get('index.html').data;
      assert.ok(!names.some((name) => /^(gl|motion|fonts|img)\//.test(name)));
      assert.ok(![...files.values()].some((file) => /(?:src|href)="https?:\/\/|three\.module/.test(String(file.data))));
      const list = grammar === 'terminal' ? piece.terminal.session : piece.chapters;
      list.forEach((entry) => assert.ok(html.includes(`id="${entry.id}"`)));
      const escaped = structuredClone(piece);
      if (grammar === 'terminal') { escaped.terminal.session[0].cmd = '<script>alert(1)</script>'; assert.ok(html.includes(piece.terminal.session[0].output[0])); }
      else escaped.collage.words[0] = '<script>alert(1)</script>';
      assert.ok(buildFiles(escaped,tmp,null).get('index.html').data.includes('&lt;script&gt;'));
      const out = path.join(tmp,grammar + '-demo'), input = path.join(ROOT,'.proofs',grammar + '-demo','spec.json');
      generate(input,out,OFFLINE); assert.ok(generate(input,out,OFFLINE).report.every(([status]) => ['unchanged','kept'].includes(status)));
    });
    await test(grammar + ': actual controller timing, scroll, bounded motion, mobile and reduced motion', () => grammar === 'terminal' ? terminalBehavior(piece) : collageBehavior(piece));
  }
}
