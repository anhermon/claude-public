// Morph-target layouts: (n, k, rng, params) -> Float32Array(n*3), radius about LAYOUT_R. Grouped layouts (layers, clusters,
// towers, shards) assign item i to group floor(i*k/n): the same rule every archetype uses for chips, tiers and layers.
import { mulberry32, gauss } from './rand.js';

export const LAYOUT_R = 3;
const GOLDEN = Math.PI * (3 - Math.sqrt(5));
const TAU = Math.PI * 2;
export const groupOf = (i, n, k) => Math.min(k - 1, Math.floor((i * k) / n));

const grid3 = (n, half) => { const m = Math.ceil(Math.cbrt(n)); return (i) => { const x = i % m, y = Math.floor(i / m) % m, z = Math.floor(i / (m * m)); const c = (v) => (m > 1 ? (v / (m - 1) - 0.5) * 2 * half : 0); return [c(x), c(y), c(z)]; }; };

const L = {
  cube: (n, k, r, p) => { const f = grid3(n, LAYOUT_R * 0.62 * (p.spread || 1)); return (i) => { const [x, y, z] = f(i); return [x + (r() - 0.5) * 0.12, y + (r() - 0.5) * 0.12, z + (r() - 0.5) * 0.12]; }; },
  sphere: (n, k, r, p) => (i) => { const y = 1 - ((i + 0.5) / n) * 2, rad = Math.sqrt(1 - y * y), a = i * GOLDEN, R = LAYOUT_R * 0.92 * (p.spread || 1); return [Math.cos(a) * rad * R, y * R, Math.sin(a) * rad * R]; },
  ring: (n, k, r, p) => (i) => { const a = (i / n) * TAU, R = LAYOUT_R * 0.95 * (p.spread || 1); return [Math.cos(a) * R, gauss(r) * 0.22, Math.sin(a) * R + gauss(r) * 0.18]; },
  helix: (n, k, r, p) => (i) => { const t = i / n, a = t * (p.turns || 3.2) * TAU + (i % 2) * Math.PI; return [Math.cos(a) * LAYOUT_R * 0.55, (t - 0.5) * LAYOUT_R * 2.1, Math.sin(a) * LAYOUT_R * 0.55]; },
  layers: (n, k, r, p) => (i) => { const g = groupOf(i, n, k), per = n / k, j = i - g * per, a = j * GOLDEN, rad = Math.sqrt((j + 0.5) / per) * LAYOUT_R * (0.95 - 0.09 * g) * (p.spread || 1); return [Math.cos(a) * rad, (0.5 - g / Math.max(1, k - 1)) * LAYOUT_R * 1.5, Math.sin(a) * rad * 0.7]; },
  clusters: (n, k, r, p) => (i) => { const g = groupOf(i, n, k), a = (g / k) * TAU + 0.4, R = LAYOUT_R * 0.66 * (p.spread || 1); return [Math.cos(a) * R + gauss(r) * 0.42, Math.sin(a * 1.7) * R * 0.45 + gauss(r) * 0.42, Math.sin(a) * R * 0.8 + gauss(r) * 0.42]; },
  towers: (n, k, r, p) => (i) => { const g = groupOf(i, n, k), per = n / k, j = i - g * per, h = (0.45 + 0.55 * ((g + 1) / k)) * LAYOUT_R * 1.7, x = (g - (k - 1) / 2) * LAYOUT_R * (1.7 / Math.max(1, k - 1)) * (p.spread || 1); const a = j * GOLDEN; return [x + Math.cos(a) * 0.28, -LAYOUT_R * 0.8 + (j / per) * h, Math.sin(a) * 0.28]; },
  shards: (n, k, r, p) => (i) => { const g = groupOf(i, n, k), per = n / k, j = i - g * per, m = Math.ceil(Math.cbrt(per)), x = j % m, y = Math.floor(j / m) % m, z = Math.floor(j / (m * m)), s = LAYOUT_R * 0.11; const cx = (g - (k - 1) / 2) * (LAYOUT_R * 2.1 / Math.max(1, k - 1)) * (p.spread || 1), cy = Math.sin(g * 1.9) * LAYOUT_R * 0.35; return [cx + (x - (m - 1) / 2) * s, cy + (y - (m - 1) / 2) * s, (z - (m - 1) / 2) * s + Math.cos(g * 1.3) * 0.6]; },
  wave: (n, k, r, p) => { const m = Math.ceil(Math.sqrt(n)); return (i) => { const x = (i % m) / (m - 1) - 0.5, z = Math.floor(i / m) / (m - 1) - 0.5, W = LAYOUT_R * 2.3 * (p.spread || 1); return [x * W, Math.sin(x * 9 + z * 5) * 0.55 * LAYOUT_R * 0.45, z * W * 0.7]; }; },
  galaxy: (n, k, r, p) => (i) => { const t = (i + 0.5) / n, rad = Math.sqrt(t) * LAYOUT_R * 1.05 * (p.spread || 1), a = rad * 2.2 + (i % 2) * Math.PI; return [Math.cos(a) * rad + gauss(r) * 0.1, gauss(r) * 0.12 * (1.2 - t), Math.sin(a) * rad + gauss(r) * 0.1]; },
  scatter: (n, k, r, p) => () => { const u = r() * 2 - 1, a = r() * TAU, s = Math.sqrt(1 - u * u), R = LAYOUT_R * 1.1 * Math.cbrt(r()) * (p.spread || 1); return [s * Math.cos(a) * R, u * R, s * Math.sin(a) * R]; },
  plane: (n, k, r, p) => { const m = Math.ceil(Math.sqrt(n)); return (i) => [((i % m) / (m - 1) - 0.5) * LAYOUT_R * 2.2 * (p.spread || 1), (Math.floor(i / m) / (m - 1) - 0.5) * LAYOUT_R * 2.2 * (p.spread || 1), 0]; },
};

/** @returns Float32Array(n*3) */
export function buildLayout(name, n, k, seed, params = {}) {
  const fn = L[name];
  if (!fn) throw new Error(`unknown layout ${name}`);
  const r = mulberry32(seed), pick = fn(n, k, r, params), out = new Float32Array(n * 3);
  for (let i = 0; i < n; i++) out.set(pick(i), i * 3);
  return out;
}
export const LAYOUT_NAMES = Object.keys(L);

/** A scattered starting cloud used by the assembly animation. */
export function buildScatter(n, seed, radius) {
  const r = mulberry32(seed), out = new Float32Array(n * 3);
  for (let i = 0; i < n; i++) { const u = r() * 2 - 1, a = r() * TAU, s = Math.sqrt(1 - u * u), R = radius * (0.5 + 0.5 * Math.cbrt(r())); out.set([s * Math.cos(a) * R, u * R, s * Math.sin(a) * R], i * 3); }
  return out;
}
