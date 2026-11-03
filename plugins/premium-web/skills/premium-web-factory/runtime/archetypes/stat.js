// stat: the stepper fans the subject out (first s groups lit) and four numerals come from a labelled sample model.
import { $, $$, fmtBig, fmtNum } from '../util.js';

const LIT = 0.9, DIM = 0.1, SMALL_MAX = 1e4;
const MODES = {
  divide: (n, s) => n.total / s,
  log: (n, s) => n.base + n.per * Math.log2(s),
  linear: (n, s) => n.base + n.per * s,
  inverse: (n, s) => n.base / s + (n.per || 0),
};
export function mount(el, { subject, ch }) {
  const c = ch.copy, K = ch.target.k || c.steps.length, stepsEl = $(el, '[data-role=steps]'), nums = $$(el, '[data-role=num]');
  let sel = 0;
  const paint = () => {
    const s = c.steps[sel];
    (c.numerals || []).forEach((n, k) => { const v = MODES[n.mode](n, s); nums[k].textContent = (v >= SMALL_MAX ? fmtBig(v) : fmtNum(v, n.decimals ?? 0)) + (n.suffix || ''); });
    $$(stepsEl, '.chip').forEach((b, j) => b.setAttribute('aria-checked', String(j === sel)));
  };
  c.steps.forEach((s, j) => { const b = document.createElement('button'); b.className = 'chip'; b.type = 'button'; b.setAttribute('role', 'radio'); b.textContent = String(s); b.onclick = () => { sel = j; paint(); }; stepsEl.append(b); });
  paint();
  const custom = { fn(_t, o) { const s = Math.min(K, c.steps[sel]); for (let i = 0; i < subject.M; i++) o[i] = subject.groupOf(i, K) < s ? LIT : DIM; } };
  return { enter() { subject.setCustom(custom); }, leave() { subject.setCustom(null); } };
}
