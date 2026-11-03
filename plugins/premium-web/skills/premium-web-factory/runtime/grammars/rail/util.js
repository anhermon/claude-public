// Commerce imports this standalone utility module; rail never depends on WebGL.
export { clamp } from './scroll.js';
export const $ = (root, selector) => root.querySelector(selector);
export const $$ = (root, selector) => [...root.querySelectorAll(selector)];
const HASH = { a: 127.1, b: 311.7, c: 43758.5453 };
export const hash01 = (i) => { const s = Math.sin(i * HASH.a + HASH.b) * HASH.c; return s - Math.floor(s); };
export const fmtNum = (n, decimals = 0) => n.toLocaleString('en-US', { minimumFractionDigits: decimals, maximumFractionDigits: decimals });
