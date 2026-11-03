// Per-chapter "worlds": floor-glow palette + scene extras, tweened over WORLD_TWEEN_S (time-driven, never scrubbed).
import { hex } from './util.js';

const WORLD_TWEEN_S = 0.7, CHANNEL_MAX = 255;   // tween overshoot must not push a channel past 255 (-> 7-digit hex)
const mixc = (a, b, t) => { const A = hex(a), B = hex(b); return '#' + A.map((v, i) => Math.max(0, Math.min(CHANNEL_MAX, Math.round((v + (B[i] - v) * t) * CHANNEL_MAX))).toString(16).padStart(2, '0')).join(''); };
const mixn = (a, b, t) => a + (b - a) * t;
export function lerpPalette(A, B, t) {
  const ga = A.glows[0], gb = B.glows[0];
  return { base: mixc(A.base, B.base, t), accent: mixc(A.accent, B.accent, t), grain: mixn(A.grain, B.grain, t),
    glows: [{ at: ga.at.map((v, i) => mixn(v, gb.at[i], t)), radius: ga.radius.map((v, i) => mixn(v, gb.radius[i], t)), stops: ga.stops.map(([pos, c], i) => [mixn(pos, gb.stops[i][0], t), mixc(c, gb.stops[i][1], t)]) }] };
}
const ease = (t) => 1 - Math.pow(1 - t, 3);

/** createWorlds({ stage, subject, reduced, worlds }) -> { to(index) }; writes html[data-world] and the css accent var */
export function createWorlds({ stage, subject, reduced, worlds }) {
  let cur = 0, shown = { p: worlds[0], x: worlds[0].x }, raf = 0;
  const apply = (p, x) => { stage.setBackdrop(p); subject.setWorld({ fog: p.base, palette: p, ...x }); };
  return { get index() { return cur; }, to(i) {
    i = Math.max(0, Math.min(worlds.length - 1, i));
    if (i === cur) return; cur = i;
    const target = worlds[i], from = shown.p, fx = shown.x;
    document.documentElement.dataset.world = target.light ? 'light' : 'dark';
    cancelAnimationFrame(raf);
    if (reduced) { shown = { p: target, x: target.x }; apply(target, target.x); return; }
    const t0 = performance.now();
    const step = (now) => {
      const k = Math.min(1, (now - t0) / (WORLD_TWEEN_S * 1000)), e = ease(k);
      const p = lerpPalette(from, target, e), x = { dust: mixn(fx.dust, target.x.dust, e), halo: mixn(fx.halo, target.x.halo, e), key: mixn(fx.key, target.x.key, e) };
      apply(p, x); shown = { p, x };
      if (k < 1) raf = requestAnimationFrame(step); else shown = { p: target, x: target.x };
    };
    raf = requestAnimationFrame(step);
  } };
}
