// text/count-up-blur: number counts up while resolving from blur. measured from public reference sites, 2026-11.
// Reads "9K+", "$1,240.5", "24" from the element; keeps prefix/suffix/decimals/thousands separator.
import { $, resolve, reducedMotion, tween, fn, token } from '../core/easing.js';
export const DEFAULTS = {
  trigger: 'load',     // 'load' | 'view' | 'manual'
  duration: 0.9,       // 0.9 s ease-out: measured from public reference sites, 2026-11
  blur: 4,             // px, 4 -> 0: measured from public reference sites, 2026-11
  from: 0,
  delay: 0,
  ease: fn.expoOut,    // ease-out family: measured from public reference sites, 2026-11
  fadeFrac: 0.3,       // opacity ramps over the first 30% so the number "develops"
  viewThreshold: 0.5,  // measured from public reference sites, 2026-11 IO 0.5
};
const NUM = /(-?\d[\d,]*(?:\.\d+)?)/;
export function init(target, options = {}) {
  const el = $(target);
  if (el.__ckCount) el.__ckCount.destroy();
  const o = resolve(el, DEFAULTS, { duration: '--ck-dur-count', blur: '--ck-blur-count' }, options);
  const reduced = reducedMotion(o);
  const orig = el.dataset.ckText || el.textContent.trim();
  el.dataset.ckText = orig;
  const m = orig.match(NUM);
  if (!m) throw new Error('ck count-up: no number in "' + orig + '"');
  const [raw] = m, pre = orig.slice(0, m.index), suf = orig.slice(m.index + raw.length);
  const end = parseFloat(raw.replace(/,/g, ''));
  const dec = (raw.split('.')[1] || '').length;
  const sep = raw.includes(',');
  const fmt = (v) => pre + v.toLocaleString('en-US', { minimumFractionDigits: dec, maximumFractionDigits: dec, useGrouping: sep }) + suf;
  el.setAttribute('aria-label', orig);
  el.textContent = '';
  const inner = document.createElement('span');
  inner.setAttribute('aria-hidden', 'true');
  inner.style.cssText = 'display:inline-block;font-variant-numeric:tabular-nums;text-align:' + getComputedStyle(el).textAlign;
  el.append(inner);
  inner.textContent = orig;
  inner.style.minWidth = inner.offsetWidth + 'px';   // reserve final width: no reflow while counting
  let tw = null, io = null, played = false, dead = false;
  const paint = (e) => {
    inner.textContent = fmt(o.from + (end - o.from) * e);
    inner.style.filter = `blur(${o.blur * (1 - e)}px)`;
    inner.style.opacity = Math.min(1, e / o.fadeFrac);
  };
  const settle = () => { inner.textContent = orig; inner.style.filter = ''; inner.style.opacity = ''; inner.style.willChange = ''; };
  function reset() { tw && tw.cancel(); played = false; if (reduced) { settle(); played = true; } else { paint(0); } }
  function play() {
    if (dead || played) return Promise.resolve();
    played = true;
    if (reduced) { settle(); return Promise.resolve(); }
    inner.style.willChange = 'filter, opacity';
    tw = tween({ duration: o.duration, delay: o.delay, ease: o.ease, onUpdate: paint, onDone: () => { settle(); o.onComplete && o.onComplete(); } });
    return tw.finished;
  }
  function destroy() { dead = true; tw && tw.cancel(); io && io.disconnect(); el.textContent = orig; delete el.__ckCount; }
  reset();
  if (!reduced && o.trigger === 'view') {
    io = new IntersectionObserver((es) => { if (es.some((e) => e.isIntersecting)) { io.disconnect(); play(); } }, { threshold: o.viewThreshold });
    io.observe(el);
  } else if (o.trigger === 'load') requestAnimationFrame(() => play());
  return (el.__ckCount = { play, reset, destroy, update: (x) => Object.assign(o, x) });
}
