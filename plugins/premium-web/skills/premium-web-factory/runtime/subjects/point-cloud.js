// point-cloud: N points (a third on mobile) morphing between layouts on the GPU. The look is the shader (pseudo-normal key + rim
// light, back-face dim, depth fog, swirl in flight), not the count. M anchor points (every N/M-th) are the queryable items:
// they are larger, and light up as the cursor query ranks them. The wordmark is a dim ghost plane behind.
import { clamp, lerp, smoothstep, hash01 } from '../util.js';
import { makeWordmarkTexture, placeWordmark, wordBandY } from './wordmark.js';
import { MORPH } from './core.js';

const MOBILE_SHARE = 1 / 3, MAX_PX = 26, MIN_PX = 1, REF_H = 900, DEPTH_REF = 26, FOG_NEAR = 8, FOG_RANGE = 22, FOG_FLOOR = 0.15;
const LIGHT_ALPHA = 1.8, LIGHT_LUMA = 0.5, GHOST_OPACITY = 0.2, WORD_FADE = [0.2, 1.1], WORD_DROP = 1.2, STAGGER = 0.7, RAMP_GAIN = 1.7;
const VERT = /* glsl */`
attribute vec3 aB; attribute float aSeed; attribute float aLit; attribute float aItem;
uniform float uMix, uTime, uPx, uSize, uSwirl, uRim, uGain, uAsm, uAnchor, uLight; uniform vec3 uKey, uLit, uShade, uRimCol, uAcc;
varying vec4 vCol; varying float vL;
vec3 swirl(vec3 p){ return vec3(sin(p.y * 1.7 + uTime * .30), sin(p.z * 1.9 - uTime * .25), sin(p.x * 1.5 + uTime * .20)); }
void main(){
  float r = smoothstep(0., 1., clamp((uMix * ${RAMP_GAIN.toFixed(1)} - aSeed * ${STAGGER.toFixed(1)}) , 0., 1.));
  vec3 p = mix(position, aB, r);
  float mid = r * (1. - r);
  p += swirl(p) * mid * 4. * uSwirl;
  p += swirl(p * 3. + aSeed * 40.) * .02;
  vec3 n = normalize(p + 1e-4);
  vec4 wp = modelMatrix * vec4(p, 1.);
  vec3 wn = normalize(mat3(modelMatrix) * n), v = normalize(cameraPosition - wp.xyz);
  float diff = max(dot(wn, uKey), 0.), rim = pow(1. - max(dot(wn, v), 0.), 3.) * uRim, back = mix(.45, 1., step(0., dot(wn, v)));
  vec3 col = mix(uShade, uLit, diff) * (.3 + .9 * diff) * back + uRimCol * rim;
  col *= uGain; col = mix(col, uAcc * 2.2, aItem * (.35 + .65 * aLit));
  vec4 mv = viewMatrix * wp;
  float fog = clamp(1. - (-mv.z - ${FOG_NEAR.toFixed(1)}) / ${FOG_RANGE.toFixed(1)}, ${FOG_FLOOR}, 1.);
  float big = 1. + aItem * (uAnchor - 1.) * (.45 + aLit);
  gl_PointSize = clamp(uSize * uPx * (.7 + aSeed * .9) * big * (${DEPTH_REF.toFixed(1)} / -mv.z), ${MIN_PX.toFixed(1)}, ${MAX_PX.toFixed(1)});
  vCol = vec4(col, fog * uAsm); vL = aLit;
  gl_Position = projectionMatrix * mv;
}`;
// dark ground: additive glow. Light ground (uLight 1): normal blending with accent-ink dots, because additive light washes out to chalk.
const FRAG = /* glsl */`precision highp float; varying vec4 vCol; varying float vL; uniform vec3 uInk; uniform float uLight;
void main(){ vec2 c = gl_PointCoord - .5; float d = length(c) * 2.; if (d > 1.) discard; float g = pow(1. - d, 1.6);
  vec3 rgb = mix(vCol.rgb * g * 1.6, uInk * (.7 + .3 * vL), uLight); gl_FragColor = vec4(rgb, g * vCol.a * mix(1., ${LIGHT_ALPHA.toFixed(1)}, uLight)); }`;

export function create(core, piece) {
  const P = piece.subject.params, { M, N, forms, st, mobile } = core, wordY = wordBandY(piece, mobile), stride = N / M;
  const itemPos = new Float32Array(M * 3);
  let T, ctx, pts, mat, aB, aLit, geo, wordmark, wordTex, curSeg = -1, group;
  const scene = { root: null };
  const itemPoint = (j) => Math.min(N - 1, Math.floor(j * stride));

  scene.init = (c) => {
    ctx = c; T = c.THREE;
    scene.root = new T.Group(); group = new T.Group(); scene.root.add(group);
    ctx.camera.position.set(0, 0.8, 12.5);
    geo = new T.BufferGeometry();
    const a0 = new Float32Array(forms[0]), seeds = new Float32Array(N), item = new Float32Array(N);
    for (let i = 0; i < N; i++) seeds[i] = hash01(i + 3);
    for (let j = 0; j < M; j++) item[itemPoint(j)] = 1;
    aB = new T.BufferAttribute(new Float32Array(forms[1]), 3); aLit = new T.BufferAttribute(new Float32Array(N), 1);
    geo.setAttribute('position', new T.BufferAttribute(a0, 3)); geo.setAttribute('aB', aB); geo.setAttribute('aSeed', new T.BufferAttribute(seeds, 1));
    geo.setAttribute('aLit', aLit); geo.setAttribute('aItem', new T.BufferAttribute(item, 1));
    mat = new T.ShaderMaterial({ vertexShader: VERT, fragmentShader: FRAG, transparent: true, depthWrite: false, blending: T.AdditiveBlending, uniforms: {
      uMix: { value: 0 }, uTime: { value: 0 }, uPx: { value: 1 }, uSize: { value: P.size }, uSwirl: { value: P.swirl }, uRim: { value: P.rim }, uGain: { value: P.gain }, uAsm: { value: 0 }, uAnchor: { value: P.anchorSize }, uLight: { value: 0 }, uInk: { value: new T.Color(piece.palette.accent) },
      uKey: { value: new T.Vector3(0.5, 0.8, 0.6).normalize() }, uLit: { value: new T.Color(P.lit) }, uShade: { value: new T.Color(P.shade) }, uRimCol: { value: new T.Color(P.rimColor) }, uAcc: { value: new T.Color(piece.palette.accent) } } });
    pts = new T.Points(geo, mat); pts.frustumCulled = false; group.add(pts);
    if (piece.subject.wordmark) {
      wordTex = makeWordmarkTexture(T, piece.wordmark, piece.fonts.display.family, { top: '#ffffff', mid: '#c9c9c9', bottom: '#777777' });
      wordmark = new T.Mesh(new T.PlaneGeometry(1, 1), new T.MeshBasicMaterial({ map: wordTex, transparent: true, opacity: GHOST_OPACITY, depthWrite: false, toneMapped: false, fog: false, color: piece.palette.accent }));
      wordmark.renderOrder = -1; scene.root.add(wordmark);
    }
    core.onWorld = (w) => {
      const base = new T.Color(w.palette?.base || piece.palette.ground), light = 0.2126 * base.r + 0.7152 * base.g + 0.0722 * base.b > LIGHT_LUMA;
      mat.uniforms.uGain.value = P.gain * (0.6 + 0.4 * (w.halo ?? 1)); mat.uniforms.uAcc.value.set(w.palette?.accent || piece.palette.accent);
      mat.uniforms.uLight.value = light ? 1 : 0; mat.uniforms.uInk.value.set(w.palette?.accent || piece.palette.accent); mat.blending = light ? T.NormalBlending : T.AdditiveBlending;
    };
  };
  const setSeg = (i0) => {   // GPU holds form i0 (position) and i0+1 (aB); swap buffers only when the segment changes
    if (i0 === curSeg) return; curSeg = i0;
    geo.attributes.position.array.set(forms[i0]); geo.attributes.position.needsUpdate = true;
    aB.array.set(forms[i0 + 1]); aB.needsUpdate = true;
  };

  scene.update = (c) => {
    const view = core.view(c.camera), { a, i0, t, key } = core.frame(c, view), time = c.time;
    setSeg(i0);
    const u = mat.uniforms, asm = core.asm.t >= 99 ? 1 : clamp(core.asm.t / 1.6);
    u.uMix.value = t; u.uTime.value = time; u.uAsm.value = asm; u.uPx.value = ((c.dpr * c.size.h) / REF_H) * (mobile ? 0.9 : 1);
    const park = st.parkV, s = key.s * lerp(1, 0.55, park);
    group.position.set(key.x, key.y - park * view.halfH * 0.5, 0); group.scale.set(s, s * st.stretchV, s);
    group.rotation.set(key.pitch - st.tilt[1] * 0.6, key.yaw + (c.reduced ? 0 : time * 0.1) + st.tilt[0], 0, 'YXZ');
    c.camera.lookAt(0, 0, 0); group.updateMatrixWorld(true);
    // anchor positions on the CPU (same stagger/ramp as the shader, minus the swirl) -> a real brute-force screen-space query
    const fa = forms[i0], fb = forms[i0 + 1], v = new T.Vector3();
    for (let j = 0; j < M; j++) {
      const p = itemPoint(j), r = smoothstep(0, 1, clamp(t * RAMP_GAIN - hash01(p + 3) * STAGGER));
      v.set(lerp(fa[p * 3], fb[p * 3], r), lerp(fa[p * 3 + 1], fb[p * 3 + 1], r), lerp(fa[p * 3 + 2], fb[p * 3 + 2], r)).applyMatrix4(group.matrixWorld).project(c.camera);
      itemPos[j * 3] = v.x; itemPos[j * 3 + 1] = v.y;
    }
    const nearest = st.custom?.fn ? null : core.query((j) => Math.hypot((itemPos[j * 3] - c.pointer.x) * c.camera.aspect, itemPos[j * 3 + 1] - c.pointer.y));
    core.litStep(c, nearest);
    const la = aLit.array; la.fill(0);
    for (let j = 0; j < M; j++) la[itemPoint(j)] = core.lit[j] * (st.mask[j] ? 1 : 0.2);
    aLit.needsUpdate = true;
    if (wordmark) { const wv = 1 - smoothstep(WORD_FADE[0], WORD_FADE[1], a); wordmark.visible = wv > 0.05; placeWordmark(wordmark, c.camera, wordY, (1 - wv) * WORD_DROP); }
    void MORPH;
  };
  scene.setQuality = (q) => { if (geo) geo.setDrawRange(0, Math.floor(N * q.count)); };
  scene.dispose = () => { geo?.dispose(); mat?.dispose(); wordTex?.dispose(); };
  return scene;
}
export const pointCount = (piece, mobile) => Math.floor(piece.subject.count * (mobile ? MOBILE_SHARE : 1));
