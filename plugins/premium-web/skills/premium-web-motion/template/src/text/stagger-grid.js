// text/stagger-grid: blur-rise stagger of a card/list/grid's children. measured from public reference sites, 2026-11 (all four sites).
import { createReveal } from '../core/reveal.js';
import { EASE } from '../core/easing.js';
export const DEFAULTS = {
  trigger: 'load',
  items: ':scope > *',  // selector for the children to stagger
  duration: 0.8,        // 0.8 s: measured from public reference sites, 2026-11
  stagger: 0.11,        // 100-120 ms: measured from public reference sites, 2026-11
  delay: 0,
  blur: 14,             // px, 14 -> 0: measured from public reference sites, 2026-11
  y: 40,                // px, 40 -> 0: measured from public reference sites, 2026-11
  opacity: 0,
  ease: EASE.expoOut,
  reverse: false,
};
const kf = (blur, y, op) => ({ opacity: op, filter: `blur(${blur}px)`, transform: `translateY(${y}px)` });
export const init = createReveal({
  DEFAULTS,
  tokens: { duration: '--ck-dur-stagger-grid' },
  noSplit: true,
  pick: (el, o) => [...el.querySelectorAll(o.items)],
  hidden: (o) => kf(o.blur, o.y, o.opacity),
  keyframes: (o) => [kf(o.blur, o.y, o.opacity), kf(0, 0, 1)],
});
