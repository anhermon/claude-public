// pricing: every tier is priced live at the visitor's usage; the cheapest tier that fits is "best fit" (click to pick another).
// The sliders DRIVE the subject: lit fraction = usage, tower height = cost, the selected tier's group stays lit, hover lifts it.
import { $, $$, clamp, hash01, fmtNum } from '../util.js';

const LIT_BASE = 0.1, USAGE_LIT = 0.5, SEL_LIT = 0.95, STRETCH = { min: 0.8, span: 0.45 }, PULSE = { rate: 2, amp: 0.1 };
const money = (cur, v) => cur + fmtNum(v, Number.isInteger(v) ? 0 : 2);

export function mount(el, { subject, piece }) {
  const cm = piece.commerce, T = cm.tiers, K = T.length, rows = $$(el, '.trow'), inp = {}, outp = {};
  cm.inputs.forEach((x) => { inp[x.id] = $(el, `[data-role=in-${x.id}]`); outp[x.id] = $(el, `[data-role=out-${x.id}]`); });
  const totalEl = $(el, '[data-role=total]'), lineEl = $(el, '[data-role=line]');
  let manual = -1, usage = 0, selNow = 0;
  const val = (id) => (inp[id] ? +inp[id].value : 0);
  const part = (t, id, v) => Math.max(0, v - (t.included?.[id] ?? 0)) * (t.rates?.[id] ?? 0);
  const cost = (t, a, b) => t.fixed + part(t, 'a', a) + part(t, 'b', b);
  const over = (t, a, b) => !!t.cap && ((t.cap.a != null && a > t.cap.a) || (t.cap.b != null && b > t.cap.b));
  const unit = (id) => cm.inputs.find((x) => x.id === id)?.suffix || '';
  const paint = () => {
    const a = val('a'), b = val('b'), costs = T.map((t) => cost(t, a, b)), maxC = Math.max(...costs, 1);
    let best = T.findIndex((t) => !over(t, a, b)); const fits = T.map((t, k) => ({ k, c: costs[k] })).filter((x) => !over(T[x.k], a, b)).sort((x, y) => x.c - y.c); best = fits.length ? fits[0].k : K - 1;
    selNow = manual >= 0 ? manual : best;
    cm.inputs.forEach((x) => { outp[x.id].textContent = inp[x.id].value + (x.suffix || ''); });
    rows.forEach((r, k) => {
      r.setAttribute('aria-checked', String(k === selNow)); r.dataset.over = over(T[k], a, b) ? '1' : '0';
      $(r, '[data-role=cost]').textContent = money(cm.currency, costs[k]); $(r, '[data-role=bar]').style.width = `${(costs[k] / maxC) * 100}%`;
      $(r, '[data-role=note]').textContent = over(T[k], a, b) ? 'over this tier\'s limit at your usage' : (T[k].bullets || []).slice(0, 2).join(' · ');
    });
    const t = T[selNow], terms = [`${money(cm.currency, t.fixed)}`];
    ['a', 'b'].forEach((id) => { const p = part(t, id, val(id)); if (p > 0) terms.push(`(${val(id)} - ${t.included?.[id] ?? 0})${unit(id)} x ${money(cm.currency, t.rates[id])}`); });
    totalEl.textContent = money(cm.currency, costs[selNow]); lineEl.textContent = `${t.name}: ${terms.join(' + ')} = ${money(cm.currency, costs[selNow])}`;
    usage = clamp(cm.inputs.reduce((s, x) => s + (val(x.id) - x.min) / ((x.max - x.min) || 1), 0) / cm.inputs.length);
    subject.setDrive({ stretch: STRETCH.min + STRETCH.span * usage });
  };
  Object.values(inp).forEach((i) => i.addEventListener('input', () => { manual = -1; paint(); }));
  rows.forEach((r, k) => {
    r.onclick = () => { manual = k; paint(); };
    r.onmouseenter = () => subject.setHover(k, K); r.onmouseleave = () => subject.setHover(null); r.onfocus = r.onmouseenter; r.onblur = r.onmouseleave;
  });
  const custom = { fn(time, o) {
    for (let i = 0; i < subject.M; i++) {
      const g = subject.groupOf(i, K), on = hash01(i + 7) < usage ? USAGE_LIT : 0;
      o[i] = g === selNow ? SEL_LIT * (1 - PULSE.amp + PULSE.amp * Math.sin(time * PULSE.rate + i)) : Math.max(on, LIT_BASE);
    }
  } };
  paint();
  return { enter() { subject.setCustom(custom); paint(); }, leave() { subject.setCustom(null); subject.setDrive(null); subject.setHover(null); } };
}
