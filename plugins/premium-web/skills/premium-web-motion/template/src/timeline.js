// timeline: ONE pinned stage driven by scroll. Scroll progress is SCRUBBED (written to --stage-p, rail travel);
// chapter colour hand-offs are TIME-DRIVEN tweens fired on chapter change; step crossfades are CSS transitions.
// The scrub-vs-time split is itself measured: public reference sites scrub the object/camera and time-drive the palette.
import { EASE, clamp, damp, settled, resolveEl, resolveAll, tween, loop, subscribe, sectionProgress, isReduced, singleton, opts } from './util/helpers.js';

export const DEFAULTS = {
  chapters: [],        // [{id, bg, fg, accent, at?}]; `at` = start progress 0..1, default equal shares
  handoff: 0.7,        // s, palette tween per chapter change: 0.6-0.8 s, measured from public reference sites, 2026-11; +-0.15 s
  vars: { bg: '--stage-bg', fg: '--stage-fg', accent: '--stage-accent' }, // css variables written on the stage element
  damp: 0.09,          // per-60Hz-frame lerp of progress: 0.08-0.1, measured from public reference sites, 2026-11
  rail: null,          // selector of a track inside the stage translated horizontally by progress (pinned rail, scrub ~1 s)
  steps: null,         // selector of step items inside the stage; one gets [data-active] per progress slice (stepper, 0.3 s crossfade in css)
  railEnd: 1,          // progress at which the rail has travelled fully
  onChapter: null,     // (index, chapter) => void
  scroll: null,        // optional createScroll() instance; native scroll otherwise
  reduced: undefined,  // test override of prefers-reduced-motion
};
const HEX_SHORT = 4;
const RGB_MAX = 255;

function parse(hex) {
  let h = hex.replace('#', '');
  if (hex.length === HEX_SHORT) h = [...h].map((c) => c + c).join('');
  const n = parseInt(h, 16);
  return [(n >> 16) & RGB_MAX, (n >> 8) & RGB_MAX, n & RGB_MAX];
}

export function pinStage(target, options = {}) {
  const el = resolveEl(target);
  return singleton(el, 'stage', () => create(el, opts(DEFAULTS, options)));
}

function create(el, o) {
  const reduced = isReduced(o);
  const chapters = o.chapters.map((c, i, a) => ({ at: i / a.length, ...c }));
  const track = o.rail ? el.querySelector(o.rail) : null;
  const steps = o.steps ? resolveAll(o.steps, el) : [];
  const pin = el.firstElementChild;
  let target = 0, cur = 0, index = -1, tw = null, dead = false;
  let shown = chapters[0] ? ['bg', 'fg', 'accent'].map((k) => parse(chapters[0][k])) : [];

  const KEYS = Object.keys(o.vars);
  const paintColours = (rgbs) => KEYS.forEach((k, i) => rgbs[i] && el.style.setProperty(o.vars[k], `rgb(${rgbs[i].map(Math.round).join(',')})`)); // sRGB lerp: fine over 0.7 s
  function toChapter(i) {
    if (i === index || !chapters[i]) return;
    index = i;
    el.dataset.chapter = chapters[i].id;
    el.style.setProperty('--stage-chapter', String(i));
    const next = KEYS.map((k) => parse(chapters[i][k]));
    tw && tw.cancel();
    if (reduced || o.handoff <= 0) { shown = next; paintColours(next); } else {
      const from = shown;
      tw = tween({ duration: o.handoff, ease: EASE.power3Out, onUpdate: (e) => {
        shown = next.map((n, k) => from[k].map((v, c) => v + (n[c] - v) * e));
        paintColours(shown);
      } });
    }
    o.onChapter?.(i, chapters[i]);
  }
  function paint() {
    el.style.setProperty('--stage-p', cur.toFixed(4));
    let i = 0;
    chapters.forEach((c, k) => { if (cur >= c.at - 1e-6) i = k; });
    if (chapters.length) toChapter(i);
    if (track) {
      const travel = Math.max(0, track.scrollWidth - innerWidth);
      track.style.transform = `translate3d(${(-travel * clamp(cur / o.railEnd)).toFixed(1)}px,0,0)`;
    }
    if (steps.length) {
      const k = Math.min(steps.length - 1, Math.floor(cur * steps.length));
      steps.forEach((s, n) => (n === k ? s.setAttribute('data-active', '') : s.removeAttribute('data-active')));
    }
  }
  const lp = loop((_, dt) => { cur = damp(cur, target, o.damp, dt); if (settled(cur, target)) cur = target; paint(); return cur !== target; });
  const measure = () => { target = sectionProgress(el); if (reduced) { cur = target; paint(); } else lp.wake(); };

  let unsub = () => {};
  if (reduced) {      // no pin, no scrub: stacked content, first chapter palette, steps all visible, rail scrolls natively
    el.style.height = 'auto';
    if (pin) pin.style.position = 'static';
    if (track) track.parentElement.style.overflowX = 'auto';
    steps.forEach((s) => s.setAttribute('data-active', ''));
    toChapter(0);
  } else { target = cur = sectionProgress(el); paint(); unsub = subscribe(o.scroll, measure); }
  return {
    get progress() { return cur; }, get chapter() { return index; }, chapters,
    destroy() { dead = true; lp.stop(); tw && tw.cancel(); unsub(); },
    update(next = {}) { Object.assign(o, next); measure(); },
  };
}
