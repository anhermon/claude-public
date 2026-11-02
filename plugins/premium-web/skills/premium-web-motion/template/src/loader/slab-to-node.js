// loader/slab-to-node: full-bleed accent slab shrinks to a squircle, then FLIPs onto a node in the UI and becomes it.
// measured from public reference sites, 2026-11; +-0.1 s: 0.55 s expo.inOut, radius 0 -> 28%.
// Implemented with clip-path inset() on a full-viewport slab: no scale distortion of the radius, paint-only.
import { $, resolve, reducedMotion, EASE } from '../core/easing.js';
export const DEFAULTS = {
  dock: null,              // element (or selector) the squircle lands on; revealed when the slab arrives
  color: 'var(--ck-accent)', // one hot accent on a dark page, e.g. lime
  markColor: '#0a0a09',
  mark: '»',          // glyph centred in the squircle (a ">>" chevron mark was observed)
  nodeSize: 112,           // px, resting squircle edge
  radius: 0.28,            // 28% of edge: measured from public reference sites, 2026-11
  duration: 0.55,          // 0.55 s: measured from public reference sites, 2026-11
  ease: EASE.expoInOut,    // expo.inOut: measured from public reference sites, 2026-11
  hold: 0.12,              // s the squircle rests before docking (observed: shrink 0-0.6 s, dock 0.5-1.0 s)
  revealAt: 0.55,          // onReveal at this fraction of the shrink (observed: hero text 0.3-0.7 s)
  waitFor: null,
  zIndex: 9999,
  lockScroll: true,
};
const MS = 1000;
export function init(target, options = {}) {
  const host = $(target) || document.body;
  const o = resolve(host, DEFAULTS, { duration: '--ck-dur-slab' }, options);
  const reduced = reducedMotion(o);
  const dock = $(o.dock);
  const W = () => innerWidth, H = () => innerHeight;
  const slab = document.createElement('div');
  slab.setAttribute('aria-hidden', 'true');
  slab.style.cssText = `position:fixed;inset:0;z-index:${o.zIndex};background:${o.color};will-change:clip-path;clip-path:inset(0 0 0 0 round 0px)`;
  const mark = document.createElement('div');
  mark.setAttribute('aria-hidden', 'true');
  mark.textContent = o.mark;
  mark.style.cssText = `position:fixed;left:0;top:0;z-index:${o.zIndex + 1};width:${o.nodeSize}px;height:${o.nodeSize}px;display:grid;place-items:center;font:700 ${o.nodeSize * 0.42}px/1 var(--ck-font-sans);color:${o.markColor};transform-origin:0 0;will-change:transform`;
  mark.style.transform = `translate(${(W() - o.nodeSize) / 2}px,${(H() - o.nodeSize) / 2}px)`;
  host.append(slab, mark);
  const live = document.createElement('div');
  live.setAttribute('role', 'status'); live.textContent = 'Loading';
  live.style.cssText = 'position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0)';
  host.append(live);
  if (o.lockScroll) document.documentElement.style.overflow = 'hidden';
  if (dock) dock.style.visibility = 'hidden';
  const inset = (l, t, w, h, r) => `inset(${t}px ${W() - l - w}px ${H() - t - h}px ${l}px round ${r}px)`;
  const squircle = () => { const s = o.nodeSize; return [(W() - s) / 2, (H() - s) / 2, s, s]; };
  let dead = false, resolveDone;
  const done = new Promise((r) => (resolveDone = r));
  const cleanup = () => { slab.remove(); mark.remove(); live.remove(); if (dock) dock.style.visibility = ''; if (o.lockScroll) document.documentElement.style.overflow = ''; resolveDone(true); };
  const wait = (ms) => new Promise((r) => setTimeout(r, ms));
  async function run() {
    if (reduced) { o.onReveal && o.onReveal(); o.onComplete && o.onComplete(); cleanup(); return; }
    const d = o.duration * MS, opt = { duration: d, easing: o.ease, fill: 'forwards' };
    const [l, t, w, h] = squircle();
    const a = slab.animate([{ clipPath: 'inset(0px 0px 0px 0px round 0px)' }, { clipPath: inset(l, t, w, h, w * o.radius) }], opt);
    setTimeout(() => !dead && o.onReveal && o.onReveal(), d * o.revealAt);
    await a.finished;
    if (dead) return;
    if (o.waitFor) await Promise.all([].concat(o.waitFor));
    await wait(o.hold * MS);
    if (dead) return;
    if (dock) {                                           // FLIP onto the node
      const r = dock.getBoundingClientRect();
      const rad = Math.min(r.width, r.height) * o.radius;
      slab.animate([{ clipPath: inset(l, t, w, h, w * o.radius) }, { clipPath: inset(r.left, r.top, r.width, r.height, rad) }], opt);
      const s = r.width / o.nodeSize;
      const m = mark.animate([{ transform: `translate(${l}px,${t}px) scale(1)` }, { transform: `translate(${r.left}px,${r.top}px) scale(${s})` }], opt);
      await m.finished;
      if (dead) return;
      dock.style.visibility = '';                         // node takes over from the slab with no visible seam
      await slab.animate([{ opacity: 1 }, { opacity: 0 }], { duration: 120, fill: 'forwards' }).finished;
      mark.style.display = 'none';
    } else {
      const s = slab.animate([{ opacity: 1, clipPath: inset(l, t, w, h, w * o.radius) }, { opacity: 0, clipPath: inset(l + w / 2, t + h / 2, 0, 0, 0) }], opt);
      mark.animate([{ opacity: 1 }, { opacity: 0 }], { duration: d * 0.6, fill: 'forwards' });
      await s.finished;
    }
    if (dead) return;
    cleanup();
    o.onComplete && o.onComplete();
  }
  run();
  return { done, update: (x) => Object.assign(o, x), destroy() { dead = true; cleanup(); } };
}
