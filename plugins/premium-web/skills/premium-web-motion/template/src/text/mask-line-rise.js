// text/mask-line-rise: overflow-clipped line, text rises from below. measured from public reference sites, 2026-11.
import { createReveal } from '../core/reveal.js';
import { EASE } from '../core/easing.js';
export const DEFAULTS = {
  trigger: 'load',
  duration: 0.8,        // 0.8 s: measured from public reference sites, 2026-11
  stagger: 0.06,        // 60 ms line stagger: measured from public reference sites, 2026-11
  delay: 0,
  fromY: 105,           // % of line height, 105 -> 0: measured from public reference sites, 2026-11
  ease: EASE.expoOut,   // expo.out: measured from public reference sites, 2026-11
  reverse: false,
};
export const init = createReveal({
  DEFAULTS,
  tokens: { duration: '--ck-dur-mask-rise' },
  splitOpts: () => ({ mask: true }),
  pick: (sp) => sp.inners,
  hidden: (o) => ({ transform: `translateY(${o.fromY}%)` }),
  keyframes: (o) => [{ transform: `translateY(${o.fromY}%)` }, { transform: 'translateY(0)' }],
});
