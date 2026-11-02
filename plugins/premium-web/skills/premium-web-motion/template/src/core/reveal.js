// core/reveal: shared runner behind the DOM text reveals (blur-line, mask-rise, word-blur, stagger-grid).
// Hidden state is inline style; WAAPI plays hidden->final with per-unit delay; on finish inline style is cleared
// (final state == natural CSS), so there is no reflow or jump on completion.
import { $, resolve, reducedMotion } from './easing.js';
import { split } from './split.js';

const VIEW_THRESHOLD = 0.5;  // IO trigger: measured from public reference sites, 2026-11 "IO 0.5"
const MS = 1000;

/** spec: {DEFAULTS, tokens, splitOpts?(o), pick(split|el, o)->Element[], hidden(o)->{css}, keyframes(o)->[from,to]} */
export function createReveal(spec) {
  return function init(target, options = {}) {
    const el = $(target);
    if (!el) throw new Error('ck: target not found');
    if (el.__ck && el.__ck.spec === spec) el.__ck.destroy();
    const o = resolve(el, spec.DEFAULTS, spec.tokens, options);
    const reduced = reducedMotion(o);
    let sp = null, units = [], anims = [], io = null, played = false, dead = false, scrollOff = null;

    const setHidden = (u) => {
      const h = spec.hidden(o);
      for (const x of u) { x.dataset.ckHidden = ''; Object.assign(x.style, h); }
    };
    const clear = (u) => {
      for (const x of u) { x.style.cssText = x.__ckBase || ''; delete x.dataset.ckHidden; }
    };
    const collect = () => {
      units = spec.pick(sp || el, o);
      units.forEach((x) => { if (x.__ckBase === undefined) x.__ckBase = x.style.cssText; });
    };
    const prepare = () => {
      if (spec.noSplit) { sp = null; } else {
        sp = split(el, { ...(spec.splitOpts ? spec.splitOpts(o) : {}), onResplit: () => { collect(); played ? clear(units) : setHidden(units); } });
      }
      collect();
      if (reduced) { clear(units); played = true; } else setHidden(units);
    };
    function play() {
      if (dead || played) return Promise.resolve();
      played = true;
      if (reduced) { clear(units); o.onComplete && o.onComplete(); return Promise.resolve(); }
      const [from, to] = spec.keyframes(o);
      const order = o.reverse ? [...units].reverse() : units;
      anims = order.map((u, i) => {
        u.style.willChange = Object.keys(from).filter((k) => k !== 'offset').join(',');
        return u.animate([from, to], { duration: o.duration * MS, delay: (o.delay + i * o.stagger) * MS, easing: o.ease, fill: 'both' });
      });
      const all = Promise.all(anims.map((a) => a.finished)).then(() => {
        if (dead) return;
        anims.forEach((a) => a.cancel());
        clear(units);
        o.onComplete && o.onComplete();
      }, () => {});
      return all;
    }
    function reset() {
      anims.forEach((a) => a.cancel()); anims = [];
      played = false;
      if (spec.scrub) return;
      reduced ? clear(units) : setHidden(units);
      if (reduced) played = true;
    }
    function destroy() {
      dead = true;
      anims.forEach((a) => a.cancel());
      io && io.disconnect(); scrollOff && scrollOff();
      clear(units);
      sp && sp.revert();
      delete el.__ck;
    }
    prepare();
    if (spec.scrub && o.scroll && !reduced) scrollOff = spec.scrub(o, () => units, el);
    else if (o.trigger === 'view' && !reduced) {
      io = new IntersectionObserver((es) => { if (es.some((e) => e.isIntersecting)) { io.disconnect(); play(); } }, { threshold: VIEW_THRESHOLD });
      io.observe(el);
    } else if (o.trigger === 'load') {
      (document.fonts && document.fonts.ready ? document.fonts.ready : Promise.resolve()).then(() => requestAnimationFrame(() => play()));
    }
    const api = {
      play, reset, destroy, spec,
      update(opts) { Object.assign(o, opts); },
      get units() { return units; },
      get done() { return Promise.all(anims.map((a) => a.finished)).catch(() => {}); },
    };
    el.__ck = api;
    return api;
  };
}
