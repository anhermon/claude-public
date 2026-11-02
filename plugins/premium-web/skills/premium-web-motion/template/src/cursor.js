// cursor: ring + dot follower, grows over interactive targets. Fine pointers only; off under reduced motion.
import { loop, isReduced, isFinePointer, damp, make } from './util/helpers.js';

export const DEFAULTS = {
  follow: 0.14,         // per-60Hz-frame lerp of the ring: 0.1-0.2 (0.14 typical), measured from public reference sites, 2026-11
  ring: 36,             // px ring diameter: measured from public reference sites, 2026-11; +-6 px
  dot: 6,               // px dot diameter: measured from public reference sites, 2026-11
  hoverScale: 1.9,      // ring scale over targets: 1.5-2x, measured from public reference sites, 2026-11
  targets: 'a, button, [data-cursor]',
  hideNative: true,     // cursor:none on body (inputs keep theirs)
  zIndex: 10000,
  reduced: undefined,
};
export function initCursor(options = {}) {
  const o = { ...DEFAULTS, ...options };
  if (isReduced(o) || !isFinePointer()) return { destroy() {} };
  const base = `position:fixed;left:0;top:0;pointer-events:none;z-index:${o.zIndex};will-change:transform;opacity:0;`;
  const ring = make('div', { 'aria-hidden': 'true', 'data-cursor-ring': '' }, {}, document.body);
  const dot = make('div', { 'aria-hidden': 'true', 'data-cursor-dot': '' }, {}, document.body);
  ring.style.cssText = `${base}width:${o.ring}px;height:${o.ring}px;margin:${-o.ring / 2}px 0 0 ${-o.ring / 2}px;border:1px solid currentColor;border-radius:50%;mix-blend-mode:difference;color:#fff`;
  dot.style.cssText = `${base}width:${o.dot}px;height:${o.dot}px;margin:${-o.dot / 2}px 0 0 ${-o.dot / 2}px;border-radius:50%;background:#fff;mix-blend-mode:difference`;
  const style = make('style', {}, {}, document.head);
  if (o.hideNative) style.textContent = 'body,a,button,[data-cursor]{cursor:none}input,textarea,select{cursor:auto}';
  let tx = -100, ty = -100, x = tx, y = ty, scale = 1, goal = 1, shown = false;
  const move = (e) => { tx = e.clientX; ty = e.clientY; goal = e.target.closest?.(o.targets) ? o.hoverScale : 1; if (!shown) { shown = true; x = tx; y = ty; ring.style.opacity = dot.style.opacity = '1'; } lp.wake(); };
  const lp = loop((_, dt) => {
    x = damp(x, tx, o.follow, dt); y = damp(y, ty, o.follow, dt); scale = damp(scale, goal, o.follow, dt);
    ring.style.transform = `translate3d(${x.toFixed(1)}px,${y.toFixed(1)}px,0) scale(${scale.toFixed(3)})`;
    dot.style.transform = `translate3d(${tx}px,${ty}px,0)`;
    return Math.abs(tx - x) + Math.abs(ty - y) + Math.abs(goal - scale) > 0.05;
  });
  addEventListener('pointermove', move, { passive: true });
  return { destroy() { removeEventListener('pointermove', move); lp.stop(); ring.remove(); dot.remove(); style.remove(); } };
}
