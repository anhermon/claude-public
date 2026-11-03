// faq: one subject item per answer. Opening an answer pulses its item (and its neighbours); none open -> the first.
import { $$ } from '../util.js';

const NEIGHBOUR = 0.45, PULSE = { rate: 2.4, base: 0.75, amp: 0.25 };
export function mount(el, { subject }) {
  const items = $$(el, 'details'), n = items.length;
  let active = Math.max(0, items.findIndex((d) => d.open));
  items.forEach((d, k) => d.addEventListener('toggle', () => { if (d.open) active = k; }));
  const custom = { fn(time, o) {
    const idx = Math.floor(((active + 0.5) * subject.M) / n);
    o[idx] = PULSE.base + PULSE.amp * Math.sin(time * PULSE.rate);
    if (idx > 0) o[idx - 1] = NEIGHBOUR; if (idx < subject.M - 1) o[idx + 1] = NEIGHBOUR;
  } };
  return { enter() { subject.setCustom(custom); }, leave() { subject.setCustom(null); } };
}
