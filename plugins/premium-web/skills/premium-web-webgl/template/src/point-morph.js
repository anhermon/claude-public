// point-morph scene: one cloud of points that flows through N shapes as stage progress goes 0 -> 1.
// The look comes from the SHADER, not the point count: per-point pseudo-normal (direction from the centre) gives a key
// light, a rim light and a back-face dim; fog darkens far points; size follows depth. Flat additive points with
// none of that read as cheap (lesson from a built-and-reviewed demo, 2026-11).
// Numbers: point-morph N 20-60k, 1.1 s ease-in-out, shimmer +-2 px, pointer lerp .05, tilt <= .3 rad
// (measured from public reference sites, 2026-11; +-10 %).
import { resolve } from './shapes.js';
import { hex, clamp, lerp } from './util.js';

const STAGGER = 0.7;        // fraction of a transition spent staggering points by their seed (0 = all at once)
const RAMP_GAIN = 1.7;      // steepness of the per-point ramp
const REF_HEIGHT = 900;     // px; point size is authored for this canvas height
const SIZE_DEPTH_REF = 26;  // world units at which uSize is exact
const MAX_POINT_PX = 22;
const MIN_POINT_PX = 1;
const FOG_NEAR = 8, FOG_RANGE = 22, FOG_FLOOR = 0.15;

const VERT = /* glsl */`
attribute vec3 aT1; attribute vec3 aT2; attribute float aSeed;
uniform float uMorph, uTime, uPx, uSize, uShimmer, uNoise, uRim, uGain;
uniform vec3 uKey, uLit, uShade, uRimCol;
varying vec4 vCol;
float ramp(float k, float h){ return smoothstep(0., 1., clamp((uMorph - k) * ${RAMP_GAIN.toFixed(1)} - h * ${STAGGER.toFixed(1)}, 0., 1.)); }
vec3 swirl(vec3 p){ return vec3(sin(p.y * 1.7 + uTime * .30), sin(p.z * 1.9 - uTime * .25), sin(p.x * 1.5 + uTime * .20)); }
void main(){
  float r0 = ramp(0., aSeed), r1 = ramp(1., aSeed);
  vec3 p = mix(mix(position, aT1, r0), aT2, r1);
  float mid = r0 * (1. - r0) + r1 * (1. - r1);                  // 0 at rest, .25 mid-flight each
  p += swirl(p) * mid * 4. * uNoise;                            // midpoint turbulence so it reads as flow, not a lerp
  p += (swirl(p * 3. + aSeed * 40.) * uShimmer);                // idle shimmer
  vec3 n = normalize(p + 1e-4);
  vec3 wn = normalize(mat3(modelMatrix) * n);
  vec4 wp = modelMatrix * vec4(p, 1.);
  vec3 v = normalize(cameraPosition - wp.xyz);
  float diff = max(dot(wn, uKey), 0.);
  float rim = pow(1. - max(dot(wn, v), 0.), 3.) * uRim;
  float back = mix(.45, 1., step(0., dot(wn, v)));              // far side of the cloud sits dimmer: reads as volume
  vec3 col = mix(uShade, uLit, diff) * (.3 + .9 * diff) * back + uRimCol * rim;
  col *= uGain;                                                 // dense regions add up: keep the sum below white
  vec4 mv = viewMatrix * wp;
  float fog = clamp(1. - (-mv.z - ${FOG_NEAR.toFixed(1)}) / ${FOG_RANGE.toFixed(1)}, ${FOG_FLOOR}, 1.);
  gl_PointSize = clamp(uSize * uPx * (.7 + aSeed * .9) * (${SIZE_DEPTH_REF.toFixed(1)} / -mv.z), ${MIN_POINT_PX.toFixed(1)}, ${MAX_POINT_PX.toFixed(1)});
  vCol = vec4(col, fog);
  gl_Position = projectionMatrix * mv;
}`;
const FRAG = /* glsl */`
precision mediump float; varying vec4 vCol;
void main(){
  float r = length(gl_PointCoord - .5) * 2.;
  float a = pow(max(0., 1. - r), 1.7);
  gl_FragColor = vec4(vCol.rgb, a * vCol.a);
}`;

/** createPointMorph(config) -> scene for stage.addScene(). See webgl.config.js for the options. */
export function createPointMorph(cfg) {
  let THREE, group, points, geo, mat, total = 0;
  const tilt = { x: 0, y: 0 };
  const scene = {
    root: null,
    init(ctx) {
      THREE = ctx.THREE;
      total = ctx.mobile ? cfg.count.mobile : cfg.count.desktop;
      const arrays = cfg.shapes.map((s) => resolve(s, total));
      geo = new THREE.BufferGeometry();
      geo.setAttribute('position', new THREE.BufferAttribute(arrays[0], 3));
      geo.setAttribute('aT1', new THREE.BufferAttribute(arrays[1] || arrays[0], 3));
      geo.setAttribute('aT2', new THREE.BufferAttribute(arrays[2] || arrays[1] || arrays[0], 3));
      const seeds = new Float32Array(total);
      for (let i = 0; i < total; i++) seeds[i] = ((i * 2654435761) >>> 0) / 4294967296;   // stable hash, no RNG state
      geo.setAttribute('aSeed', new THREE.BufferAttribute(seeds, 1));
      geo.boundingSphere = new THREE.Sphere(new THREE.Vector3(), cfg.boundingRadius);
      const v3 = (c) => new THREE.Vector3(...hex(c));
      mat = new THREE.ShaderMaterial({
        vertexShader: VERT, fragmentShader: FRAG, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending,
        uniforms: {
          uMorph: { value: 0 }, uTime: { value: 0 }, uPx: { value: 1 }, uSize: { value: cfg.size }, uShimmer: { value: cfg.shimmer },
          uNoise: { value: cfg.noise }, uRim: { value: cfg.rim }, uGain: { value: cfg.gain }, uKey: { value: new THREE.Vector3(...cfg.key).normalize() },
          uLit: { value: v3(cfg.colors.lit) }, uShade: { value: v3(cfg.colors.shade) }, uRimCol: { value: v3(cfg.colors.rim) },
        },
      });
      points = new THREE.Points(geo, mat); points.frustumCulled = false;
      group = new THREE.Group(); group.add(points);
      scene.root = group;
    },
    resize(ctx) { if (!mat) return;   // the stage may call resize before init
      mat.uniforms.uPx.value = ctx.dpr * (ctx.size.h / REF_HEIGHT) * (ctx.size.w / ctx.size.h < 1 ? cfg.portraitSizeScale : 1); },
    setQuality(q) { if (geo) geo.setDrawRange(0, Math.max(1, Math.floor(total * q.count))); },
    update(ctx) {
      if (!mat) return;
      const u = mat.uniforms, last = cfg.shapes.length - 1;
      const morph = clamp(ctx.progress, 0, 1) * last;
      u.uMorph.value = morph; u.uTime.value = ctx.time;
      const i = Math.min(last - 1, Math.floor(morph)), f = morph - i;
      const portrait = ctx.size.w / ctx.size.h < 1;
      const x = lerp(cfg.offsetX[i] ?? 0, cfg.offsetX[i + 1] ?? 0, f * f * (3 - 2 * f));
      group.position.x = portrait ? 0 : x;
      group.position.y = portrait ? cfg.portraitLift : 0;
      group.scale.setScalar(portrait ? cfg.portraitScale : 1);
      const k = ctx.reduced ? 1 : cfg.pointerLerp;
      tilt.x += (ctx.pointer.y * cfg.tiltMax - tilt.x) * k;
      tilt.y += (ctx.pointer.x * cfg.tiltMax - tilt.y) * k;
      group.rotation.x = tilt.x;
      group.rotation.y = tilt.y + morph * cfg.spin + (ctx.reduced ? 0 : ctx.time * cfg.idleSpin);
    },
    dispose() { geo?.dispose(); mat?.dispose(); },
  };
  return scene;
}
