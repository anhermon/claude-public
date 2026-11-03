// footer: closing CTA card (procedural gradient plate or a generated file if present), giant wordmark, concept line.
import { esc, mq } from './_shared.mjs';
import { plateSvg } from './band.mjs';

export const meta = {
  id: 'footer', needsTarget: false, needsCommerce: true, copyRequired: [],
  params: { slot: 'cta', lineCount: 12 },
  doc: { copy: '(none; the CTA comes from commerce.cta and the notice from concept.notice)', params: 'slot (default cta), lineCount (procedural contours)' },
};

export function render(ch, piece, env) {
  const cta = piece.commerce.cta, a = env.assetFor(ch.params.slot);
  const art = a ? `<img class="plate" src="${esc(a.file)}" alt="${esc(a.alt || '')}" loading="lazy">` : plateSvg(piece.subject.seed + 11, ch.params.lineCount);
  return `<footer class="foot" id="${ch.id}" data-act="${ch.act}" data-archetype="footer">
  <div class="cta-card">
    ${art}
    <div class="cta-copy"><h2>${esc(cta.title)}</h2>${cta.body ? `<p>${esc(cta.body)}</p>` : ''}<a class="btn" href="${esc(cta.href || '#top')}">${esc(cta.label)}</a></div>
  </div>
  <div class="foot-word" data-fit aria-hidden="true"><span>${esc(piece.wordmark)}</span></div>
  <p class="fine mono foot-line">${esc(piece.concept.notice)}. Built with the premium-web factory.</p>
</footer>`;
}

export function css(piece) {
  return `
/* footer */
.foot { position: relative; padding: 8svh var(--pad) 0; overflow: hidden; }
.cta-card { position: relative; border-radius: 28px; overflow: hidden; min-height: min(70svh, 600px); display: grid; align-items: center; background: #0a1a1f; color: #f2f7f6; }
.cta-card .plate { position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; }
.cta-copy { position: relative; display: grid; gap: 18px; padding: clamp(24px, 5vw, 72px); max-width: min(620px, 100%); }
.cta-copy h2 { font-size: clamp(34px, 4.6vw, 76px); } .cta-copy p { color: rgba(242, 247, 246, .78); max-width: 36ch; }
.cta-copy .btn { justify-self: start; background: #f2f7f6; color: #04100f; }
.foot-word { font: 800 clamp(90px, 21vw, 400px)/0.8 var(--font-display); font-stretch: 125%; letter-spacing: -0.05em; text-align: center; margin: 6svh 0 -1vw; white-space: nowrap; background: linear-gradient(180deg, color-mix(in srgb, var(--ink) 42%, transparent), color-mix(in srgb, var(--ink) 4%, transparent) 80%); -webkit-background-clip: text; background-clip: text; color: transparent; user-select: none; }
.foot-word span { display: inline-block; }
.foot-line { position: relative; z-index: 2; padding: 18px 0 22px; margin-top: 3vw; text-align: center; }
${mq(piece, `.cta-card { min-height: 460px; align-items: end; } .foot-word { margin-bottom: 0; font-size: 19vw; }`)}`;
}
