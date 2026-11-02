// text/typewriter: mono type-on with a block caret. measured from public reference sites, 2026-11: 1 char / 35 ms.
// The not-yet-typed remainder stays in the flow as visibility:hidden, so layout never shifts.
import { $, resolve, reducedMotion } from '../core/easing.js';
export const DEFAULTS = {
  trigger: 'load',
  charMs: 35,          // 1 char per 35 ms: measured from public reference sites, 2026-11
  delay: 0,
  caret: true,
  caretBlinkMs: 1060,  // classic terminal blink period
  caretHideOnDone: false,
  mono: true,          // forces the kit mono stack; 'false' keeps the element font
  viewThreshold: 0.5,
};
const MS = 1000;
export function init(target, options = {}) {
  const el = $(target);
  if (el.__ckType) el.__ckType.destroy();
  const o = resolve(el, DEFAULTS, {}, options);
  const reduced = reducedMotion(o);
  const text = (el.dataset.ckText || el.textContent).trim();
  el.dataset.ckText = text;
  el.setAttribute('aria-label', text);
  el.textContent = '';
  if (o.mono) el.style.fontFamily = 'var(--ck-font-mono)';
  const mk = (css, style) => { const s = document.createElement('span'); s.setAttribute('aria-hidden', 'true'); if (css) s.className = css; if (style) s.style.cssText = style; return s; };
  const typed = mk(), caret = mk('ck-caret', 'position:relative;display:inline-block;width:0'), rest = mk(null, 'visibility:hidden');
  const bar = mk(null, 'position:absolute;left:0.08em;top:0.12em;width:0.55em;height:1em;background:currentColor;animation:ck-blink ' + o.caretBlinkMs + 'ms steps(1) infinite');
  caret.append(bar);
  if (!document.getElementById('ck-caret-style')) {
    const st = document.createElement('style'); st.id = 'ck-caret-style';
    st.textContent = '@keyframes ck-blink{0%,49%{opacity:1}50%,100%{opacity:0}}@media (prefers-reduced-motion: reduce){.ck-caret span{animation:none!important}}';
    document.head.append(st);
  }
  el.append(typed, o.caret ? caret : '', rest);
  let raf = 0, io = null, played = false, dead = false;
  const show = (n) => { typed.textContent = text.slice(0, n); rest.textContent = text.slice(n); };
  const finish = () => { show(text.length); if (o.caretHideOnDone) caret.remove(); o.onComplete && o.onComplete(); };
  function reset() { cancelAnimationFrame(raf); played = false; if (reduced) { show(text.length); played = true; } else show(0); }
  function play() {
    if (dead || played) return Promise.resolve();
    played = true;
    if (reduced) { finish(); return Promise.resolve(); }
    return new Promise((res) => {
      const t0 = performance.now() + o.delay * MS;
      const frame = (now) => {
        if (dead) return res();
        const n = Math.min(text.length, Math.max(0, Math.floor((now - t0) / o.charMs) + (now >= t0 ? 1 : 0)));
        show(n);
        if (n < text.length) raf = requestAnimationFrame(frame); else { finish(); res(); }
      };
      raf = requestAnimationFrame(frame);
    });
  }
  function destroy() { dead = true; cancelAnimationFrame(raf); io && io.disconnect(); el.textContent = text; el.style.fontFamily = ''; delete el.__ckType; }
  reset();
  if (!reduced && o.trigger === 'view') {
    io = new IntersectionObserver((es) => { if (es.some((e) => e.isIntersecting)) { io.disconnect(); play(); } }, { threshold: o.viewThreshold });
    io.observe(el);
  } else if (o.trigger === 'load') requestAnimationFrame(() => play());
  return (el.__ckType = { play, reset, destroy, update: (x) => Object.assign(o, x) });
}
