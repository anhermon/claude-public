// core/easing: easings, token reading, reduced-motion, tiny rAF tween. No deps.
export const EASE = {
  expoOut: 'cubic-bezier(0.16, 1, 0.3, 1)',      // GSAP expo.out, measured from public reference sites, 2026-11
  expoInOut: 'cubic-bezier(0.87, 0, 0.13, 1)',   // expo.inOut, measured from public reference sites, 2026-11
  power3Out: 'cubic-bezier(0.215, 0.61, 0.355, 1)', // power3.out, measured from public reference sites, 2026-11
  in: 'cubic-bezier(0.7, 0, 0.84, 0)',           // accelerating, measured from public reference sites, 2026-11
  linear: 'linear',
};
const clamp01 = (x) => Math.min(1, Math.max(0, x));
// JS equivalents for rAF-driven modules
export const fn = {
  linear: (t) => t,
  expoOut: (t) => (t >= 1 ? 1 : 1 - Math.pow(2, -10 * t)),
  expoInOut: (t) => (t <= 0 ? 0 : t >= 1 ? 1 : t < 0.5 ? Math.pow(2, 20 * t - 10) / 2 : (2 - Math.pow(2, -20 * t + 10)) / 2),
  power3Out: (t) => 1 - Math.pow(1 - t, 3),
  cubicIn: (t) => t * t * t,
};
export { clamp01 };

export const $ = (t, root = document) => (typeof t === 'string' ? root.querySelector(t) : t);
export const $$ = (t, root = document) => (typeof t === 'string' ? [...root.querySelectorAll(t)] : t instanceof Element ? [t] : [...t]);

const MS_PER_S = 1000;
// "0.6s" / "600ms" -> seconds; returns fallback if the var is missing
export function token(el, name, fallback) {
  const v = getComputedStyle(el || document.documentElement).getPropertyValue(name).trim();
  if (!v) return fallback;
  if (v.endsWith('ms')) return parseFloat(v) / MS_PER_S;
  if (v.endsWith('s')) return parseFloat(v);
  return typeof fallback === 'number' ? parseFloat(v) : v;
}
// merge DEFAULTS <- css tokens <- options. tokenMap: {optionKey: '--ck-var'}
export function resolve(el, defaults, tokenMap = {}, options = {}) {
  const o = { ...defaults };
  for (const k in tokenMap) o[k] = token(el, tokenMap[k], defaults[k]);
  return { ...o, ...options };
}
export function reducedMotion(options = {}) {
  if (typeof options.reduced === 'boolean') return options.reduced;
  return typeof matchMedia === 'function' && matchMedia('(prefers-reduced-motion: reduce)').matches;
}
// rAF tween: returns {cancel, finished:Promise}. fn(eased, raw)
export function tween({ duration, ease = fn.expoOut, delay = 0, onUpdate, onDone }) {
  let raf = 0, cancelled = false, resolveP;
  const finished = new Promise((r) => (resolveP = r));
  const t0 = performance.now() + delay * MS_PER_S;
  const tick = (now) => {
    if (cancelled) return;
    const raw = clamp01((now - t0) / (duration * MS_PER_S));
    if (now >= t0) onUpdate(ease(raw), raw);
    if (raw >= 1) { onDone && onDone(); resolveP(true); return; }
    raf = requestAnimationFrame(tick);
  };
  raf = requestAnimationFrame(tick);
  return { finished, cancel() { cancelled = true; cancelAnimationFrame(raf); resolveP(false); } };
}
