// shader fields: full-screen fragment shaders on a raw-WebGL2 canvas (fx-canvas). Pick one with config `field.kind`.
//   colorField : low-frequency fbm domain-warped, mixed through a 4-5 stop palette in OKLab, then grain + dither.
//   ribbon     : domain-warped sine iso-lines with 0.01/abs(f) glow (the "glow ribbon" look).
// Numbers: colour field ~160 px wide internal render blurred 2.5 rem upscaled (renderScale .15-.5), 4-5 stops, 30 fps,
// visible-only; ribbon glow .01/abs(f); grain ~6 % (all measured from public reference sites, 2026-11; +-15 %).
import { createFx } from './fx-canvas.js';
import { GLSL_HASH, GLSL_NOISE, GLSL_OKLAB, GLSL_FINISH } from './fx-glsl.js';
import { compilePalettes, paletteAt } from './fx-color.js';

const OKLAB_STRIDE = 3;
const MAX_STOPS = 5;

const COLOR_FIELD = /* glsl */`
uniform float uTime, uGrain, uScale, uWarp, uProgress; uniform vec2 uRes, uPointer; uniform vec3 uPal[${MAX_STOPS}];
vec3 ramp(float t){
  float x = clamp(t, 0., 1.) * float(${MAX_STOPS - 1}); int i = int(min(floor(x), float(${MAX_STOPS - 2}))); float f = smoothstep(0., 1., x - float(i));
  vec3 a = uPal[0], b = uPal[1];
  if (i == 1) { a = uPal[1]; b = uPal[2]; } else if (i == 2) { a = uPal[2]; b = uPal[3]; } else if (i == 3) { a = uPal[3]; b = uPal[4]; }
  return mix(a, b, f);
}
void main(){
  vec2 p = (gl_FragCoord.xy - .5 * uRes) / uRes.y * uScale;
  p += uPointer * .25;
  vec2 q = vec2(fbm3(p + uTime * .05), fbm3(p + 5.2 - uTime * .04));
  float f = fbm3(p + uWarp * q + vec2(0., uProgress));
  vec3 col = lin2srgb(oklab2lin(ramp(f * 1.35 - .1)));
  fragColor = vec4(finish(col, gl_FragCoord.xy, uTime, uGrain), 1.);
}`;

const RIBBON = /* glsl */`
uniform float uTime, uGrain, uScale, uWarp, uGlow; uniform vec2 uRes, uPointer; uniform vec3 uPal[${MAX_STOPS}];
void main(){
  vec2 p = (gl_FragCoord.xy - .5 * uRes) / uRes.y * uScale;
  float t = uTime * .35;
  vec3 col = vec3(0.);
  for (int i = 0; i < 6; i++) {
    float fi = float(i);
    vec2 q = p + uPointer * .12 * (1. + fi * .2);
    float y = q.y - (fi - 2.5) * .11 - uWarp * (.22 * sin(q.x * (1.4 + .15 * fi) + t + fi * 1.3) + .1 * sin(q.x * 3.1 - t * .8 + fi * 2.));
    float g = uGlow / (abs(y) + .004);
    col += oklab2lin(mix(uPal[1], uPal[3], fi / 5.)) * g;
  }
  col = 1. - exp(-col);
  fragColor = vec4(finish(lin2srgb(col), gl_FragCoord.xy, uTime, uGrain), 1.);
}`;
const KINDS = { colorField: COLOR_FIELD, ribbon: RIBBON };

/** createField(target, cfg) -> fx (fx-canvas handle). cfg: see webgl.config.js `field`. */
export function createField(target, cfg) {
  const pals = compilePalettes([cfg.palette]);
  const flat = new Float32Array(MAX_STOPS * OKLAB_STRIDE);
  paletteAt(pals, 0, flat);
  const pointer = [0, 0];
  const fx = createFx(target, {
    label: cfg.kind, frag: KINDS[cfg.kind], chunks: [GLSL_HASH, GLSL_NOISE, GLSL_OKLAB, GLSL_FINISH],
    renderScale: cfg.renderScale, timeScale: cfg.timeScale, staticTime: cfg.staticTime, poster: cfg.poster, reduced: cfg.reduced,
    uniforms: { uPal: flat, uGrain: cfg.grain, uScale: cfg.scale, uWarp: cfg.warp, uGlow: cfg.glow, uProgress: 0, uPointer: pointer },
  });
  if (!fx.fallback) {
    const target_ = typeof target === 'string' ? document.querySelector(target) : target;
    const move = (e) => { const r = target_.getBoundingClientRect(); fx.set('uPointer', [((e.clientX - r.left) / r.width) * 2 - 1, -(((e.clientY - r.top) / r.height) * 2 - 1)]); };
    target_.addEventListener('pointermove', move, { passive: true });
  }
  return fx;
}
