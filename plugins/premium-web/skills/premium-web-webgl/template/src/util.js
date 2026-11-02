// gl/util: tiny shared helpers for the GL modules (no three import at load time).
// three.js r170 is vendored at template/vendor (MIT, see vendor/LICENSES.md); it is only fetched when a stage actually goes GL.
let threePromise = null;
export const loadThree = () => (threePromise ||= import('../vendor/three.module.min.js'));

export const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
export const lerp = (a, b, t) => a + (b - a) * t;
export const smoothstep = (a, b, x) => { const t = clamp((x - a) / (b - a)); return t * t * (3 - 2 * t); };
export const expoOut = (t) => (t >= 1 ? 1 : 1 - Math.pow(2, -10 * t));        // GSAP expo.out; measured from public reference sites, 2026-11
export const power3InOut = (t) => (t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2); // GSAP power3.inOut

const HEX_RE = /^#?([0-9a-f]{3}|[0-9a-f]{6})$/i;
const CHANNEL_MAX = 255;
/** '#f04f24' -> [r,g,b] in 0..1, plain sRGB numbers (shader-space, no colour management). */
export function hex(s) {
  const m = HEX_RE.exec(String(s).trim());
  if (!m) return [0, 0, 0];
  let h = m[1];
  if (h.length === 3) h = h.replace(/./g, '$&$&');
  const n = parseInt(h, 16);
  return [(n >> 16) / CHANNEL_MAX, ((n >> 8) & 255) / CHANNEL_MAX, (n & 255) / CHANNEL_MAX];
}
export const rgbCss = (c, a = 1) => `rgba(${Math.round(c[0] * 255)},${Math.round(c[1] * 255)},${Math.round(c[2] * 255)},${a})`;

/** Deterministic RNG so every device draws the same shapes. */
export function mulberry32(seed) {
  let a = seed | 0;
  return () => {
    a = (a + 0x6d2b79f5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}
export const gauss = (r) => { let u = 0, v = 0; while (!u) u = r(); while (!v) v = r(); return Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * v); };

export const resolveEl = (t) => (typeof t === 'string' ? document.querySelector(t) : t) || document.body;

/** reduced-motion: explicit option wins, else the OS media query */
export function reducedMotion(options = {}) {
  if (typeof options.reduced === 'boolean') return options.reduced;
  return typeof matchMedia === 'function' && matchMedia('(prefers-reduced-motion: reduce)').matches;
}
