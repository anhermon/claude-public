// gl/fx-glsl: shared GLSL chunks (strings) for the shader-field modules. Concatenated after the fx-canvas header.
export const GLSL_HASH = /* glsl */ `
float hash21(vec2 p){ vec3 p3 = fract(vec3(p.xyx) * .1031); p3 += dot(p3, p3.yzx + 33.33); return fract((p3.x + p3.y) * p3.z); }
vec2 hash22(vec2 p){ vec3 p3 = fract(vec3(p.xyx) * vec3(.1031, .1030, .0973)); p3 += dot(p3, p3.yzx + 33.33); return fract((p3.xx + p3.yz) * p3.zy); }
`;

export const GLSL_NOISE = /* glsl */ `
float vnoise(vec2 p){
  vec2 i = floor(p), f = fract(p);
  vec2 u = f * f * f * (f * (f * 6. - 15.) + 10.);
  return mix(mix(hash21(i), hash21(i + vec2(1, 0)), u.x), mix(hash21(i + vec2(0, 1)), hash21(i + vec2(1, 1)), u.x), u.y);
}
const mat2 FBM_ROT = mat2(.8, .6, -.6, .8);
float fbm(vec2 p){
  float a = .5, s = 0.;
  for (int i = 0; i < 5; i++) { s += a * vnoise(p); p = FBM_ROT * p * 2.02 + 17.3; a *= .5; }
  return s;
}
float fbm3(vec2 p){
  float a = .5, s = 0.;
  for (int i = 0; i < 3; i++) { s += a * vnoise(p); p = FBM_ROT * p * 2.02 + 17.3; a *= .5; }
  return s;
}
mat2 rot2(float a){ float c = cos(a), s = sin(a); return mat2(c, -s, s, c); }
`;

// OKLab <-> linear sRGB, then sRGB encode. Gradients are mixed in OKLab to avoid grey mud.
export const GLSL_OKLAB = /* glsl */ `
vec3 oklab2lin(vec3 c){
  float l = c.x + .3963377774 * c.y + .2158037573 * c.z;
  float m = c.x - .1055613458 * c.y - .0638541728 * c.z;
  float s = c.x - .0894841775 * c.y - 1.291485548 * c.z;
  l = l * l * l; m = m * m * m; s = s * s * s;
  return vec3(4.0767416621 * l - 3.3077115913 * m + .2309699292 * s,
             -1.2684380046 * l + 2.6097574011 * m - .3413193965 * s,
             -.0041960863 * l - .7034186147 * m + 1.707614701 * s);
}
vec3 lin2srgb(vec3 c){ c = max(c, 0.); return mix(c * 12.92, 1.055 * pow(c, vec3(1. / 2.4)) - .055, step(.0031308, c)); }
vec3 srgb2lin(vec3 c){ return mix(c / 12.92, pow((c + .055) / 1.055, vec3(2.4)), step(.04045, c)); }
`;

// Film grain + sub-LSB dither applied AFTER sRGB encode so dark gradients do not band at 8 bit.
// grain 0 still dithers. Grain steps at 24 fps (film), weighted to midtones.
export const GLSL_FINISH = /* glsl */ `
vec3 finish(vec3 srgb, vec2 frag, float t, float grain){
  float l = dot(srgb, vec3(.299, .587, .114));
  vec2 seed = frag + floor(t * 24.) * vec2(37.1, 17.7);
  float n = hash21(seed) - .5;
  float mid = .35 + 1.3 * (1. - abs(2. * l - 1.));
  float tri = hash21(frag * 1.37 + 91.7) + hash21(frag * .73 + 13.1) - 1.;
  return srgb + n * grain * mid + tri / 255.;
}
`;

export const GLSL_TONE = /* glsl */ `
vec3 tonemapExp(vec3 x){ return 1. - exp(-x); }
`;
