// hero: paints the live query readout from subject.st.scan (the real scan of the subject's items).
import { $, $$ } from '../util.js';

const READOUT_MS = 110, FAST_SCAN_MS = 0.1, OFF_STRIDE = 13;
export function mount(el, { subject }) {
  const rows = $$(el, '[data-role=hits] li'), msEl = $(el, '[data-role=ms]'), nEl = $(el, '[data-role=n]');
  const paint = () => {
    const scan = subject.st.scan;
    if (!subject.live) { rows.forEach((r, k) => { r.children[1].textContent = subject.itemName(k * OFF_STRIDE); r.children[2].textContent = 'n/a'; }); msEl.textContent = 'n/a (WebGL off)'; return; }
    if (!scan.top.length) return;
    rows.forEach((r, k) => { const t = scan.top[k]; if (t) { r.children[1].textContent = subject.itemName(t.i); r.children[2].textContent = t.d.toFixed(2); } });
    msEl.textContent = `${scan.ms < FAST_SCAN_MS ? '<0.1' : scan.ms.toFixed(1)} ms`; nEl.textContent = String(scan.n);
  };
  setInterval(paint, READOUT_MS); paint();
  return {};
}
