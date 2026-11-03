// Subject core: everything the three subject kinds share. Forms per act, responsive placement (the subject sits opposite the
// copy on desktop, above it on mobile, fitted to the viewport), damped act, assembly timeline, lit state, the real pointer query
// and the public API the archetype modules use. Kinds only build and update their own GPU objects.
import { clamp, lerp, smoothstep, expoOut, hash01 } from '../util.js';
import { buildLayout, buildScatter, groupOf as layoutGroup, LAYOUT_R } from './layouts.js';

export const K_TOP = 7;                                            // ranked rows kept by the query
const ASSEMBLE = { seconds: 1.6, delayMax: 0.4, scatterRadius: 9 };   // scatter-to-form, measured from a reference site, 2026-11
export const MORPH = { damp: 0.085, stagger: 0.32, arcAmp: 0.9 };
export const POINTER = { lerp: 0.05, tiltMax: 0.3, queryK: 5, litLerp: 0.12, litStep: 0.16 };
const PARK_DAMP = 0.085, STRETCH_DAMP = 0.12, HIDE_DAMP = 0.1;
const DESKTOP_AT = { left: [-0.5, 0], right: [0.5, 0], center: [0, 0], top: [0, 0.5], bottom: [0, -0.6] };
const MOBILE_AT = { top: [0, 0.52], center: [0, 0.12], bottom: [0, -0.5] };
const IDLE = { rate: 1.2, phase: 0.5, threshold: 0.985, level: 0.8 };
const NAME_BASE = 100, NAME_SPAN = 900, NAME_MUL = 37;

/** Fit radius (world units at the origin plane) for a placement. Desktop sides get their half of the viewport. */
function fitRadius(place, view, mobile) {
  const { halfW, halfH } = view;
  if (mobile) return place.mobile === 'center' ? Math.min(halfW * 0.9, halfH * 0.4) : Math.min(halfW * 0.88, halfH * 0.28);
  switch (place.desktop) {
    case 'left': case 'right': return Math.min(halfW * 0.46, halfH * 0.82);
    case 'center': return Math.min(halfW * 0.75, halfH * 0.78);
    default: return Math.min(halfH * 0.3, halfW * 0.6);
  }
}

export function createCore({ piece, mobile, N }) {
  const M = piece.subject.items, seed = piece.subject.seed;
  const targets = piece.chapters.filter((c) => c.hasTarget);
  const forms = targets.map((c, a) => buildLayout(c.target.layout, N, c.target.k || 4, seed + a * 17, c.target.params || {}));
  if (forms.length < 2) forms.push(forms[0]);
  const keys = targets.map((c) => ({ at: mobile ? MOBILE_AT[c.place.mobile] : DESKTOP_AT[c.place.desktop], place: c.place, pitch: c.place.pitch, yaw: c.place.yaw, scale: c.place.scale, params: c.target.params || {} }));
  if (keys.length < 2) keys.push(keys[0]);
  const scatter = buildScatter(N, seed + 3, ASSEMBLE.scatterRadius);
  const st = { act: 0, cur: 0, tilt: [0, 0], park: 0, parkV: 0, hide: 0, hideV: 0, stretch: 1, stretchV: 1, mask: new Uint8Array(M).fill(1), custom: null, hover: null,
    world: { dust: 1, halo: 1, key: 1, fog: piece.worlds[0].base, palette: piece.worlds[0] }, scan: { ms: 0, top: [], n: M }, drive: null };
  const lit = new Float32Array(M), litTarget = new Float32Array(M);
  const asm = { start: -1, t: 0 };
  const groups = Math.max(1, piece.interaction.groups.length);

  const core = { M, N, forms, keys, scatter, st, lit, litTarget, mobile, asm, nForms: forms.length, kind: piece.subject.kind, live: true, onWorld: null };

  core.view = (camera) => { const d = camera.position.length(), halfH = Math.tan((camera.fov * Math.PI) / 360) * d; return { halfW: halfH * camera.aspect, halfH, dist: d }; };
  core.keyAt = (a, view) => {
    const i = clamp(Math.floor(a), 0, keys.length - 2), t = smoothstep(0, 1, clamp(a - i)), A = keys[i], B = keys[i + 1];
    const sA = (fitRadius(A.place, view, mobile) / LAYOUT_R) * A.scale, sB = (fitRadius(B.place, view, mobile) / LAYOUT_R) * B.scale;
    return { x: lerp(A.at[0], B.at[0], t) * view.halfW, y: lerp(A.at[1], B.at[1], t) * view.halfH, s: lerp(sA, sB, t), pitch: lerp(A.pitch, B.pitch, t), yaw: lerp(A.yaw, B.yaw, t), i0: i, t, A, B };
  };
  /** advance damped state; returns { a, i0, t, key } */
  core.frame = (c, view) => {
    const dt = c.dt, damp = (r) => (c.reduced ? 1 : 1 - Math.pow(1 - r, dt * 60));
    st.cur += (st.act - st.cur) * damp(MORPH.damp);
    st.parkV += (st.park - st.parkV) * damp(PARK_DAMP);
    st.hideV += (st.hide - st.hideV) * damp(HIDE_DAMP);
    st.stretchV += (st.stretch - st.stretchV) * damp(STRETCH_DAMP);
    st.tilt[0] += (c.pointer.x * POINTER.tiltMax - st.tilt[0]) * (c.reduced ? 1 : POINTER.lerp);
    st.tilt[1] += (c.pointer.y * POINTER.tiltMax - st.tilt[1]) * (c.reduced ? 1 : POINTER.lerp);
    if (st.assembleRequested && asm.start < 0) asm.start = c.time;
    asm.t = c.reduced ? 99 : asm.start < 0 ? 0 : c.time - asm.start;
    const a = clamp(st.cur, 0, forms.length - 1), key = core.keyAt(a, view);
    core.last = { key, view };
    key.s *= 1 - st.hideV;   // setHide: shrink the subject away while long copy scrolls through its zone (mobile)
    return { a, i0: key.i0, t: key.t, key };
  };
  core.asmEase = (i) => (asm.t >= 99 ? 1 : asm.start < 0 ? 0 : expoOut(clamp((asm.t - hash01(i + 31) * ASSEMBLE.delayMax) / ASSEMBLE.seconds)));
  core.assembled = () => asm.t > ASSEMBLE.seconds + ASSEMBLE.delayMax;

  /** brute-force nearest search: distFn(i) -> distance (screen units); honours the topic mask. */
  core.query = (distFn) => {
    const t0 = performance.now(), d = [];
    for (let i = 0; i < M; i++) if (st.mask[i]) d.push([distFn(i), i]);
    d.sort((x, y) => x[0] - y[0]);
    st.scan.ms = performance.now() - t0; st.scan.n = d.length;
    st.scan.top = d.slice(0, K_TOP).map(([dist, i]) => ({ i, d: dist }));
    return d;
  };
  /** lit targets: chapter-custom function, else the query's top-K, else a rare idle twinkle; then damp */
  core.litStep = (c, nearest) => {
    const dt = c.dt, time = c.time;
    litTarget.fill(0);
    if (st.custom?.fn) { st.custom.fn(time, litTarget); for (let i = 0; i < M; i++) if (!st.mask[i]) litTarget[i] *= 0.15; }
    else {
      for (let r = 0; r < Math.min(POINTER.queryK, nearest?.length || 0); r++) litTarget[nearest[r][1]] = 1 - r * POINTER.litStep;
      if (!c.pointer.moved) for (let i = 0; i < M; i++) litTarget[i] = Math.max(litTarget[i], 0.5 + 0.5 * Math.sin(time * IDLE.rate + i * IDLE.phase) > IDLE.threshold ? IDLE.level : 0);
    }
    if (st.hover) for (let i = 0; i < M; i++) if (layoutGroup(i, M, st.hover.k) === st.hover.g) litTarget[i] = Math.max(litTarget[i], 0.75);
    const k = c.reduced ? 1 : 1 - Math.pow(1 - POINTER.litLerp, dt * 60);
    for (let i = 0; i < M; i++) lit[i] += (litTarget[i] - lit[i]) * k;
  };

  // ---- public API (what archetype modules and the bespoke hook see)
  const api = {
    live: true, kind: core.kind, M, st, core,
    setAct(a) { st.act = a; },
    assemble() { st.assembleRequested = true; },
    setWorld(w) { Object.assign(st.world, w); core.onWorld?.(st.world, w); },
    setMask(m) { st.mask = m; },
    setCustom(c) { st.custom = c; },
    setHover(g, k) { st.hover = g == null ? null : { g, k }; },
    setPark(v) { st.park = v ? 1 : 0; },
    setHide(v) { st.hide = v ? 1 : 0; },
    /** subject bounding box in viewport px (for verify-piece collision/void checks); null before the first frame */
    box() {
      const L = core.last; if (!L) return null;
      const { key, view } = L, r = ((key.s * LAYOUT_R) / view.halfH) * (innerHeight / 2) * (1 - st.hideV);
      return { x: innerWidth * (0.5 + key.x / (2 * view.halfW)) - r, y: innerHeight * (0.5 - (key.y - st.parkV * view.halfH * 0.5) / (2 * view.halfH)) - r, w: 2 * r, h: 2 * r };
    },
    setDrive(d) { st.drive = d; st.stretch = d?.stretch ?? 1; },
    groupOf: (i, k = groups) => layoutGroup(i, M, k),
    itemName(i) { const names = piece.interaction.names, g = layoutGroup(i, M, groups); return `${names[g] || 'item'}-${NAME_BASE + ((i * NAME_MUL) % NAME_SPAN)}`; },
  };
  core.api = api;
  return core;
}

/** Inert stand-in used when WebGL is off: DOM figures keep working without a scene. */
export function createNullSubject(piece) {
  const M = piece.subject.items, nothing = () => {};
  const groups = Math.max(1, piece.interaction.groups.length);
  return { live: false, kind: 'none', M, st: { scan: { ms: 0, top: [], n: M }, mask: new Uint8Array(M).fill(1) }, setAct: nothing, assemble: nothing, setWorld: nothing, setMask: nothing, setCustom: nothing,
    setHover: nothing, setPark: nothing, setHide: nothing, box: () => null, setDrive: nothing, groupOf: (i, k = groups) => layoutGroup(i, M, k),
    itemName(i) { const names = piece.interaction.names, g = layoutGroup(i, M, groups); return `${names[g] || 'item'}-${NAME_BASE + ((i * NAME_MUL) % NAME_SPAN)}`; } };
}
