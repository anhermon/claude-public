// Shared helpers for transition modules.
// Transition modules import from here: easing, tweens, rAF loop, scroll-source adapter, reduced-motion, instance registry.

export const VERSION = '0.1.0';

// ---- easings (gsap-equivalent curves, t in 0..1) ----
export const EASE = {
  linear: (t) => t,
  power2Out: (t) => 1 - (1 - t) ** 2,
  power2InOut: (t) => (t < 0.5 ? 2 * t * t : 1 - (-2 * t + 2) ** 2 / 2),
  power3Out: (t) => 1 - (1 - t) ** 3,
  power3InOut: (t) => (t < 0.5 ? 4 * t ** 3 : 1 - (-2 * t + 2) ** 3 / 2),
  expoOut: (t) => (t >= 1 ? 1 : 1 - 2 ** (-10 * t)),
  expoInOut: (t) => (t <= 0 ? 0 : t >= 1 ? 1 : t < 0.5 ? 2 ** (20 * t - 10) / 2 : (2 - 2 ** (-20 * t + 10)) / 2),
};
const FRAME_HZ = 60; // lerp factors in this kit are specified per 60 Hz frame
const MAX_DT = 0.1; // s, clamp after tab switches
const SETTLE_EPS = 0.0005; // progress delta below which a damped value is considered settled

export const clamp = (v, a = 0, b = 1) => Math.min(b, Math.max(a, v));
export const lerp = (a, b, t) => a + (b - a) * t;
export const map = (v, a, b, c = 0, d = 1) => lerp(c, d, clamp((v - a) / (b - a)));
/** frame-rate independent version of "lerp by f every 60 Hz frame" */
export const damp = (cur, target, f, dt) => lerp(cur, target, 1 - (1 - f) ** (dt * FRAME_HZ));
export const settled = (a, b) => Math.abs(a - b) < SETTLE_EPS;

// ---- DOM / css helpers ----
export function resolveEl(target, root = document) {
  const el = typeof target === 'string' ? root.querySelector(target) : target;
  if (!el) throw new Error(`[ck] target not found: ${target}`);
  return el;
}
export function resolveAll(sel, root) {
  if (!sel) return [];
  if (typeof sel === 'string') return [...root.querySelectorAll(sel)];
  return Array.isArray(sel) ? sel : [...sel];
}
/** read a --ck-* css variable; supports "0.6s" / "600ms" / plain numbers. Falls back to the JS constant. */
export function cssNum(name, fallback, el = document.documentElement) {
  const raw = getComputedStyle(el).getPropertyValue(name).trim();
  if (!raw) return fallback;
  const n = parseFloat(raw);
  if (Number.isNaN(n)) return fallback;
  return raw.endsWith('ms') ? n / 1000 : n;
}
export function make(tag, props = {}, styles = {}, parent) {
  const el = document.createElement(tag);
  Object.entries(props).forEach(([k, v]) => (k === 'text' ? (el.textContent = v) : el.setAttribute(k, v)));
  Object.assign(el.style, styles);
  if (parent) parent.appendChild(el);
  return el;
}
export function injectStyle(id, css) {
  let s = document.getElementById(id);
  if (!s) {
    s = make('style', { id });
    document.head.appendChild(s);
  }
  s.textContent = css;
  return s;
}
export function isReduced(opts = {}) {
  if (typeof opts.reduced === 'boolean') return opts.reduced;
  return !!(window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches);
}
export function isFinePointer() {
  return !!(window.matchMedia && window.matchMedia('(hover: hover) and (pointer: fine)').matches);
}

// ---- instance registry: init() twice on the same element replaces the first instance ----
const registry = new WeakMap();
export function singleton(el, key, make_) {
  let m = registry.get(el);
  if (!m) registry.set(el, (m = new Map()));
  if (m.has(key)) m.get(key).destroy();
  const inst = make_();
  const origDestroy = inst.destroy;
  inst.destroy = () => {
    origDestroy();
    if (m.get(key) === inst) m.delete(key);
  };
  m.set(key, inst);
  return inst;
}

// ---- time-based tween ----
/** tween({duration(s), delay(s), ease, onUpdate(e,t), onDone}) -> {cancel(), finish()} ; instant when duration<=0 */
export function tween({ duration, delay = 0, ease = EASE.linear, onUpdate, onDone }) {
  let id = 0, done = false;
  const t0 = performance.now() + delay * 1000;
  const end = (finish) => {
    if (done) return;
    done = true;
    cancelAnimationFrame(id);
    if (finish) onUpdate?.(1, 1);
    onDone?.(finish);
  };
  const step = (now) => {
    const t = clamp((now - t0) / (duration * 1000));
    if (now >= t0) onUpdate?.(ease(t), t);
    if (t >= 1) end(false); else id = requestAnimationFrame(step);
  };
  if (duration <= 0 && delay <= 0) queueMicrotask(() => end(true));
  else id = requestAnimationFrame(step);
  return { cancel: () => end(false), finish: () => end(true) };
}

// ---- rAF loop that sleeps when fn returns false ----
export function loop(fn) {
  let id = 0, last = 0;
  const tick = (now) => {
    id = 0;
    const dt = Math.min(MAX_DT, last ? (now - last) / 1000 : 1 / FRAME_HZ);
    last = now;
    if (fn(now, dt) !== false) id = requestAnimationFrame(tick); else last = 0;
  };
  return {
    wake() { if (!id) { last = 0; id = requestAnimationFrame(tick); } },
    stop() { if (id) cancelAnimationFrame(id); id = 0; last = 0; },
    get active() { return !!id; },
  };
}

// ---- scroll source adapter: contract createScroll() .on(fn); falls back to native scroll if none given ----
/** subscribe(scroll, onChange) -> unsubscribe. Also fires on resize. */
export function subscribe(scroll, onChange) {
  const offs = [];
  const add = (t, ev, fn, o) => { t.addEventListener(ev, fn, o); offs.push(() => t.removeEventListener(ev, fn, o)); };
  if (scroll && typeof scroll.on === 'function') {
    const off = scroll.on(onChange);
    if (typeof off === 'function') offs.push(off);
  } else {
    add(window, 'scroll', onChange, { passive: true });
  }
  add(window, 'resize', onChange);
  return () => offs.forEach((f) => f());
}
/** 0..1 progress through a tall pinned section (sticky stage inside): 0 when its top hits the viewport top, 1 when its bottom hits the viewport bottom */
export function sectionProgress(el) {
  const r = el.getBoundingClientRect();
  const travel = r.height - window.innerHeight;
  return travel <= 0 ? 0 : clamp(-r.top / travel);
}
/** merge user options over DEFAULTS (shallow, undefined ignored) */
export function opts(defaults, user = {}) {
  const o = { ...defaults };
  for (const k in user) if (user[k] !== undefined) o[k] = user[k];
  return o;
}
