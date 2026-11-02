// transition/curtain-overlap: the next section slides over a sticky previous one (rounded top, shadow);
// the previous scales, dims and drifts up while it is covered. Colour hand-off = whatever backgrounds the sections have.
import { VERSION, EASE, clamp, lerp, damp, settled, resolveEl, resolveAll, make, isReduced, singleton, loop, subscribe, cssNum, opts } from '../util/helpers.js';

export { VERSION };
export const DEFAULTS = {
  sections: ':scope > section', // curtain panels, in stacking order
  radius: 24,        // px, top corners of the covering panel; 16-28 px: measured from public reference sites, 2026-11; +-4 px
  scaleTo: 0.96,     // previous panel scales to .96 when fully covered: measured from public reference sites, 2026-11
  dim: 0.55,         // opacity of the black shade over the covered panel (observed "dims"; value tuned by eye)
  parallax: 0.08,    // covered panel drifts up by this fraction of the viewport height (our addition for depth)
  shadow: '0 -28px 70px rgba(0,0,0,.35)', // soft cast shadow of the covering panel (depth cue)
  damp: 0.14,        // per-frame lerp of the local progress, 60 Hz basis; contract damped lerp 0.08-0.1, slightly looser here because progress is local
  origin: '50% 0%',  // transform-origin of the covered panel
  backdrop: null,    // css colour shown behind the receding panel (default: leave as is)
  onChange: null,    // (activeIndex) => void when the dominant panel changes
  scroll: null,      // createScroll() instance (core/scroll); null = native scroll events
  reduced: undefined, // test override of prefers-reduced-motion
};
const SHADE_Z = 2; // above panel content, below nothing else we own
const COVER_DONE = 0.5; // panel i+1 counts as active once it covers this much of panel i

export function init(target, options = {}) {
  const root = resolveEl(target);
  return singleton(root, 'curtain', () => create(root, opts(DEFAULTS, options)));
}

function create(root, o) {
  const panels = resolveAll(o.sections, root).length ? resolveAll(o.sections, root) : [...root.children];
  const reduced = isReduced(o);
  const n = panels.length;
  const saved = panels.map((p) => p.getAttribute('style'));
  const savedRoot = root.getAttribute('style');
  const cur = new Array(n).fill(0), tgt = new Array(n).fill(0);
  const shades = [];
  let active = -1, dead = false;

  if (o.backdrop) root.style.background = o.backdrop;
  panels.forEach((p, i) => {
    p.style.position = i < n - 1 && !reduced ? 'sticky' : 'relative';
    p.style.zIndex = String(i + 1);
    p.style.overflow = 'hidden';
    p.style.transformOrigin = o.origin;
    if (i > 0) p.style.boxShadow = o.shadow;
    if (i < n - 1 && !reduced) {
      const s = make('div', { 'aria-hidden': 'true', 'data-ck-shade': '' }, { position: 'absolute', inset: '0', background: '#000', opacity: '0', pointerEvents: 'none', zIndex: String(SHADE_Z) }, p);
      shades.push(s);
    } else shades.push(null);
  });

  function layout() {
    const vh = window.innerHeight;
    panels.forEach((p, i) => {
      if (i >= n - 1 || reduced) return;
      p.style.top = `${Math.min(0, vh - p.offsetHeight)}px`; // taller-than-viewport panels stick once their bottom is reached
    });
  }
  function measure() {
    const vh = window.innerHeight;
    for (let i = 0; i < n - 1; i++) tgt[i] = clamp((vh - panels[i + 1].getBoundingClientRect().top) / vh);
  }
  function paint(vh) {
    let a = 0;
    for (let i = 0; i < n - 1; i++) {
      const p = cur[i];
      const el = panels[i];
      const k = EASE.power2Out(p);
      el.style.transform = p === 0 ? '' : `translate3d(0,${(-o.parallax * vh * p).toFixed(2)}px,0) scale(${lerp(1, o.scaleTo, p).toFixed(4)})`;
      el.style.borderRadius = `${i > 0 ? o.radius : 0}px ${i > 0 ? o.radius : 0}px ${(o.radius * p).toFixed(2)}px ${(o.radius * p).toFixed(2)}px`; // lower corners round as it recedes
      shades[i].style.opacity = (o.dim * k).toFixed(3);
      el.style.setProperty('--ck-curtain-p', p.toFixed(4));
      if (p >= COVER_DONE) a = i + 1;
    }
    root.style.setProperty('--ck-curtain-index', String(a));
    if (a !== active) { active = a; root.dataset.ckActive = String(a); o.onChange?.(a); }
  }
  const lp = loop((_, dt) => {
    let moving = false;
    for (let i = 0; i < n - 1; i++) {
      cur[i] = o.damp > 0 ? damp(cur[i], tgt[i], o.damp, dt) : tgt[i];
      if (!settled(cur[i], tgt[i])) moving = true; else cur[i] = tgt[i];
    }
    paint(window.innerHeight);
    return moving;
  });
  panels.forEach((p, i) => i > 0 && (p.style.borderRadius = `${o.radius}px ${o.radius}px 0 0`));
  const onScroll = () => { if (!reduced && !dead) { measure(); lp.wake(); } };

  let unsub = () => {}, ro = null;
  if (reduced) { root.dataset.ckActive = '0'; } else {
    layout(); measure(); cur.splice(0, n, ...tgt); paint(window.innerHeight);
    unsub = subscribe(o.scroll, () => { layout(); onScroll(); });
    ro = new ResizeObserver(() => { layout(); onScroll(); });
    panels.forEach((p) => ro.observe(p));
  }

  return {
    panels,
    get active() { return active; },
    progress: (i) => cur[i] ?? 0,
    update(next = {}) { Object.assign(o, next); panels.forEach((p, i) => i > 0 && (p.style.boxShadow = o.shadow)); layout(); onScroll(); if (!reduced) paint(window.innerHeight); },
    destroy() {
      dead = true; lp.stop(); unsub(); ro?.disconnect();
      shades.forEach((s) => s?.remove());
      panels.forEach((p, i) => (saved[i] == null ? p.removeAttribute('style') : p.setAttribute('style', saved[i])));
      savedRoot == null ? root.removeAttribute('style') : root.setAttribute('style', savedRoot);
      root.style.removeProperty('--ck-curtain-index');
      delete root.dataset.ckActive;
    },
  };
}
