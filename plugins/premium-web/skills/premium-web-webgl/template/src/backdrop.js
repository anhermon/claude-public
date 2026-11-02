// gl/backdrop: the "floor glow" as a full-screen shader quad drawn inside the scene.
// Being a real opaque object it is what transmissive glass refracts, so the glass picks up the glow.
// Palette = CSS-radial-gradient semantics (stop positions are fractions of the ellipse radii), so the
// same object also renders the CSS poster fallback. Shader adds dither/grain (no banding on dark ramps).
import { hex, rgbCss, lerp } from './util.js';

const MAX_GLOWS = 2;
const STOPS = 4;
const BREATH_AMP = 0.05;   // glow strength swing: "breathes subtly 2->6 s" (measured from public reference sites, 2026-11)
const BREATH_HZ = 0.16;    // ~6 s period
const DEFAULT_GRAIN = 0.05; // grain amplitude; ~6% noise (measured from public reference sites, 2026-11)

/** warm fire: `radial-gradient(ellipse 80% 55% at 50% 100%, #fce7aa, #f04f24 30%, #8a0207 55%, #020101 80%)` */
export const FIRE = {
  base: '#020101', accent: '#f04f24', grain: DEFAULT_GRAIN,
  glows: [{ at: [0.5, 1.0], radius: [0.8, 0.55], stops: [[0, '#fce7aa'], [0.3, '#f04f24'], [0.55, '#8a0207'], [0.8, '#020101']] }],
};
/** aurora: violet top-left, teal bottom-right on teal-black */
export const AURORA = {
  base: '#02070a', accent: '#6ee7a0', grain: DEFAULT_GRAIN,
  glows: [
    { at: [0.0, 0.0], radius: [0.62, 0.55], stops: [[0, '#4a3aa8'], [0.35, '#251f66'], [0.7, '#0a0c24'], [1, '#02070a']] },
    { at: [1.0, 1.0], radius: [0.7, 0.5], stops: [[0, '#3b8a8f'], [0.35, '#1f5a60'], [0.7, '#0a2226'], [1, '#02070a']] },
  ],
};
/** cold blue alt for chapter hand-offs (electric-blue accent family, measured from public reference sites, 2026-11) */
export const COBALT = {
  base: '#010208', accent: '#4f7dff', grain: DEFAULT_GRAIN,
  glows: [{ at: [0.5, 1.0], radius: [0.8, 0.55], stops: [[0, '#cfe0ff'], [0.3, '#3a63ff'], [0.55, '#0a1a7a'], [0.8, '#010208']] }],
};

/** Normalise a palette into flat arrays: 2 glows x 4 stops. */
export function compile(p) {
  const glows = [];
  for (let g = 0; g < MAX_GLOWS; g++) {
    const src = p.glows[g];
    if (!src) { glows.push({ geo: [0.5, 1, 1, 1], pos: [0, 0.3, 0.6, 1], col: Array(STOPS).fill([0, 0, 0]), str: 0 }); continue; }
    const st = src.stops;
    glows.push({
      geo: [src.at[0], src.at[1], src.radius[0], src.radius[1]],
      pos: [0, 1, 2, 3].map((i) => st[Math.min(i, st.length - 1)][0]),
      col: [0, 1, 2, 3].map((i) => hex(st[Math.min(i, st.length - 1)][1])),
      str: 1,
    });
  }
  return { base: hex(p.base), grain: p.grain ?? DEFAULT_GRAIN, glows, accent: hex(p.accent || '#ffffff') };
}

const pct = (f) => `${+(f * 100).toFixed(2)}%`;
/** CSS background-image equivalent (poster fallback). */
export function backdropToCss(p) {
  const layers = p.glows.map((g) => {
    const st = g.stops.map(([pos, c], i) => (i === g.stops.length - 1 ? `${rgbCss(hex(c), 0)} ${pct(pos)}` : `${c} ${pct(pos)}`));
    return `radial-gradient(ellipse ${pct(g.radius[0])} ${pct(g.radius[1])} at ${pct(g.at[0])} ${pct(g.at[1])}, ${st.join(', ')})`;
  });
  return `${layers.join(', ')}, ${p.base}`;
}

const VERT = /* glsl */`
varying vec2 vUv;
void main(){ vUv = uv; gl_Position = vec4(position.xy, 1.0, 1.0); }`;
const FRAG = /* glsl */`
precision highp float;
varying vec2 vUv;
uniform vec3 uBase; uniform vec4 uGeo[2]; uniform vec4 uPos[2]; uniform vec3 uCol[8]; uniform vec2 uStr;
uniform float uTime, uGrain, uBreath;
float hash(vec2 p){ p = fract(p * vec2(443.897, 441.423)); p += dot(p, p.yx + 19.19); return fract((p.x + p.y) * p.x); }
vec3 ramp4(vec3 a, vec3 b, vec3 c, vec3 d, vec4 p, float t){
  vec3 col = a;
  col = mix(col, b, clamp((t - p.x) / max(p.y - p.x, 1e-4), 0., 1.));
  col = mix(col, c, clamp((t - p.y) / max(p.z - p.y, 1e-4), 0., 1.));
  return mix(col, d, clamp((t - p.z) / max(p.w - p.z, 1e-4), 0., 1.));
}
void main(){
  vec2 st = vec2(vUv.x, 1. - vUv.y);
  vec3 col = uBase;
  float br = 1. + uBreath * sin(uTime * ${(2 * Math.PI * BREATH_HZ).toFixed(4)});
  vec2 q0 = (st - uGeo[0].xy) / uGeo[0].zw;
  col += max(ramp4(uCol[0], uCol[1], uCol[2], uCol[3], uPos[0], length(q0)) - uBase, 0.) * uStr.x * br;
  vec2 q1 = (st - uGeo[1].xy) / uGeo[1].zw;
  col += max(ramp4(uCol[4], uCol[5], uCol[6], uCol[7], uPos[1], length(q1)) - uBase, 0.) * uStr.y * br;
  col += (hash(gl_FragCoord.xy + fract(uTime * 7.31) * 113.) - .5) * uGrain;
  gl_FragColor = vec4(col, 1.);
}`;

/** createBackdrop(THREE, palette, {palette2}) -> { mesh, setMix(t), setPalette(p, p2), update(ctx), accent, dispose() } */
export function createBackdrop(THREE, palette, { palette2 = null, breath = true } = {}) {
  let A = compile(palette), B = palette2 ? compile(palette2) : null, mix = 0;
  const u = {
    uBase: { value: new THREE.Vector3() }, uGeo: { value: [new THREE.Vector4(), new THREE.Vector4()] },
    uPos: { value: [new THREE.Vector4(), new THREE.Vector4()] }, uCol: { value: Array.from({ length: 8 }, () => new THREE.Vector3()) },
    uStr: { value: new THREE.Vector2(1, 0) }, uTime: { value: 0 }, uGrain: { value: DEFAULT_GRAIN }, uBreath: { value: breath ? BREATH_AMP : 0 },
  };
  const accent = new THREE.Vector3();
  function push() {
    const t = B ? mix : 0, s = (a, b) => lerp(a, b, t), ref = B || A;
    u.uBase.value.set(s(A.base[0], ref.base[0]), s(A.base[1], ref.base[1]), s(A.base[2], ref.base[2]));
    u.uGrain.value = s(A.grain, ref.grain);
    accent.set(s(A.accent[0], ref.accent[0]), s(A.accent[1], ref.accent[1]), s(A.accent[2], ref.accent[2]));
    for (let g = 0; g < MAX_GLOWS; g++) {
      const a = A.glows[g], b = ref.glows[g];
      u.uGeo.value[g].set(s(a.geo[0], b.geo[0]), s(a.geo[1], b.geo[1]), s(a.geo[2], b.geo[2]), s(a.geo[3], b.geo[3]));
      u.uPos.value[g].set(s(a.pos[0], b.pos[0]), s(a.pos[1], b.pos[1]), s(a.pos[2], b.pos[2]), s(a.pos[3], b.pos[3]));
      for (let k = 0; k < STOPS; k++) u.uCol.value[g * STOPS + k].set(s(a.col[k][0], b.col[k][0]), s(a.col[k][1], b.col[k][1]), s(a.col[k][2], b.col[k][2]));
      u.uStr.value.setComponent(g, s(a.str, b.str));
    }
  }
  push();
  const geo = new THREE.PlaneGeometry(2, 2);
  const material = new THREE.ShaderMaterial({ vertexShader: VERT, fragmentShader: FRAG, uniforms: u, depthTest: false, depthWrite: false, toneMapped: false });
  const mesh = new THREE.Mesh(geo, material);
  mesh.frustumCulled = false; mesh.renderOrder = -1000; mesh.name = 'gl-backdrop';
  return {
    mesh, accent, uniforms: u,
    setMix(t) { if (t !== mix) { mix = t; push(); } },
    setPalette(p, p2 = null) { A = compile(p); B = p2 ? compile(p2) : null; mix = 0; push(); },
    update(ctx) { u.uTime.value = ctx.time; },
    dispose() { geo.dispose(); material.dispose(); },
  };
}
