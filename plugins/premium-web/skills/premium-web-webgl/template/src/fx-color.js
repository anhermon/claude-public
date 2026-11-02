// gl/fx-color: colour helpers shared by the shader-field modules. sRGB hex <-> OKLab, palette morph by `progress`.
// No allocation in the per-frame paths (paletteAt writes into a caller-owned Float32Array).
const HEX_RADIX = 16;
const BYTE_MAX = 255;
const SRGB_LIN_KNEE = 0.04045;
const SRGB_GAMMA = 2.4;
const SRGB_A = 0.055;
const SRGB_LIN_SLOPE = 12.92;

export const clamp01 = (x) => Math.min(1, Math.max(0, x));
export const lerp = (a, b, t) => a + (b - a) * t;
export const smooth01 = (t) => t * t * (3 - 2 * t);
/** frame-rate independent damped approach: cur -> target, `rate` is the per-60Hz-frame factor (0.08-0.1 same source) */
export const damp = (cur, target, rate, dt) => cur + (target - cur) * (1 - Math.pow(1 - rate, dt * 60));

/** "#rrggbb" | "#rgb" | [r,g,b] (0-1 sRGB) -> [r,g,b] 0-1 sRGB */
export function parseColor(c) {
  if (Array.isArray(c)) return c;
  let h = String(c).replace('#', '');
  if (h.length === 3) h = h.split('').map((x) => x + x).join('');
  const n = parseInt(h, HEX_RADIX);
  return [((n >> 16) & BYTE_MAX) / BYTE_MAX, ((n >> 8) & BYTE_MAX) / BYTE_MAX, (n & BYTE_MAX) / BYTE_MAX];
}
export const toLinear = (v) => (v <= SRGB_LIN_KNEE ? v / SRGB_LIN_SLOPE : Math.pow((v + SRGB_A) / (1 + SRGB_A), SRGB_GAMMA));
export const fromLinear = (v) => (v <= 0.0031308 ? v * SRGB_LIN_SLOPE : (1 + SRGB_A) * Math.pow(v, 1 / SRGB_GAMMA) - SRGB_A);

/** sRGB colour -> OKLab [L,a,b] */
export function toOklab(c) {
  const [r, g, b] = parseColor(c).map(toLinear);
  const l = Math.cbrt(0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b);
  const m = Math.cbrt(0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b);
  const s = Math.cbrt(0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b);
  return [0.2104542553 * l + 0.793617785 * m - 0.0040720468 * s, 1.9779984951 * l - 2.428592205 * m + 0.4505937099 * s, 0.0259040371 * l + 0.7827717662 * m - 0.808675766 * s];
}
/** OKLab -> linear-light RGB triple (what the shaders want for the uniform "linear" convention) */
export function oklabToLinear([L, a, b]) {
  const l = Math.pow(L + 0.3963377774 * a + 0.2158037573 * b, 3);
  const m = Math.pow(L - 0.1055613458 * a - 0.0638541728 * b, 3);
  const s = Math.pow(L - 0.0894841775 * a - 1.291485548 * b, 3);
  return [4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s, -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s, -0.0041960863 * l - 0.7034186147 * m + 1.707614701 * s];
}
export const toLinearRgb = (c) => parseColor(c).map(toLinear);

/** Pre-convert palettes (arrays of colours) to flat OKLab Float32Arrays: [[c0..cN-1], ...] -> Float32Array[] */
export function compilePalettes(palettes) {
  return palettes.map((p) => {
    const out = new Float32Array(p.length * 3);
    p.forEach((c, i) => out.set(toOklab(c), i * 3));
    return out;
  });
}
/** Blend compiled palettes by progress 0..1 (linear in OKLab between neighbours) into `out` (Float32Array, same length). */
export function paletteAt(compiled, progress, out) {
  const last = compiled.length - 1;
  const x = clamp01(progress) * last;
  const i = Math.min(last - 1 < 0 ? 0 : last - 1, Math.floor(x));
  const a = compiled[i], b = compiled[Math.min(last, i + 1)], t = last === 0 ? 0 : smooth01(x - i);
  for (let k = 0; k < out.length; k++) out[k] = a[k] + (b[k] - a[k]) * t;
  return out;
}
