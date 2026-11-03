// faq: native <details> list on glass. One subject node per answer: opening an answer lights its node (runtime/archetypes/faq.js).
// Padding clears the fixed nav so the heading is never tucked under it.
import { esc, h2, actOpen, mq } from './_shared.mjs';

export const meta = {
  id: 'faq', needsTarget: true, needsCommerce: true, copyRequired: ['title'],
  params: { openFirst: true },
  doc: { copy: 'title, em?', params: 'openFirst (default true); questions come from commerce.faq[]' },
};

export function render(ch, piece) {
  const items = piece.commerce.faq.map((f, k) => `<details class="glass" data-node="${k}"${k === 0 && ch.params.openFirst ? ' open' : ''}><summary>${esc(f.q)}</summary><p>${esc(f.a)}</p></details>`).join('\n    ');
  return `${actOpen(ch, 'act-faq')}
  <div class="copy">
    ${h2(ch)}
    <div class="faq" data-motion="stagger-grid">
    ${items}
    </div>
  </div>
</section>`;
}

export function css(piece) {
  return `
/* faq */
.act-faq { padding-top: calc(var(--nav-h) + 12svh); min-height: 100svh; } .act-faq .copy { max-width: min(680px, 54vw); gap: 28px; } .act-faq h2 { font-size: clamp(44px, 6.6vw, 112px); }
.faq { display: grid; gap: 10px; }
.faq details { border-radius: 20px; padding: 0 22px; }
.faq summary { list-style: none; cursor: pointer; min-height: 60px; display: flex; align-items: center; justify-content: space-between; gap: 20px; font: 400 clamp(16px, 1.4vw, 20px)/1.3 var(--font); }
.faq summary::-webkit-details-marker { display: none; }
.faq summary::after { content: "+"; font-size: 26px; font-weight: 200; color: var(--accent-text); transition: transform .4s var(--ease); }
.faq details[open] summary::after { transform: rotate(45deg); }
.faq details p { color: var(--ink-soft); padding-bottom: 20px; max-width: 60ch; }
${mq(piece, `.act-faq { padding-top: 38svh; min-height: 0; } .act-faq .copy { max-width: none; }`)}`;
}
