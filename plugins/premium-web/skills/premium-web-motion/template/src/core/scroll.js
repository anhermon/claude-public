// core/scroll: one shared scroll source. Damped lerp over native scroll (no hijack).
import { fn, clamp01, reducedMotion } from './easing.js';
const DEFAULTS = {
  smooth: true,
  lerp: 0.09,        // 0.08-0.1 damped lerp: measured from public reference sites, 2026-11
  epsilon: 0.00005,  // settle threshold on progress
  frameMs: 16.667,   // lerp is tuned per 60 Hz frame; scaled by dt
};
export function createScroll(options = {}) {
  const o = { ...DEFAULTS, ...options };
  const smooth = o.smooth && !reducedMotion(o);
  const listeners = new Set();
  const segs = {};
  let target = 0, cur = 0, vel = 0, raf = 0, last = 0, dead = false;
  const max = () => Math.max(1, document.documentElement.scrollHeight - innerHeight);
  const read = () => clamp01(scrollY / max());
  const state = {
    get progress() { return cur; },
    get velocity() { return vel; },
    get target() { return target; },
    on(f) { listeners.add(f); f(state); return () => listeners.delete(f); },
    // named sub-range of progress with its own easing; returns a getter and stores it by name
    segment(name, [a, b], ease = fn.linear) {
      const get = () => ease(clamp01((cur - a) / (b - a)));
      segs[name] = get;
      return get;
    },
    segments: segs,
    destroy() { dead = true; cancelAnimationFrame(raf); removeEventListener('scroll', onScroll); removeEventListener('resize', onScroll); listeners.clear(); },
  };
  const emit = () => listeners.forEach((f) => f(state));
  function frame(now) {
    if (dead) return;
    const dt = Math.min(4, (now - last) / o.frameMs || 1);
    last = now;
    const k = 1 - Math.pow(1 - o.lerp, dt);
    const prev = cur;
    cur += (target - cur) * k;
    if (Math.abs(target - cur) < o.epsilon) cur = target;
    vel = (cur - prev) / dt;
    emit();
    raf = cur === target ? 0 : requestAnimationFrame(frame);
    if (!raf) { vel = 0; }
  }
  function onScroll() {
    target = read();
    if (!smooth) { vel = target - cur; cur = target; emit(); return; }
    if (!raf) { last = performance.now(); raf = requestAnimationFrame(frame); }
  }
  target = cur = read();
  addEventListener('scroll', onScroll, { passive: true });
  addEventListener('resize', onScroll);
  return state;
}
