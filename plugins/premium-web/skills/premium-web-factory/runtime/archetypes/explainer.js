// explainer: layer buttons light their group in the subject; the slider drives the numerals and how many items a search visits.
import { $, $$, hash01, fmtNum } from '../util.js';

const IDLE_LIT = 0.08, VISIT_BASE = 0.08, VISIT_SPAN = 0.4, VISIT_LEVEL = 0.55, SEL_LEVEL = 0.9, SAT_K = 4, EXP_P = 2.5, PULSE = { rate: 3, amp: 0.15 };
const CURVES = { lin: (t) => t, sat: (t) => 1 - Math.exp(-SAT_K * t), exp: (t) => Math.pow(t, EXP_P) };

export function mount(el, { subject, ch }) {
  const c = ch.copy, K = c.layers.length, layers = $$(el, '.layer'), slider = $(el, '[data-role=slider]'), out = $(el, '[data-role=slider-out]'), nums = $$(el, '[data-role=num]');
  let sel = -1;
  const frac = () => (slider ? (slider.value - slider.min) / (slider.max - slider.min) : 0.5);
  const paint = () => {
    const f = frac(); if (out) out.textContent = slider.value + (c.slider.suffix || '');
    (c.numerals || []).forEach((n, k) => { nums[k].textContent = fmtNum(n.base + n.span * (CURVES[n.curve] || CURVES.lin)(f), n.decimals ?? 0) + (n.suffix || ''); });
  };
  slider?.addEventListener('input', paint); paint();
  layers.forEach((b, k) => { b.onclick = () => { sel = sel === k ? -1 : k; layers.forEach((x, j) => x.setAttribute('aria-pressed', String(j === sel))); }; });
  const custom = { fn(time, o) {
    const f = frac();
    for (let i = 0; i < subject.M; i++) {
      const g = subject.groupOf(i, K), base = sel < 0 ? 0 : g === sel ? SEL_LEVEL : IDLE_LIT, visited = hash01(i + 41) < VISIT_BASE + VISIT_SPAN * f ? VISIT_LEVEL : 0;
      o[i] = Math.max(base, visited) * (1 - PULSE.amp + PULSE.amp * Math.sin(time * PULSE.rate + i));
    }
  } };
  return { enter() { subject.setCustom(custom); }, leave() { subject.setCustom(null); } };
}
