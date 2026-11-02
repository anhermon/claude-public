// loader/hole-expand: dark screen with a small aperture and a % counter; the aperture scales ~15x to reveal the page.
// measured from public reference sites, 2026-11: scale 1 -> 15, 0.25-0.5 s, ease-in (accelerating).
import { $, resolve, reducedMotion, tween, fn, EASE } from '../core/easing.js';
export const DEFAULTS = {
  size: 14,                // vmin, resting aperture
  shape: 'circle',         // 'circle' | 'squircle'
  scale: 15,               // 1 -> 15: measured from public reference sites, 2026-11 (auto-raised so the hole always covers the viewport diagonal)
  duration: 0.4,           // 0.25-0.5 s: measured from public reference sites, 2026-11
  ease: EASE.in,           // ease-in, accelerating: measured from public reference sites, 2026-11
  minDuration: 1.2,        // counter runtime (~1.0 s observed)
  waitFor: null,
  autoExpand: true,
  bg: '#030303',
  ring: 'rgba(255,255,255,.22)',
  label: 'LOADING',
  counterFade: 0.18,       // s, counter fades as the hole starts to open
  zIndex: 9999,
  lockScroll: true,
};
const MS = 1000;
const SQUIRCLE_RADIUS = '28%';  // measured from public reference sites, 2026-11 radius
export function init(target, options = {}) {
  const host = $(target) || document.body;
  const o = resolve(host, DEFAULTS, { duration: '--ck-dur-hole' }, options);
  const reduced = reducedMotion(o);
  const wrap = document.createElement('div');
  wrap.setAttribute('aria-hidden', 'true');
  wrap.style.cssText = `position:fixed;inset:0;z-index:${o.zIndex};overflow:hidden;pointer-events:all`;
  const hole = document.createElement('div');
  const r = o.shape === 'circle' ? '50%' : SQUIRCLE_RADIUS;
  hole.style.cssText = `position:absolute;left:50%;top:50%;width:${o.size}vmin;height:${o.size}vmin;margin:-${o.size / 2}vmin 0 0 -${o.size / 2}vmin;border-radius:${r};box-shadow:0 0 0 200vmax ${o.bg}, inset 0 0 0 1px ${o.ring};will-change:transform`;
  const ui = document.createElement('div');
  ui.style.cssText = `position:absolute;left:0;right:0;bottom:0;padding:0 clamp(20px,4vw,56px) clamp(20px,4vh,44px);display:flex;justify-content:space-between;align-items:flex-end;color:var(--ck-loader-fg,#f4f1ea);font:500 12px/1 var(--ck-font-mono);letter-spacing:.2em`;
  const lbl = Object.assign(document.createElement('span'), { textContent: o.label });
  const num = Object.assign(document.createElement('span'), { textContent: '000%' });
  num.style.cssText = 'font-size:clamp(40px,8vw,112px);letter-spacing:-.02em;font-variant-numeric:tabular-nums;font-weight:400';
  const bar = document.createElement('div');
  bar.style.cssText = `position:absolute;left:0;right:0;bottom:0;height:1px;background:var(--ck-loader-fg,#f4f1ea);transform-origin:0 50%;transform:scaleX(0);opacity:.6`;
  ui.append(lbl, num);
  wrap.append(hole, ui, bar);
  host.append(wrap);
  const live = document.createElement('div');
  live.setAttribute('role', 'status'); live.textContent = 'Loading';
  live.style.cssText = 'position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0)';
  host.append(live);
  if (o.lockScroll) document.documentElement.style.overflow = 'hidden';

  let progress = 0, tw = null, dead = false, opened = false, ready = !o.waitFor, resolveDone;
  const done = new Promise((res) => (resolveDone = res));
  const setProgress = (p) => { progress = Math.max(progress, Math.min(1, p)); num.textContent = String(Math.round(progress * 100)).padStart(3, '0') + '%'; bar.style.transform = `scaleX(${progress})`; };
  const cleanup = () => { wrap.remove(); live.remove(); if (o.lockScroll) document.documentElement.style.overflow = ''; resolveDone(true); };
  function expand() {
    if (dead || opened) return done;
    opened = true; setProgress(1);
    if (reduced) { o.onReveal && o.onReveal(); o.onComplete && o.onComplete(); cleanup(); return done; }
    const size = (Math.min(innerWidth, innerHeight) * o.size) / 100;
    const cover = (Math.hypot(innerWidth, innerHeight) / size) * 1.05;  // never leave a corner of the aperture ring visible
    const S = Math.max(o.scale, cover);
    ui.animate([{ opacity: 1 }, { opacity: 0 }], { duration: o.counterFade * MS, fill: 'forwards' });
    bar.animate([{ opacity: 0.6 }, { opacity: 0 }], { duration: o.counterFade * MS, fill: 'forwards' });
    o.onReveal && o.onReveal();
    hole.animate([{ transform: 'scale(1)' }, { transform: `scale(${S})` }], { duration: o.duration * MS, easing: o.ease, fill: 'forwards' })
      .finished.then(() => { if (dead) return; cleanup(); o.onComplete && o.onComplete(); }, () => {});
    return done;
  }
  const maybe = () => { if (o.autoExpand && ready && progress >= 1) expand(); };
  if (!reduced) {
    tw = tween({ duration: o.minDuration, ease: fn.power3Out, onUpdate: setProgress, onDone: maybe });
    if (o.waitFor) Promise.all([].concat(o.waitFor)).then(() => { ready = true; maybe(); });
  } else if (o.autoExpand) expand();
  return { setProgress, expand, done, update: (x) => Object.assign(o, x), destroy() { dead = true; tw && tw.cancel(); cleanup(); } };
}
