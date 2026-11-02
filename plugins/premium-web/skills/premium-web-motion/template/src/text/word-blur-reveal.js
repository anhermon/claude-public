// text/word-blur-reveal: per-word blur-fade. measured from public reference sites, 2026-11.
// Optional scroll scrub (options.scroll = createScroll()): words resolve as the block travels up the viewport.
import { createReveal } from '../core/reveal.js';
import { EASE, clamp01, fn } from '../core/easing.js';
export const DEFAULTS = {
  trigger: 'load',
  duration: 0.6,        // 0.6 s power3.out: measured from public reference sites, 2026-11
  stagger: 0.04,        // 40 ms: measured from public reference sites, 2026-11
  delay: 0,
  blur: 10,             // px, 10 -> 0: measured from public reference sites, 2026-11
  y: 12,                // px, 12 -> 0: measured from public reference sites, 2026-11
  opacity: 0.2,         // 0.2 -> 1: measured from public reference sites, 2026-11
  ease: EASE.power3Out,
  reverse: false,
  scroll: null,         // shared createScroll() instance => scrubbed mode
  scrubStart: 0.9,      // element top at 90% of viewport height = 0 progress
  scrubEnd: 0.35,       // element top at 35% = fully resolved
  scrubOverlap: 5,      // how many words are mid-transition at once
};
const kf = (o, blur, y, op) => ({ opacity: op, filter: `blur(${blur}px)`, transform: `translateY(${y}px)` });
export const init = createReveal({
  DEFAULTS,
  tokens: { duration: '--ck-dur-word-blur' },
  pick: (sp) => sp.words,
  hidden: (o) => kf(o, o.blur, o.y, o.opacity),
  keyframes: (o) => [kf(o, o.blur, o.y, o.opacity), kf(o, 0, 0, 1)],
  scrub(o, getUnits, el) {
    const apply = () => {
      const u = getUnits(), n = u.length;
      const r = el.getBoundingClientRect();
      const p = clamp01((innerHeight * o.scrubStart - r.top) / (innerHeight * (o.scrubStart - o.scrubEnd)));
      const span = n - 1 + o.scrubOverlap;
      u.forEach((w, i) => {
        const e = fn.power3Out(clamp01((p * span - i) / o.scrubOverlap));
        w.style.opacity = o.opacity + (1 - o.opacity) * e;
        w.style.filter = `blur(${o.blur * (1 - e)}px)`;
        w.style.transform = `translateY(${o.y * (1 - e)}px)`;
      });
    };
    apply();
    return o.scroll.on(apply);
  },
});
