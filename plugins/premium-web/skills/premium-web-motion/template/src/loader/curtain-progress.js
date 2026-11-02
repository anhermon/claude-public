// loader/curtain-progress: solid curtain, tracked wordmark, 1 px progress line, then the curtain lifts and the
// wordmark FLIPs into the header slot. measured from public reference sites, 2026-11, solid-curtain preloader.
import { $, resolve, reducedMotion, tween, fn, EASE } from '../core/easing.js';
export const DEFAULTS = {
  wordmark: 'WORDMARK',
  dock: null,              // element (or selector) the wordmark flies into; null = wordmark lifts with the curtain
  minDuration: 1.0,        // progress line 0 -> 100% in 0.8-1.2 s: measured from public reference sites, 2026-11
  waitFor: null,           // Promise | Promise[] that must also resolve before the lift (real asset loading)
  autoLift: true,
  liftDuration: 0.7,       // translateY(-100%) 0.7 s: measured from public reference sites, 2026-11
  liftEase: EASE.expoInOut, // expo.inOut: measured from public reference sites, 2026-11
  revealAt: 0.3,           // onReveal fires at 30% of the lift so the hero text overlaps the curtain (tuned by eye)
  lineWidth: 120,          // px, 1 px tall progress line (~60 px observed; widened for legibility)
  wordmarkFadeIn: 0.6,     // s, blur-fade of the wordmark at start
  zIndex: 9999,
  lockScroll: true,
};
const MS = 1000;
const CSS = 'position:fixed;';
export function init(target, options = {}) {
  const host = $(target) || document.body;
  const o = resolve(host, DEFAULTS, { liftDuration: '--ck-dur-curtain' }, options);
  const reduced = reducedMotion(o);
  const dock = $(o.dock);
  const mk = (css) => { const d = document.createElement('div'); d.style.cssText = css; d.setAttribute('aria-hidden', 'true'); return d; };
  const curtain = mk(`${CSS}inset:0;z-index:${o.zIndex};background:var(--ck-loader-bg);will-change:transform`);
  const mark = mk(`${CSS}left:50%;top:50%;z-index:${o.zIndex + 1};transform:translate(-50%,-50%);color:var(--ck-loader-fg);font:500 14px/1 var(--ck-font-sans);letter-spacing:.32em;text-transform:uppercase;white-space:nowrap;transform-origin:50% 50%`);
  mark.textContent = o.wordmark;
  const lineWrap = mk(`${CSS}left:50%;top:calc(50% + 26px);width:${o.lineWidth}px;height:1px;margin-left:${-o.lineWidth / 2}px;z-index:${o.zIndex + 1};background:rgba(255,255,255,.18)`);
  const line = mk('position:absolute;inset:0;background:var(--ck-loader-fg);transform-origin:0 50%;transform:scaleX(0)');
  lineWrap.append(line);
  const live = document.createElement('div');          // announce loading politely for AT, hidden visually
  live.setAttribute('role', 'status'); live.textContent = 'Loading';
  live.style.cssText = 'position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0)';
  host.append(curtain, mark, lineWrap, live);
  if (o.lockScroll) document.documentElement.style.overflow = 'hidden';
  if (dock) dock.style.visibility = 'hidden';

  let progress = 0, tw = null, dead = false, lifted = false, ready = !o.waitFor, resolveDone;
  const done = new Promise((r) => (resolveDone = r));
  const setProgress = (p) => { progress = Math.max(progress, Math.min(1, p)); line.style.transform = `scaleX(${progress})`; };
  const cleanup = () => {
    [curtain, mark, lineWrap, live].forEach((e) => e.remove());
    if (dock) dock.style.visibility = '';
    if (o.lockScroll) document.documentElement.style.overflow = '';
    resolveDone(true);
  };
  function lift() {
    if (dead || lifted) return done;
    lifted = true;
    setProgress(1);
    const d = (reduced ? 0 : o.liftDuration) * MS;
    if (reduced) { o.onReveal && o.onReveal(); o.onComplete && o.onComplete(); cleanup(); return done; }
    const opt = { duration: d, easing: o.liftEase, fill: 'forwards' };
    curtain.animate([{ transform: 'translateY(0)' }, { transform: 'translateY(-100%)' }], opt);
    lineWrap.animate([{ opacity: 1 }, { opacity: 0 }], { duration: d * 0.3, fill: 'forwards' });
    let wm;
    if (dock) {                                         // FLIP: first = wordmark box, last = dock box
      const f = mark.getBoundingClientRect(), l = dock.getBoundingClientRect();
      const dx = l.left + l.width / 2 - (f.left + f.width / 2), dy = l.top + l.height / 2 - (f.top + f.height / 2), s = l.width / f.width;
      wm = mark.animate([{ transform: 'translate(-50%,-50%)' }, { transform: `translate(calc(-50% + ${dx}px), calc(-50% + ${dy}px)) scale(${s})` }], opt);
    } else {
      wm = mark.animate([{ transform: 'translate(-50%,-50%)' }, { transform: 'translate(-50%,calc(-50% - 100vh))' }], opt);
    }
    setTimeout(() => !dead && o.onReveal && o.onReveal(), d * o.revealAt);
    wm.finished.then(() => { if (dead) return; cleanup(); o.onComplete && o.onComplete(); }, () => {});
    return done;
  }
  function maybeLift() { if (o.autoLift && ready && progress >= 1) lift(); }
  if (!reduced) {
    mark.animate([{ opacity: 0, filter: 'blur(8px)' }, { opacity: 1, filter: 'blur(0px)' }], { duration: o.wordmarkFadeIn * MS, easing: EASE.expoOut, fill: 'backwards' });
    tw = tween({ duration: o.minDuration, ease: fn.power3Out, onUpdate: (e) => setProgress(e), onDone: maybeLift });
    if (o.waitFor) Promise.all([].concat(o.waitFor)).then(() => { ready = true; maybeLift(); });
  } else { setProgress(1); if (o.autoLift) lift(); }
  return {
    setProgress, lift, done,
    update: (x) => Object.assign(o, x),
    destroy() { dead = true; tw && tw.cancel(); cleanup(); },
  };
}
