// explainer: a mechanism with labelled layers. Each layer button lights its group in the subject; a slider drives three live numerals.
import { esc, h2, deck, actOpen } from './_shared.mjs';

export const meta = {
  id: 'explainer', needsTarget: true, needsCommerce: false, copyRequired: ['title', 'deck', 'layers'],
  params: {},
  doc: { copy: 'title, em?, deck, layers[{label, detail}], slider?{label,min,max,value,suffix}, numerals?[{label, base, span, curve: lin|sat|exp, decimals, suffix}], fine?', params: '(none)' },
};

export function render(ch) {
  const c = ch.copy;
  const layers = c.layers.map((l, k) => `<li><button type="button" class="layer" data-layer="${k}" aria-pressed="false"><i class="mono">${String(k + 1).padStart(2, '0')}</i><b>${esc(l.label)}</b><span>${esc(l.detail || '')}</span></button></li>`).join('');
  const s = c.slider ? `<label class="slider"><span>${esc(c.slider.label)}</span><input data-role="slider" type="range" min="${c.slider.min}" max="${c.slider.max}" value="${c.slider.value}" aria-label="${esc(c.slider.label)}"><output class="mono" data-role="slider-out">${c.slider.value}</output></label>` : '';
  const n = (c.numerals || []).map((x, k) => `<div><dd data-role="num" data-k="${k}">0</dd><dt>${esc(x.label)}</dt></div>`).join('');
  return `${actOpen(ch, 'act-explainer')}
  <div class="copy">
    ${h2(ch)}
    ${deck(c.deck)}
    <ol class="layers" data-role="layers">${layers}</ol>
    ${s}
    ${n ? `<dl class="numerals">${n}</dl>` : ''}
    ${c.fine ? `<p class="fine mono">${esc(c.fine)}</p>` : ''}
  </div>
</section>`;
}

export const css = () => `
/* explainer */
.layers { list-style: none; padding: 0; margin: 0; display: grid; gap: 6px; }
.layer { width: 100%; display: grid; grid-template-columns: 34px auto 1fr; gap: 12px; align-items: baseline; text-align: left; background: transparent; color: var(--ink); border: 0; border-top: 1px solid var(--hair); padding: 12px 2px; min-height: 48px; cursor: pointer; font: 400 15px/1.3 var(--font); transition: background-color .3s, border-color .3s; }
.layer i { font-style: normal; color: var(--accent-text); font-size: 12px; } .layer b { font-weight: 500; } .layer span { color: var(--ink-soft); font-size: 13px; }
.layer:hover, .layer[aria-pressed="true"] { border-top-color: var(--accent); background: color-mix(in srgb, var(--accent) 10%, transparent); }
`;
