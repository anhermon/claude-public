// pricing: a calculator matrix, not a card row. Every tier is priced live at the visitor's usage (the arithmetic is printed),
// the cheapest tier that fits is highlighted, and the sliders DRIVE the subject (lit fraction = usage, tower height = cost,
// hovered tier lifts its group). Prices come from spec.commerce; nothing is hard-coded here.
import { esc, h2, deck, actOpen, mq } from './_shared.mjs';

export const meta = {
  id: 'pricing', needsTarget: true, needsCommerce: true, copyRequired: ['title'],
  params: {},
  doc: { copy: 'title, em?, deck?, fine?', params: '(data: commerce.inputs[], commerce.tiers[] {name, fixed, included{a,b}, rates{a,b}, cap{a,b}?, bullets[]})' },
};

export function render(ch, piece) {
  const cm = piece.commerce, c = ch.copy;
  const rows = cm.tiers.map((t, k) => `<button type="button" class="trow" role="radio" aria-checked="false" data-tier="${k}">
      <span class="tname">${esc(t.name)}</span><span class="tcost" data-role="cost">${esc(cm.currency)}0</span>
      <span class="tbar" aria-hidden="true"><i data-role="bar"></i></span>
      <span class="tnote mono" data-role="note">${esc((t.bullets || []).slice(0, 2).join(' · '))}</span></button>`).join('');
  const sliders = cm.inputs.map((x) => `<label class="slider"><span>${esc(x.label)}</span><input data-role="in-${x.id}" type="range" min="${x.min}" max="${x.max}" step="${x.step || 1}" value="${x.value}" aria-label="${esc(x.label)}"><output class="mono" data-role="out-${x.id}">${x.value}${esc(x.suffix || '')}</output></label>`).join('');
  return `${actOpen(ch, 'act-pricing')}
  <div class="copy">
    ${h2(ch)}
    ${deck(c.deck)}
    <div class="matrix glass card" role="radiogroup" aria-label="Tiers priced at your usage" data-motion="stagger-grid" data-tell-ok>${rows}</div>
    <div class="calc-ctl">${sliders}</div>
    <div class="calc-out"><b data-role="total">${esc(cm.currency)}0</b><span class="unit">a month, sample prices</span><span class="mono line" data-role="line"></span></div>
    ${c.fine ? `<p class="fine mono">${esc(c.fine)}</p>` : ''}
  </div>
</section>`;
}

export function css(piece) {
  return `
/* pricing: matrix left, subject right (desktop); mobile puts sliders + total first (visible with the subject), then the matrix */
.act-pricing .copy { max-width: min(640px, 54vw); gap: 20px; } .act-pricing h2 { font-size: clamp(44px, 6.6vw, 112px); }
.matrix { display: grid; gap: 0; padding: 6px; }
.trow { display: grid; grid-template-columns: 1fr auto; grid-template-areas: "name cost" "bar bar" "note note"; gap: 6px 16px; text-align: left; color: var(--ink); background: transparent; border: 0; border-bottom: 1px solid var(--hair); padding: 14px 14px 12px; min-height: 64px; cursor: pointer; font: inherit; transition: background-color .35s, outline-color .35s; border-radius: 14px; }
.trow:last-child { border-bottom: 0; }
.tname { grid-area: name; font: 500 16px/1.2 var(--font); } .tcost { grid-area: cost; font: var(--display-weight) clamp(26px, 2.8vw, 40px)/1 var(--font-display); font-stretch: var(--display-stretch); font-variant-numeric: tabular-nums; letter-spacing: -0.02em; }
.tbar { grid-area: bar; height: 3px; background: var(--hair); border-radius: 2px; overflow: hidden; } .tbar i { display: block; height: 100%; width: 0; background: var(--accent); transition: width .5s var(--ease); }
.tnote { grid-area: note; font-size: 12px; color: var(--ink-soft); }
.trow:hover, .trow[aria-checked="true"] { background: color-mix(in srgb, var(--accent) 12%, transparent); }
.trow[aria-checked="true"] .tname::after { content: " / best fit"; color: var(--accent-text); font: 400 12px/1 var(--mono); }
.trow[data-over="1"] { opacity: .5; }
.calc-ctl { display: grid; gap: 4px; } .calc-out { display: grid; gap: 6px; }
.calc-out b { font: 200 clamp(56px, 7vw, 120px)/0.95 var(--font-display); font-stretch: 125%; letter-spacing: -0.045em; font-variant-numeric: tabular-nums; }
.calc-out .line { font-size: 12px; color: var(--ink-soft); line-height: 1.5; } .unit { font-size: 14px; color: var(--ink-soft); }
${mq(piece, `.act-pricing .copy { max-width: none; } .act-pricing { min-height: 0; padding-top: 38svh; } .matrix { background: var(--glass-bg); }
.act-pricing .calc-ctl { order: 1; } .act-pricing .calc-out { order: 2; } .act-pricing .matrix { order: 3; } .act-pricing .fine { order: 4; }
.act-pricing h2 { font-size: clamp(38px, 11vw, 56px); } .calc-out b { font-size: clamp(44px, 13vw, 64px); }`)}`;
}
