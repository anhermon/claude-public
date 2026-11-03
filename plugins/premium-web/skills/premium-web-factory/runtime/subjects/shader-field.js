// shader-field: caustic ink flow. No object: a domain-warped fbm ink body with thin caustic veins, swirled around M "wells" (the
// queryable items) and around the cursor. Chapter targets move the wells (the field re-forms around them) and keyframe the flow
// parameters. The wordmark is sampled THROUGH the flow, so the field refracts the type. Draws over the stage backdrop.
import { clamp, lerp, smoothstep, hash01 } from '../util.js';
import { makeWordmarkTexture, WORDMARK, wordBandY } from './wordmark.js';
import { MORPH } from './core.js';

const MAX_WELLS = 64, WORD_FADE = [0.2, 1.1], SWIRL_K = 1.6, WELL_FALLOFF = 4, POINT_FALLOFF = 60, POINTER_E = 0.9;
const VARY = { scale: 0.15, scaleF: 1.9, warp: 0.25, warpF: 1.3 };   // deterministic per-act variation so chapters differ without per-act params
const TIME_OFFSET = 6, LIGHT_LUMA = 0.5;
const VERT = /* glsl */`varying vec2 vUv; void main(){ vUv = position.xy * .5 + .5; gl_Position = vec4(position.xy, 0., 1.); }`;
const FRAG = /* glsl */`precision highp float;
varying vec2 vUv;
uniform float uTime, uAspect, uScale, uWarp, uContrast, uVeins, uRefract, uWordOn, uAsm;
uniform vec2 uFocus, uPointer; uniform float uPointerE;
uniform vec3 uC0, uC1, uC2; uniform vec4 uWord; uniform sampler2D uWordTex;
uniform vec3 uWell[${MAX_WELLS}]; uniform int uNW;
float hs(vec2 p){ return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
float vn(vec2 p){ vec2 i = floor(p), f = fract(p); f = f * f * (3. - 2. * f);
  return mix(mix(hs(i), hs(i + vec2(1, 0)), f.x), mix(hs(i + vec2(0, 1)), hs(i + vec2(1, 1)), f.x), f.y); }
float fbm(vec2 p){ float a = .5, s = 0.; for (int i = 0; i < 4; i++) { s += a * vn(p); p = p * 2.03 + vec2(1.7, 9.2); a *= .5; } return s; }
void main(){
  vec2 p0 = (vUv * 2. - 1.) * vec2(uAspect, 1.);
  vec2 p = p0 * uScale;
  float glow = 0.;
  for (int i = 0; i < ${MAX_WELLS}; i++) {
    if (i >= uNW) break;
    vec2 d = p0 - uWell[i].xy; float d2 = dot(d, d), e = uWell[i].z;
    float ang = e * exp(-d2 * ${WELL_FALLOFF.toFixed(1)}) * ${SWIRL_K.toFixed(1)}; float c = cos(ang), s = sin(ang);
    p += (mat2(c, -s, s, c) * d - d) * uScale; glow += e * exp(-d2 * ${POINT_FALLOFF.toFixed(1)});
  }
  { vec2 d = p0 - uPointer; float d2 = dot(d, d); float ang = uPointerE * exp(-d2 * 3.) * ${SWIRL_K.toFixed(1)}; float c = cos(ang), s = sin(ang); p += (mat2(c, -s, s, c) * d - d) * uScale; glow += uPointerE * .6 * exp(-d2 * 40.); }
  glow = 1. - exp(-glow * 1.2);   // soft-saturate overlapping wells so they never blow out to a white blob
  float t = uTime;
  vec2 q = vec2(fbm(p + vec2(0., t * .15)), fbm(p + vec2(5.2, 1.3) - t * .12));
  vec2 r = vec2(fbm(p + uWarp * q + vec2(1.7, 9.2) + t * .1), fbm(p + uWarp * q + vec2(8.3, 2.8) - t * .08));
  vec2 f = uWarp * r + q * .5;
  float n = fbm(p + f);
  float ridge = 1. - abs(2. * vn(p * 1.6 + f * 1.3 + t * .05) - 1.);
  float rad = mix(.7, 1.35, smoothstep(.5, 1., uAspect));   // portrait: the lit zone is only the subject's own area
  float calm = mix(.12, 1., smoothstep(rad, rad * .22, length(p0 - uFocus * vec2(uAspect, 1.))));
  float vein = pow(ridge, 9.) * uVeins * calm;
  float body = smoothstep(.28, .86, n) * calm * uContrast;
  vec3 col = mix(uC2, uC1, smoothstep(.2, .7, n)); col = mix(col, uC0, smoothstep(.55, 1., n + vein * .7));
  col += uC0 * (vein * 1.1 + glow * .55);
  float a = clamp(body * .85 + vein * .8 + glow * .45, 0., 1.);
  col = min(col, vec3(.92));
  if (uWordOn > .001) {
    vec2 wuv = (p0 - uWord.xy) / uWord.zw + .5; wuv += (f - .6) * uRefract;
    float inside = step(0., wuv.x) * step(wuv.x, 1.) * step(0., wuv.y) * step(wuv.y, 1.);
    float m = texture2D(uWordTex, wuv).a * inside;
    col = mix(col, uC0 * (.55 + n * .6 + vein * 2.2), m * uWordOn * .9); a = max(a, m * uWordOn * .9);
  }
  gl_FragColor = vec4(col, a * uAsm);
}`;

export function create(core, piece) {
  const P = piece.subject.params, { M, forms, st, mobile } = core, wordY = wordBandY(piece, mobile);
  const wells = new Float32Array(MAX_WELLS * 3), ndc = new Float32Array(M * 2);
  let T, ctx, mat, mesh, wordTex;
  const scene = { root: null };
  const paramsAt = (k, a) => {   // flow parameters of act k: explicit target.params, else the subject params with a deterministic variation
    const o = core.keys[k].params;
    return { scale: o.scale ?? P.scale * (1 + VARY.scale * Math.sin(a * VARY.scaleF)), warp: o.warp ?? P.warp * (1 + VARY.warp * Math.cos(a * VARY.warpF)), veins: o.veins ?? P.veins, contrast: o.contrast ?? P.contrast };
  };

  scene.init = (c) => {
    ctx = c; T = c.THREE;
    scene.root = new T.Group();
    ctx.camera.position.set(0, 0.8, 12.5);
    wordTex = piece.subject.wordmark ? makeWordmarkTexture(T, piece.wordmark, piece.fonts.display.family, { top: '#ffffff', mid: '#ffffff', bottom: '#ffffff' }) : null;
    if (!wordTex) { const cv = document.createElement('canvas'); cv.width = cv.height = 2; wordTex = new T.CanvasTexture(cv); }
    mat = new T.ShaderMaterial({ vertexShader: VERT, fragmentShader: FRAG, transparent: true, depthTest: false, depthWrite: false, uniforms: {
      uTime: { value: 0 }, uAspect: { value: 1 }, uScale: { value: P.scale }, uWarp: { value: P.warp }, uContrast: { value: P.contrast }, uVeins: { value: P.veins }, uRefract: { value: P.refract },
      uWordOn: { value: 0 }, uAsm: { value: 0 }, uFocus: { value: new T.Vector2() }, uPointer: { value: new T.Vector2(9, 9) }, uPointerE: { value: 0 },
      uC0: { value: new T.Color() }, uC1: { value: new T.Color() }, uC2: { value: new T.Color() }, uWord: { value: new T.Vector4(0, -0.6, 2, 0.5) }, uWordTex: { value: wordTex },
      uWell: { value: Array.from({ length: MAX_WELLS }, () => new T.Vector3()) }, uNW: { value: M } } });
    mesh = new T.Mesh(new T.PlaneGeometry(2, 2), mat); mesh.frustumCulled = false; mesh.renderOrder = -999; scene.root.add(mesh);
    core.onWorld = (w) => {
      const p = w.palette; if (!p) return;
      const g = p.glows[0].stops, acc = new T.Color(p.accent), base = new T.Color(p.base);
      const light = 0.2126 * base.r + 0.7152 * base.g + 0.0722 * base.b > LIGHT_LUMA;
      if (light) { mat.uniforms.uC0.value.copy(acc); mat.uniforms.uC1.value.copy(acc).lerp(base, 0.5); mat.uniforms.uC2.value.copy(acc).lerp(base, 0.8); }
      else { mat.uniforms.uC0.value.set(g[0][1]); mat.uniforms.uC1.value.set(g[1][1]).lerp(acc, 0.35); mat.uniforms.uC2.value.set(g[2][1]).lerp(acc, 0.15); }
    };
    core.onWorld(st.world);
  };

  scene.update = (c) => {
    const view = core.view(c.camera), { a, i0, t, key } = core.frame(c, view), time = c.time, aspect = c.camera.aspect;
    const fa = forms[i0], fb = forms[i0 + 1], cy = Math.cos(key.yaw), sy = Math.sin(key.yaw), cp = Math.cos(key.pitch), sp = Math.sin(key.pitch), park = st.parkV, s = key.s * lerp(1, 0.55, park);
    for (let i = 0; i < M; i++) {
      const d = hash01(i) * MORPH.stagger, tl = smoothstep(0, 1, clamp((t - d) / (1 - MORPH.stagger))), ax = core.asmEase(i);
      const f = [0, 1, 2].map((k) => lerp(core.scatter[i * 3 + k] * 0.4, lerp(fa[i * 3 + k], fb[i * 3 + k], tl), ax));
      const x1 = f[0] * cy + f[2] * sy, z1 = -f[0] * sy + f[2] * cy, y1 = (f[1] * cp - z1 * sp) * st.stretchV;
      ndc[i * 2] = (key.x + x1 * s) / view.halfW; ndc[i * 2 + 1] = (key.y - park * view.halfH * 0.5 + y1 * s) / view.halfH;
    }
    const nearest = st.custom?.fn ? null : core.query((i) => Math.hypot((ndc[i * 2] - c.pointer.x) * aspect, ndc[i * 2 + 1] - c.pointer.y));
    core.litStep(c, nearest);
    const u = mat.uniforms, pa = paramsAt(i0, i0), pb = paramsAt(Math.min(i0 + 1, core.keys.length - 1), i0 + 1);
    u.uTime.value = time * P.speed + TIME_OFFSET; u.uAspect.value = aspect; u.uScale.value = lerp(pa.scale, pb.scale, t); u.uWarp.value = lerp(pa.warp, pb.warp, t);
    u.uVeins.value = lerp(pa.veins, pb.veins, t); u.uContrast.value = lerp(pa.contrast, pb.contrast, t); u.uAsm.value = core.asm.t >= 99 ? 1 : clamp(core.asm.t / 1.6);
    for (let i = 0; i < M; i++) { const e = (P.wells * (0.35 + 0.9 * core.lit[i])) * (st.mask[i] ? 1 : 0.25); u.uWell.value[i].set(ndc[i * 2] * aspect, ndc[i * 2 + 1], e); }
    u.uFocus.value.set(key.x / view.halfW, key.y / view.halfH);
    u.uPointer.value.set(c.pointer.x * aspect, c.pointer.y); u.uPointerE.value = c.pointer.moved ? POINTER_E : 0;
    const wv = 1 - smoothstep(WORD_FADE[0], WORD_FADE[1], a), ww = Math.min(aspect * 2 * 0.94, 2 * (WORDMARK.width / WORDMARK.height) * 1.2);
    u.uWordOn.value = piece.subject.wordmark ? wv : 0;
    u.uWord.value.set(0, wordY, ww, (ww * WORDMARK.height) / WORDMARK.width);
  };
  scene.dispose = () => { mat?.dispose(); wordTex?.dispose(); };
  return scene;
}
