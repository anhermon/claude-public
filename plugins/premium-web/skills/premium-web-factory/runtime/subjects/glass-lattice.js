// glass-lattice: M glass-and-chrome nodes joined by rods. Recipe (r170, no HDR file): transmission .96, high ior, thick, clearcoat,
// a PMREM gradient dome + 3 emissive strips as environment, an OPAQUE wordmark behind (transmission only refracts opaque draws).
// Rods are the k-nearest links of each form, so every chapter has its own connectivity. Lit cores answer the cursor.
import { clamp, lerp, smoothstep, hash01, mulberry32 } from '../util.js';
import { makeWordmarkTexture, placeWordmark, wordBandY } from './wordmark.js';
import { MORPH, POINTER } from './core.js';

const FOG_NEAR = 15, FOG_FAR = 52, KEY_POS = [5, 7, 6], RIM_POS = [-6, 2, -5], KEY_I = 2.6, RIM_I = 2.4;
const JITTER = { min: 0.78, span: 0.5 };
const CORE = { radius: 0.085, dim: 0.34, lit: 2.4, colorDim: 0.35, colorLit: 1.8 };
const HALO = { size: 120, alpha: 0.9, scale: 9 };
const DUST = { rMin: 4.5, rMax: 16, size: 2.2, alpha: 0.55, speed: 0.05, scale: 14 };
const ROD_SIDES = 7, ROD_MIN_W = 0.02, ROD_ASSEMBLE = { delay: 0.5, span: 1.2 }, WORD_FADE = [0.2, 1.1], WORD_DROP = 1.2;
const SPHERE_SEG = [28, 18], CORE_SEG = [14, 10];

const HALO_VERT = /* glsl */`attribute float aLit; uniform float uSize, uPx; varying float vLit;
void main(){ vLit = aLit; vec4 mv = modelViewMatrix * vec4(position, 1.); gl_Position = projectionMatrix * mv; gl_PointSize = uSize * uPx * aLit * (1. / -mv.z); }`;
const HALO_FRAG = /* glsl */`precision highp float; uniform vec3 uColor; uniform float uAlpha; varying float vLit;
void main(){ float d = length(gl_PointCoord - .5) * 2.; float g = pow(max(1. - d, 0.), 2.2); gl_FragColor = vec4(uColor * g * 1.4, g * uAlpha * vLit); }`;
const DUST_VERT = /* glsl */`attribute float aSeed; uniform float uTime, uSize, uPx, uPointer; varying float vA;
void main(){ vec3 p = position; float t = uTime * ${DUST.speed} + aSeed * 6.283;
  p += vec3(sin(t * 1.3 + p.y), cos(t + p.z * .7), sin(t * .9 + p.x)) * .5; p.xy += vec2(uPointer) * (1. + aSeed);
  vec4 mv = modelViewMatrix * vec4(p, 1.); gl_Position = projectionMatrix * mv;
  gl_PointSize = uSize * uPx * (.5 + aSeed) * (${DUST.scale.toFixed(1)} / -mv.z); vA = (.25 + .75 * aSeed) * smoothstep(60., 14., -mv.z); }`;
const DUST_FRAG = /* glsl */`precision highp float; uniform vec3 uColor; uniform float uAlpha; varying float vA;
void main(){ float d = length(gl_PointCoord - .5) * 2.; float g = smoothstep(1., .2, d); gl_FragColor = vec4(uColor, g * vA * uAlpha); }`;

export function create(core, piece) {
  const P = piece.subject.params, { M, forms, st, mobile } = core, wordY = wordBandY(piece, mobile);
  const pos = new Float32Array(M * 3), litA = new Float32Array(M);
  let T, ctx, group, nodes, cores, rods, halo, dust, wordmark, wordTex, envTex, keyL, rimL, edges = [], W = null;
  const m4 = {};
  const scene = { root: null };

  function buildEdges() {   // union of each form's k-nearest links; W[e*nF+f] = 1 where the link exists in form f
    const nF = forms.length, map = new Map(), per = [];
    forms.forEach((f, fi) => {
      for (let i = 0; i < M; i++) {
        const d = [];
        for (let j = 0; j < M; j++) if (j !== i) d.push([(f[i * 3] - f[j * 3]) ** 2 + (f[i * 3 + 1] - f[j * 3 + 1]) ** 2 + (f[i * 3 + 2] - f[j * 3 + 2]) ** 2, j]);
        d.sort((a, b) => a[0] - b[0]);
        for (let r = 0; r < P.rodsPerNode; r++) { const j = d[r][1], key = i < j ? i * M + j : j * M + i; if (!map.has(key)) { map.set(key, edges.length); edges.push(i < j ? [i, j] : [j, i]); } per.push([map.get(key), fi]); }
      }
    });
    W = new Float32Array(edges.length * nF);
    for (const [e, fi] of per) W[e * nF + fi] = 1;
  }
  function makeEnv() {
    const s = new T.Scene(), acc = new T.Color(piece.palette.accent);
    const lo = acc.clone().multiplyScalar(0.18), bot = acc.clone().lerp(new T.Color('#ffffff'), 0.45);
    const dome = new T.Mesh(new T.SphereGeometry(30, 32, 16), new T.ShaderMaterial({ side: T.BackSide, depthWrite: false,
      uniforms: { uMid: { value: lo }, uBot: { value: bot } }, vertexShader: 'varying vec3 vP; void main(){ vP = normalize(position); gl_Position = projectionMatrix * modelViewMatrix * vec4(position,1.); }',
      fragmentShader: 'uniform vec3 uMid, uBot; varying vec3 vP; void main(){ float h = vP.y * .5 + .5; vec3 top = vec3(.02,.04,.07); vec3 c = mix(uBot * .6, uMid, smoothstep(0., .45, h)); c = mix(c, top, smoothstep(.45, 1., h)); gl_FragColor = vec4(c, 1.); }' }));
    s.add(dome);
    const strip = (w, h, x, y, z, col, k) => { const m = new T.Mesh(new T.PlaneGeometry(w, h), new T.MeshBasicMaterial({ color: new T.Color(col).multiplyScalar(k), side: T.DoubleSide })); m.position.set(x, y, z); m.lookAt(0, 0, 0); s.add(m); };
    strip(18, 2.2, 8, 12, 6, '#ffffff', 9); strip(2, 16, -14, 2, -4, bot, 7); strip(14, 2, 0, -3, 14, bot, 4);
    const pm = new T.PMREMGenerator(ctx.renderer), rt = pm.fromScene(s, 0.03); pm.dispose(); dome.geometry.dispose();
    return rt.texture;
  }

  scene.init = (c) => {
    ctx = c; T = c.THREE;
    scene.root = new T.Group(); group = new T.Group(); scene.root.add(group);
    ctx.camera.position.set(0, 0.8, 12.5);
    ctx.scene.fog = new T.Fog(piece.worlds[0].base, FOG_NEAR, FOG_FAR);
    envTex = makeEnv(); ctx.scene.environment = envTex;
    if (mobile) ctx.renderer.transmissionResolutionScale = 0.5;
    keyL = new T.DirectionalLight('#f2fbff', KEY_I); keyL.position.set(...KEY_POS); scene.root.add(keyL);
    rimL = new T.DirectionalLight(piece.palette.accent, RIM_I); rimL.position.set(...RIM_POS); scene.root.add(rimL);
    nodes = new T.InstancedMesh(new T.SphereGeometry(P.radius, ...SPHERE_SEG), new T.MeshPhysicalMaterial({ color: '#ffffff', transmission: 0.96, thickness: P.thickness, roughness: 0.06, ior: P.ior, attenuationColor: piece.palette.accent, attenuationDistance: 3.2, envMapIntensity: 1.25, clearcoat: 1, clearcoatRoughness: 0.08 }), M);
    nodes.instanceMatrix.setUsage(T.DynamicDrawUsage); nodes.frustumCulled = false; group.add(nodes);
    for (let i = 0; i < M; i++) nodes.setColorAt(i, new T.Color(P.tints[Math.floor(hash01(i + 17) * P.tints.length)]));
    cores = new T.InstancedMesh(new T.SphereGeometry(CORE.radius, ...CORE_SEG), new T.MeshBasicMaterial({ color: piece.palette.accent, toneMapped: false }), M);
    cores.instanceMatrix.setUsage(T.DynamicDrawUsage); cores.frustumCulled = false; group.add(cores);
    buildEdges();
    rods = new T.InstancedMesh(new T.CylinderGeometry(1, 1, 1, ROD_SIDES, 1, true), new T.MeshStandardMaterial({ color: '#d9e6ee', metalness: 1, roughness: 0.28, envMapIntensity: 1.3 }), edges.length);
    rods.instanceMatrix.setUsage(T.DynamicDrawUsage); rods.frustumCulled = false; group.add(rods);
    const hg = new T.BufferGeometry(); hg.setAttribute('position', new T.BufferAttribute(pos, 3)); hg.setAttribute('aLit', new T.BufferAttribute(litA, 1));
    halo = new T.Points(hg, new T.ShaderMaterial({ vertexShader: HALO_VERT, fragmentShader: HALO_FRAG, transparent: true, depthWrite: false, depthTest: false, blending: T.AdditiveBlending, uniforms: { uSize: { value: HALO.size }, uPx: { value: 1 }, uColor: { value: new T.Color(piece.palette.accent) }, uAlpha: { value: HALO.alpha } } }));
    halo.frustumCulled = false; halo.renderOrder = 10; group.add(halo);
    const nD = mobile ? Math.floor(P.dust * 0.43) : P.dust, dp = new Float32Array(nD * 3), ds = new Float32Array(nD), r = mulberry32(piece.subject.seed + 5);
    for (let i = 0; i < nD; i++) { const u = r() * 2 - 1, a = r() * 6.2832, s = Math.sqrt(1 - u * u), rr = DUST.rMin + (DUST.rMax - DUST.rMin) * Math.pow(r(), 0.7); dp.set([s * Math.cos(a) * rr * 1.5, u * rr * 0.8, s * Math.sin(a) * rr - 3], i * 3); ds[i] = r(); }
    const dg = new T.BufferGeometry(); dg.setAttribute('position', new T.BufferAttribute(dp, 3)); dg.setAttribute('aSeed', new T.BufferAttribute(ds, 1));
    dust = new T.Points(dg, new T.ShaderMaterial({ vertexShader: DUST_VERT, fragmentShader: DUST_FRAG, transparent: true, depthWrite: false, blending: T.AdditiveBlending, uniforms: { uTime: { value: 0 }, uSize: { value: DUST.size }, uPx: { value: 1 }, uPointer: { value: 0 }, uColor: { value: new T.Color(piece.palette.accent).lerp(new T.Color('#ffffff'), 0.4) }, uAlpha: { value: DUST.alpha } } }));
    dust.frustumCulled = false; scene.root.add(dust);
    if (piece.subject.wordmark) {
      const acc = new T.Color(piece.palette.accent);
      wordTex = makeWordmarkTexture(T, piece.wordmark, piece.fonts.display.family, { top: '#f2f8fa', mid: '#' + acc.clone().lerp(new T.Color('#ffffff'), 0.35).getHexString(), bottom: '#' + acc.clone().multiplyScalar(0.28).getHexString() });
      wordmark = new T.Mesh(new T.PlaneGeometry(1, 1), new T.MeshBasicMaterial({ map: wordTex, alphaTest: 0.5, transparent: false, alphaToCoverage: true, toneMapped: false, fog: false }));
      scene.root.add(wordmark);
    }
    Object.assign(m4, { m: new T.Matrix4(), q: new T.Quaternion(), s: new T.Vector3(), p: new T.Vector3(), up: new T.Vector3(0, 1, 0), d: new T.Vector3(), col: new T.Color(), ndc: new T.Vector3() });
    core.onWorld = (w) => {
      if (w.fog) ctx.scene.fog.color.set(w.fog);
      keyL.intensity = KEY_I * (w.key ?? 1); rimL.intensity = RIM_I * (w.key ?? 1);
      dust.material.uniforms.uAlpha.value = DUST.alpha * (w.dust ?? 1); halo.material.uniforms.uAlpha.value = HALO.alpha * (w.halo ?? 1);
    };
    core.onWorld(st.world);
  };

  scene.update = (c) => {
    const view = core.view(c.camera), fr = core.frame(c, view), { a, i0, t, key } = fr, time = c.time;
    const fa = forms[i0], fb = forms[i0 + 1];
    for (let i = 0; i < M; i++) {
      const d = hash01(i) * MORPH.stagger, tl = smoothstep(0, 1, clamp((t - d) / (1 - MORPH.stagger))), arc = Math.sin(Math.PI * tl) * MORPH.arcAmp * (hash01(i + 9) - 0.5), ax = core.asmEase(i);
      for (let k = 0; k < 3; k++) {
        const f = lerp(fa[i * 3 + k], fb[i * 3 + k], tl) + (k === 1 ? 0 : arc * (k === 0 ? 1 : -1));
        pos[i * 3 + k] = lerp(core.scatter[i * 3 + k], f * (k === 1 ? st.stretchV : 1), ax);
      }
    }
    const sp = c.reduced ? 0 : time * 0.12, park = st.parkV, s = key.s * lerp(1, 0.55, park);
    group.position.set(key.x, key.y - park * view.halfH * 0.5, 0);
    group.scale.setScalar(s);
    group.rotation.set(key.pitch - st.tilt[1] * 0.6, key.yaw + sp + st.tilt[0], 0, 'YXZ');
    c.camera.lookAt(0, 0, 0); group.updateMatrixWorld(true);
    const nearest = st.custom?.fn ? null : core.query((i) => {
      m4.ndc.set(pos[i * 3], pos[i * 3 + 1], pos[i * 3 + 2]).applyMatrix4(group.matrixWorld).project(c.camera);
      return Math.hypot((m4.ndc.x - c.pointer.x) * c.camera.aspect, m4.ndc.y - c.pointer.y);
    });
    core.litStep(c, nearest);
    for (let i = 0; i < M; i++) {
      const L = core.lit[i], on = st.mask[i];
      litA[i] = L;
      m4.p.set(pos[i * 3], pos[i * 3 + 1], pos[i * 3 + 2]); m4.s.setScalar(JITTER.min + JITTER.span * hash01(i + 5)); m4.m.compose(m4.p, m4.q.identity(), m4.s); nodes.setMatrixAt(i, m4.m);
      m4.s.setScalar(lerp(CORE.dim, CORE.lit, L) * (on ? 1 : 0.5)); m4.m.compose(m4.p, m4.q.identity(), m4.s); cores.setMatrixAt(i, m4.m);
      m4.col.set(piece.palette.accent).multiplyScalar(lerp(CORE.colorDim, CORE.colorLit, L) * (on ? 1 : 0.3)); cores.setColorAt(i, m4.col);
    }
    nodes.instanceMatrix.needsUpdate = true; cores.instanceMatrix.needsUpdate = true; if (cores.instanceColor) cores.instanceColor.needsUpdate = true;
    halo.geometry.attributes.position.needsUpdate = true; halo.geometry.attributes.aLit.needsUpdate = true;
    const nF = forms.length, ramp = smoothstep(0, 1, clamp(core.asm.t < 99 ? (core.asm.t - ROD_ASSEMBLE.delay) / ROD_ASSEMBLE.span : 1)), eT = smoothstep(0, 1, t);
    for (let e = 0; e < edges.length; e++) {
      const w = lerp(W[e * nF + i0], W[e * nF + i0 + 1], eT) * ramp, [p, q] = edges[e];
      if (w < ROD_MIN_W) { m4.s.set(0, 0, 0); m4.p.set(0, 0, 0); m4.m.compose(m4.p, m4.q.identity(), m4.s); rods.setMatrixAt(e, m4.m); continue; }
      const x1 = pos[p * 3], y1 = pos[p * 3 + 1], z1 = pos[p * 3 + 2], dx = pos[q * 3] - x1, dy = pos[q * 3 + 1] - y1, dz = pos[q * 3 + 2] - z1, len = Math.hypot(dx, dy, dz) || 1e-4;
      m4.d.set(dx / len, dy / len, dz / len); m4.q.setFromUnitVectors(m4.up, m4.d);
      m4.p.set(x1 + dx / 2, y1 + dy / 2, z1 + dz / 2); m4.s.set(P.rodRadius * w, len, P.rodRadius * w);
      m4.m.compose(m4.p, m4.q, m4.s); rods.setMatrixAt(e, m4.m);
    }
    rods.instanceMatrix.needsUpdate = true;
    dust.material.uniforms.uTime.value = time; dust.material.uniforms.uPointer.value = c.pointer.x * 0.4;
    const px = (c.dpr * c.size.h) / 900; halo.material.uniforms.uPx.value = px * HALO.scale; dust.material.uniforms.uPx.value = px;
    if (wordmark) {
      const wv = 1 - smoothstep(WORD_FADE[0], WORD_FADE[1], a);
      wordmark.visible = wv > 0.05; placeWordmark(wordmark, c.camera, wordY, (1 - wv) * WORD_DROP);
    }
  };
  scene.setQuality = (q) => { if (dust) dust.geometry.setDrawRange(0, Math.floor(dust.geometry.attributes.position.count * q.count)); };
  scene.dispose = () => { envTex?.dispose(); wordTex?.dispose(); };
  void POINTER;
  return scene;
}
