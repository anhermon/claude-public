// Small shared helpers for the generated runtime (re-exports the stage util so subjects import from one place).
export { clamp, lerp, smoothstep, expoOut, mulberry32, hex } from '../../gl/src/util.js';

export const $ = (root, sel) => root.querySelector(sel);
export const $$ = (root, sel) => [...root.querySelectorAll(sel)];
export const hash01 = (i) => { const s = Math.sin(i * 127.1 + 311.7) * 43758.5453; return s - Math.floor(s); };
const BIG = [[1e9, 'B'], [1e6, 'M'], [1e4, 'k']];
/** 480000000 -> "480M"; 1234 -> "1,234" */
export function fmtBig(n, decimals = 0) {
  for (const [v, s] of BIG) if (Math.abs(n) >= v) return (n / v).toFixed(n / v >= 100 ? 0 : 1).replace(/\.0$/, '') + s;
  return n.toLocaleString('en-US', { minimumFractionDigits: decimals, maximumFractionDigits: decimals });
}
export const fmtNum = (n, decimals = 0) => n.toLocaleString('en-US', { minimumFractionDigits: decimals, maximumFractionDigits: decimals });
