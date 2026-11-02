// text/scramble-resolve: glyph noise that locks left-to-right into the real text. measured from public reference sites, 2026-11
// measured from public reference sites, 2026-11. Each char keeps its measured width, so nothing reflows.
import { $, resolve, reducedMotion } from '../core/easing.js';
import { split } from '../core/split.js';
export const DEFAULTS = {
  trigger: 'load',
  charset: '$&#@0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ', // measured from public reference sites, 2026-11 charset
  lockMs: 28,          // 28 ms per char lock, left to right: measured from public reference sites, 2026-11
  tickMs: 50,          // glyph swap interval (30-60 ms): measured from public reference sites, 2026-11 / measured from public reference sites, 2026-11
  lineStagger: 0.15,   // 150 ms between lines: measured from public reference sites, 2026-11
  delay: 0,
  liveOpacity: 0.55,   // unresolved glyphs sit dimmer, lock snaps to full
  viewThreshold: 0.5,
};
const MS = 1000;
export function init(target, options = {}) {
  const el = $(target);
  if (el.__ckScr) el.__ckScr.destroy();
  const o = resolve(el, DEFAULTS, {}, options);
  const reduced = reducedMotion(o);
  let sp = null, raf = 0, io = null, played = false, dead = false, plan = [];
  const rnd = () => o.charset[(Math.random() * o.charset.length) | 0];
  function build() {
    sp = split(el, { chars: true, onResplit: () => { lock(); plan = mkPlan(); played ? finalize() : hide(); } });
    lock(); plan = mkPlan();
  }
  function lock() {                                  // freeze each char box to its final width
    const w = sp.chars.map((c) => c.getBoundingClientRect().width);
    sp.chars.forEach((c, i) => { c.dataset.ck = c.textContent; c.style.cssText = `width:${w[i]}px;text-align:center;overflow:visible`; });
  }
  function mkPlan() {                                // per char: {c, ch, at(ms), lockAt(ms)}
    const out = [];
    sp.lines.forEach((ln, li) => {
      let j = 0;
      for (const c of ln.querySelectorAll('.ck-char')) {
        const at = (o.delay + li * o.lineStagger) * MS;
        out.push({ c, ch: c.dataset.ck, at, lockAt: at + (j++ + 1) * o.lockMs });
      }
    });
    return out;
  }
  const hide = () => plan.forEach((p) => { p.c.style.opacity = 0; });
  const finalize = () => plan.forEach((p) => { p.c.textContent = p.ch; p.c.style.opacity = ''; p.c.style.willChange = ''; });
  function reset() { cancelAnimationFrame(raf); played = false; plan.forEach((p) => (p.c.textContent = p.ch)); if (reduced) { finalize(); played = true; } else hide(); }
  function play() {
    if (dead || played) return Promise.resolve();
    played = true;
    if (reduced) { finalize(); return Promise.resolve(); }
    return new Promise((res) => {
      const t0 = performance.now();
      let lastTick = -Infinity;
      const frame = (now) => {
        if (dead) return res();
        const t = now - t0, tick = t - lastTick >= o.tickMs;
        if (tick) lastTick = t;
        let open = 0;
        for (const p of plan) {
          if (p.done) continue;
          if (t < p.at) { open++; continue; }
          if (t >= p.lockAt) { p.c.textContent = p.ch; p.c.style.opacity = ''; p.done = true; continue; }
          open++;
          if (tick || p.c.style.opacity === '0') {
            p.c.textContent = p.ch === ' ' ? ' ' : rnd();
            p.c.style.opacity = o.liveOpacity;
          }
        }
        if (open) raf = requestAnimationFrame(frame);
        else { finalize(); o.onComplete && o.onComplete(); res(); }
      };
      plan.forEach((p) => (p.done = false));
      raf = requestAnimationFrame(frame);
    });
  }
  function destroy() { dead = true; cancelAnimationFrame(raf); io && io.disconnect(); sp && sp.revert(); delete el.__ckScr; }
  build();
  reset();
  if (!reduced && o.trigger === 'view') {
    io = new IntersectionObserver((es) => { if (es.some((e) => e.isIntersecting)) { io.disconnect(); play(); } }, { threshold: o.viewThreshold });
    io.observe(el);
  } else if (o.trigger === 'load') requestAnimationFrame(() => play());
  return (el.__ckScr = { play, reset, destroy, update: (x) => Object.assign(o, x) });
}
