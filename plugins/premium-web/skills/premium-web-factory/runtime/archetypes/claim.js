// claim: group chips filter the subject (mask) and the ranked list reads the same scan the hero readout shows.
import { $, $$ } from '../util.js';

const LIST_MS = 110, OFF_STRIDE = 7;
export function mount(el, { subject, piece }) {
  const G = piece.interaction.groups, chipsEl = $(el, '[data-role=chips]'), rows = $$(el, '[data-role=list] li'), count = $(el, '[data-role=count]');
  const on = new Set(G.keys()), mask = new Uint8Array(subject.M).fill(1);
  const apply = () => {
    for (let i = 0; i < subject.M; i++) mask[i] = on.has(subject.groupOf(i, G.length)) ? 1 : 0;
    subject.setMask(mask); $$(chipsEl, '.chip').forEach((c, j) => c.setAttribute('aria-pressed', String(on.has(j))));
  };
  G.forEach((label, k) => {
    const b = document.createElement('button'); b.className = 'chip'; b.type = 'button'; b.textContent = label; b.setAttribute('aria-pressed', 'true');
    b.onclick = () => { on.has(k) ? on.delete(k) : on.add(k); if (!on.size) G.forEach((_, j) => on.add(j)); apply(); };
    chipsEl.append(b);
  });
  if (!G.length) chipsEl.hidden = true;
  const paint = () => {
    if (!subject.live) { rows.forEach((r, k) => { r.children[0].textContent = k + 1; r.children[1].textContent = subject.itemName(k * OFF_STRIDE); r.children[2].textContent = ''; }); count.textContent = 'WebGL is off: the live query needs it.'; return; }
    const top = subject.st.scan.top; if (!top.length) return;
    rows.forEach((r, k) => { const t = top[k]; r.children[0].textContent = t ? k + 1 : '-'; r.children[1].textContent = t ? subject.itemName(t.i) : '-'; r.children[2].textContent = t ? t.d.toFixed(2) : ''; });
    const n = subject.st.scan.n; count.textContent = `${n} of ${subject.M} items match the filter. Top ${Math.min(rows.length, top.length)} by distance.`;
  };
  setInterval(paint, LIST_MS); paint();
  return {};
}
