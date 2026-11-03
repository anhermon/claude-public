// ship: ARIA tabs (arrow keys) and three pulsing items in the subject standing in for the sample response.
import { $$ } from '../util.js';

const RESULT_AT = [0.12, 0.5, 0.8], PULSE = { rate: 2, base: 0.6, amp: 0.4 };
export function mount(el, { subject }) {
  const tabs = $$(el, '[role=tab]'), panes = $$(el, '[role=tabpanel]');
  const show = (k) => tabs.forEach((t, j) => { t.setAttribute('aria-selected', String(j === k)); t.tabIndex = j === k ? 0 : -1; panes[j].hidden = j !== k; });
  tabs.forEach((t, k) => { t.onclick = () => show(k); t.onkeydown = (e) => { const d = e.key === 'ArrowRight' ? 1 : e.key === 'ArrowLeft' ? -1 : 0; if (d) { const n = (k + d + tabs.length) % tabs.length; show(n); tabs[n].focus(); } }; });
  const custom = { fn(time, o) { RESULT_AT.forEach((f) => { o[Math.floor(f * subject.M)] = PULSE.base + PULSE.amp * Math.sin(time * PULSE.rate + f * 9); }); } };
  return { enter() { subject.setCustom(custom); }, leave() { subject.setCustom(null); } };
}
