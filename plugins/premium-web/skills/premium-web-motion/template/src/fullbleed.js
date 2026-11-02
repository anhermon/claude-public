// fullbleed: an inset rounded card expands to the full viewport (the hero entrance after the loader).
// clip-path animates on the compositor-friendly paint path; no layout change, no reflow.
import { EASE, resolveEl, isReduced, singleton, opts } from './util/helpers.js';

export const DEFAULTS = {
  inset: '8vh 8vw',     // starting inset (top/bottom left/right): measured from public reference sites, 2026-11; +-3 vh
  radius: 28,           // px, corner radius at start -> 0: 28 px, measured from public reference sites, 2026-11
  duration: 0.9,        // s, expo-out: 0.9 s (0.25 s seen in recordings; slower reads better), measured from public reference sites, 2026-11
  delay: 0,
  ease: 'cubic-bezier(0.16, 1, 0.3, 1)', // expo-out
  nav: null,            // selector of the nav island that drops in 0.1 s after the card starts
  navDelay: 0.1,        // s: measured from public reference sites, 2026-11; +-0.05 s
  navDrop: 0.5,         // s for the nav drop (practice default)
  trigger: 'load',      // 'load' | 'manual'
  reduced: undefined,
};
const MS = 1000;
export function fullbleed(target, options = {}) {
  const el = resolveEl(target);
  return singleton(el, 'fullbleed', () => {
    const o = opts(DEFAULTS, options);
    const reduced = isReduced(o);
    const from = `inset(${o.inset} round ${o.radius}px)`, to = 'inset(0px 0px 0px 0px round 0px)';
    const nav = o.nav ? document.querySelector(o.nav) : null;
    let played = false, anims = [];
    const hold = () => { if (!reduced) { el.style.clipPath = from; if (nav) { nav.style.opacity = '0'; nav.style.transform = 'translate(-50%, -140%)'; } } };
    const clear = () => { el.style.clipPath = ''; if (nav) { nav.style.opacity = ''; nav.style.transform = ''; } };
    function play() {
      if (played) return Promise.resolve();
      played = true;
      if (reduced) { clear(); return Promise.resolve(); }
      const a = el.animate([{ clipPath: from }, { clipPath: to }], { duration: o.duration * MS, delay: o.delay * MS, easing: o.ease, fill: 'both' });
      anims = [a];
      if (nav) anims.push(nav.animate([{ opacity: 0, transform: 'translate(-50%, -140%)' }, { opacity: 1, transform: 'translate(-50%, 0)' }],
        { duration: o.navDrop * MS, delay: (o.delay + o.navDelay) * MS, easing: o.ease, fill: 'both' }));
      return Promise.all(anims.map((x) => x.finished)).then(() => { anims.forEach((x) => x.cancel()); clear(); o.onComplete?.(); }, () => {});
    }
    hold();
    if (o.trigger === 'load') requestAnimationFrame(play);
    return { play, destroy() { anims.forEach((x) => x.cancel()); clear(); } };
  });
}
export { EASE };
