// text/blur-line-reveal: per-line blur + rise. measured from public reference sites, 2026-11.
import { createReveal } from '../core/reveal.js';
import { EASE } from '../core/easing.js';
export const DEFAULTS = {
  trigger: 'load',      // 'load' | 'view' | 'manual'
  duration: 0.6,        // 0.5-0.7 s: measured from public reference sites, 2026-11
  stagger: 0.1,         // 100 ms (100-150): measured from public reference sites, 2026-11
  delay: 0,
  blur: 12,             // px, 10-12 -> 0: measured from public reference sites, 2026-11
  y: 20,                // px, 16-24 -> 0: measured from public reference sites, 2026-11
  opacity: 0,
  ease: EASE.expoOut,   // expo-out: measured from public reference sites, 2026-11
  reverse: false,
};
const FINAL = { opacity: 1, filter: 'blur(0px)', transform: 'translateY(0)' };
export const init = createReveal({
  DEFAULTS,
  tokens: { duration: '--ck-dur-blur-line' },
  pick: (sp) => sp.lines,
  hidden: (o) => ({ opacity: o.opacity, filter: `blur(${o.blur}px)`, transform: `translateY(${o.y}px)` }),
  keyframes: (o) => [{ opacity: o.opacity, filter: `blur(${o.blur}px)`, transform: `translateY(${o.y}px)` }, FINAL],
});
