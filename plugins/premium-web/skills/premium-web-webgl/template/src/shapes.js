// gl/shapes: point-target samplers for point-morph. Pure maths, no three import.
// Every sampler returns a Float32Array(n*3) of positions, roughly inside radius `R`, in random order
// (random order is what makes dust drawRange cuts by the governor look uniform).
import { mulberry32, gauss } from './util.js';

const TAU = Math.PI * 2;
const DEFAULT_R = 4.5;          // world-space radius shapes are fitted to
const SEED = 1337;

function rotate(out, [rx = 0, ry = 0, rz = 0]) {
  if (!rx && !ry && !rz) return out;
  const cx = Math.cos(rx), sx = Math.sin(rx), cy = Math.cos(ry), sy = Math.sin(ry), cz = Math.cos(rz), sz = Math.sin(rz);
  for (let i = 0; i < out.length; i += 3) {
    let x = out[i], y = out[i + 1], z = out[i + 2], t;
    t = y * cx - z * sx; z = y * sx + z * cx; y = t;
    t = x * cy + z * sy; z = -x * sy + z * cy; x = t;
    t = x * cz - y * sz; y = x * sz + y * cz; x = t;
    out[i] = x; out[i + 1] = y; out[i + 2] = z;
  }
  return out;
}

export function sphere(n, { R = DEFAULT_R, thickness = 0.12, seed = SEED, rotation } = {}) {
  const r = mulberry32(seed), out = new Float32Array(n * 3);
  for (let i = 0; i < n; i++) {
    const u = r() * 2 - 1, a = r() * TAU, s = Math.sqrt(1 - u * u), k = R * (1 - r() * thickness);
    out.set([s * Math.cos(a) * k, u * k, s * Math.sin(a) * k], i * 3);
  }
  return rotate(out, rotation || []);
}

/** hollow torus-ish blob. */
export function torus(n, { R = DEFAULT_R * 0.68, tube = DEFAULT_R * 0.3, wobble = 0.12, seed = SEED + 1, rotation } = {}) {
  const r = mulberry32(seed), out = new Float32Array(n * 3);
  for (let i = 0; i < n; i++) {
    const u = r() * TAU, v = r() * TAU, w = 1 + (r() - 0.5) * wobble, rr = tube * w;
    out.set([(R + rr * Math.cos(v)) * Math.cos(u), rr * Math.sin(v), (R + rr * Math.cos(v)) * Math.sin(u)], i * 3);
  }
  return rotate(out, rotation || [0.5, 0, 0.2]);
}

/** tilted log-spiral disc with discrete rings. */
export function galaxy(n, { R = DEFAULT_R * 1.25, arms = 2, twist = 2.4, rings = 3, ringShare = 0.3, thick = 0.1, seed = SEED + 2, rotation } = {}) {
  const r = mulberry32(seed), out = new Float32Array(n * 3);
  for (let i = 0; i < n; i++) {
    let rad;
    if (r() < ringShare) rad = R * ((1 + Math.floor(r() * rings)) / (rings + 0.4)) + gauss(r) * R * 0.012;
    else rad = Math.pow(r(), 1.7) * R;
    const arm = Math.floor(r() * arms) * (TAU / arms), a = arm + (rad / R) * twist * Math.PI + gauss(r) * 0.22 * (0.3 + rad / R);
    const y = gauss(r) * thick * (1.2 - rad / R) * (R * 0.2);
    out.set([Math.cos(a) * rad, y, Math.sin(a) * rad], i * 3);
  }
  return rotate(out, rotation || [0.18, 0, 0]);
}

export function helix(n, { R = DEFAULT_R * 0.55, height = DEFAULT_R * 2.1, turns = 3, strands = 2, jitter = 0.18, seed = SEED + 3, rotation } = {}) {
  const r = mulberry32(seed), out = new Float32Array(n * 3);
  for (let i = 0; i < n; i++) {
    const t = r(), s = Math.floor(r() * strands), a = t * turns * TAU + s * (TAU / strands);
    out.set([Math.cos(a) * R + gauss(r) * jitter, (t - 0.5) * height, Math.sin(a) * R + gauss(r) * jitter], i * 3);
  }
  return rotate(out, rotation || [0, 0, 0]);
}

/** Sample the filled pixels of a canvas mask, weighted by (alpha * luma) when `weighted`. */
function fromMask(cv, n, { width, seed, depth, weighted = false }) {
  const w = cv.width, h = cv.height, d = cv.getContext('2d', { willReadFrequently: true }).getImageData(0, 0, w, h).data;
  const idx = [];
  const cdf = [];
  let acc = 0;
  for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) {
    const o = (y * w + x) * 4, a = d[o + 3] / 255;
    const wt = weighted ? a * (0.2126 * d[o] + 0.7152 * d[o + 1] + 0.0722 * d[o + 2]) / 255 : a > 0.5 ? 1 : 0;
    if (wt > 0.02) { idx.push(x, y); acc += wt; cdf.push(acc); }
  }
  const r = mulberry32(seed), out = new Float32Array(n * 3), m = cdf.length;
  if (!m) return out;
  const scale = width / w;
  for (let i = 0; i < n; i++) {
    const t = r() * acc; let lo = 0, hi = m - 1;
    while (lo < hi) { const mid = (lo + hi) >> 1; if (cdf[mid] < t) lo = mid + 1; else hi = mid; }
    out.set([(idx[lo * 2] + r() - w / 2) * scale, -(idx[lo * 2 + 1] + r() - h / 2) * scale, (r() - 0.5) * depth], i * 3);
  }
  return out;
}

/** Text mask. `font` is any canvas font string; fonts must already be loaded (system fonts always are). */
export function text(n, { text: str = 'STAGE', font = '700 220px "Helvetica Neue", Arial, sans-serif', width = DEFAULT_R * 3.4, depth = 0.5, seed = SEED + 4, rotation } = {}) {
  const cv = document.createElement('canvas'), c = cv.getContext('2d');
  c.font = font;
  const px = parseInt(/(\d+)px/.exec(font)?.[1] || '220', 10), tw = Math.ceil(c.measureText(str).width) + 8;
  cv.width = tw; cv.height = Math.ceil(px * 1.3);
  c.font = font; c.fillStyle = '#fff'; c.textBaseline = 'middle'; c.textAlign = 'center';
  c.fillText(str, tw / 2, cv.height / 2);
  return rotate(fromMask(cv, n, { width, seed, depth }), rotation || []);
}

/** Image (HTMLImageElement/ImageBitmap/canvas, same-origin): density follows alpha*luma. */
export function image(n, src, { width = DEFAULT_R * 2.6, depth = 0.6, maxSide = 256, seed = SEED + 5, rotation } = {}) {
  const sw = src.naturalWidth || src.width, sh = src.naturalHeight || src.height, k = Math.min(1, maxSide / Math.max(sw, sh));
  const cv = document.createElement('canvas'); cv.width = Math.max(1, Math.round(sw * k)); cv.height = Math.max(1, Math.round(sh * k));
  cv.getContext('2d').drawImage(src, 0, 0, cv.width, cv.height);
  return rotate(fromMask(cv, n, { width, seed, depth, weighted: true }), rotation || []);
}

/** Arbitrary mesh surface: `position` flat xyz array, optional `index`; area-weighted triangle sampling, fitted to radius R. */
export function mesh(n, position, index = null, { R = DEFAULT_R, seed = SEED + 6, rotation } = {}) {
  const tri = index ? index.length / 3 : position.length / 9, vi = (t, k) => (index ? index[t * 3 + k] : t * 3 + k);
  const cdf = new Float32Array(tri); let acc = 0;
  const P = (v, c) => position[v * 3 + c];
  for (let t = 0; t < tri; t++) {
    const a = vi(t, 0), b = vi(t, 1), c = vi(t, 2);
    const ux = P(b, 0) - P(a, 0), uy = P(b, 1) - P(a, 1), uz = P(b, 2) - P(a, 2), vx = P(c, 0) - P(a, 0), vy = P(c, 1) - P(a, 1), vz = P(c, 2) - P(a, 2);
    acc += 0.5 * Math.hypot(uy * vz - uz * vy, uz * vx - ux * vz, ux * vy - uy * vx); cdf[t] = acc;
  }
  const r = mulberry32(seed), out = new Float32Array(n * 3);
  for (let i = 0; i < n; i++) {
    const s = r() * acc; let lo = 0, hi = tri - 1;
    while (lo < hi) { const mid = (lo + hi) >> 1; if (cdf[mid] < s) lo = mid + 1; else hi = mid; }
    let u = r(), v = r(); if (u + v > 1) { u = 1 - u; v = 1 - v; }
    const a = vi(lo, 0), b = vi(lo, 1), c = vi(lo, 2);
    for (let k = 0; k < 3; k++) out[i * 3 + k] = P(a, k) + (P(b, k) - P(a, k)) * u + (P(c, k) - P(a, k)) * v;
  }
  let mx = 0, cx = 0, cy = 0, cz = 0;
  for (let i = 0; i < n; i++) { cx += out[i * 3]; cy += out[i * 3 + 1]; cz += out[i * 3 + 2]; }
  cx /= n; cy /= n; cz /= n;
  for (let i = 0; i < n; i++) { out[i * 3] -= cx; out[i * 3 + 1] -= cy; out[i * 3 + 2] -= cz; mx = Math.max(mx, Math.hypot(out[i * 3], out[i * 3 + 1], out[i * 3 + 2])); }
  const k = mx ? R / mx : 1; for (let i = 0; i < out.length; i++) out[i] *= k;
  return rotate(out, rotation || []);
}

/** Resolve a shape spec to positions: 'torus' | { type:'galaxy', ...opts } | Float32Array | { positions }. Image specs are async: use resolveAsync. */
export const SAMPLERS = { sphere, torus, galaxy, helix, text };
export function resolve(spec, n) {
  if (spec instanceof Float32Array) return spec;
  if (spec?.positions) return spec.positions;
  const type = typeof spec === 'string' ? spec : spec.type, opts = typeof spec === 'string' ? {} : spec;
  if (type === 'mesh') return mesh(n, opts.position, opts.index, opts);
  if (type === 'image') return null;
  const f = SAMPLERS[type];
  if (!f) throw new Error(`gl/shapes: unknown shape "${type}"`);
  return f(n, opts);
}
export function loadImage(src) {
  return new Promise((res, rej) => { const im = new Image(); im.onload = () => res(im); im.onerror = rej; im.src = src; });
}
