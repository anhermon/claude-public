import * as original from '../../archetypes/hero.mjs';
import { esc, lines, mq } from '../../archetypes/_shared.mjs';

const POSTER = { size: 600, center: 300, radius: 210, inner: 142, lines: 12, step: 15, inset: 100 };
function poster() {
  const lines = Array.from({ length: POSTER.lines }, (_, i) => `<ellipse cx="${POSTER.center}" cy="${POSTER.inset + i * POSTER.step * 2}" rx="${POSTER.radius}" ry="${POSTER.inner / POSTER.lines}"/>`).join('');
  return `<svg class="hero-poster" viewBox="0 0 ${POSTER.size} ${POSTER.size}" aria-hidden="true"><circle cx="${POSTER.center}" cy="${POSTER.center}" r="${POSTER.radius}"/>${lines}</svg>`;
}

export const meta = original.meta;
export function render(ch, piece) {
  if (!piece.hero) return original.render(ch, piece);
  const c = ch.copy, I = piece.interaction, H = piece.hero;
  const ctas = (c.ctas || []).map((b) => `<a class="${b.kind === 'link' ? 'link' : 'btn'}" href="${esc(b.href)}">${esc(b.label)}</a>`).join('');
  const rows = Array.from({ length: ch.params.readoutRows }, (_, i) => `<li><i>${i + 1}</i><span>-</span><b>-</b></li>`).join('');
  const readout = piece.readout === 'none' ? '' : `<aside class="readout ${piece.readout === 'card' ? 'glass' : 'readout-inline'}" aria-label="Live query readout">
    <p class="r-title">${esc(I.title)}</p><ol class="rows mono" data-role="hits">${rows}</ol>
    <p class="r-foot mono"><span data-role="n">${piece.subject.items}</span> ${esc(I.scanLabel)} <b data-role="ms">-- ms</b></p>
  </aside>`;
  return `<section class="hero hero-variant" id="${ch.id}" data-act="${ch.act}" data-archetype="hero" data-layout="${H.layout}" data-wordmark="${H.wordmark}" aria-label="${esc(piece.name)}">
  <div class="hero-copy"><h1 data-motion="blur-line" data-motion-when="entrance">${lines(c.title)}${c.em ? `<br><em>${esc(c.em)}</em>` : ''}</h1>
    <p class="deck">${esc(c.deck)}</p>${ctas ? `<div class="cta-row">${ctas}</div>` : ''}${piece.readout === 'inline' ? readout : ''}
  </div>${piece.readout === 'card' ? readout : ''}
  ${poster()}
  ${H.wordmark ? `<div class="hero-word" data-fit aria-hidden="true"><span>${esc(piece.wordmark)}</span></div>` : ''}
</section>`;
}

export function css(piece, ch) {
  if (!piece.hero) return original.css(piece, ch);
  return original.css(piece, ch) + `
/* Hero compositions reserve a copy zone and a separate subject zone. */
.hero-variant[data-wordmark="false"] { padding-bottom: 6svh; }
.hero-poster { position: absolute; top: 22svh; right: 0; width: 50vw; height: 65svh; fill: none; stroke: var(--accent); stroke-width: 1; opacity: .45; pointer-events: none; }
html[data-gl="live"] .hero-poster { display: none; }
.hero[data-layout="stack"] .hero-poster { top: auto; right: 30%; bottom: 4svh; width: 40%; height: 38svh; }
.hero[data-layout="type-only"] .hero-poster { top: auto; bottom: 4svh; width: 25%; height: 24svh; }
.hero-variant .readout-inline { position: static; width: min(100%, 420px); padding: 12px 0; border-top: 1px solid var(--hair); border-radius: 0; }
.readout-inline .rows li:not(:first-child), .readout-inline .r-foot { display: none; }
.readout-inline .r-title { font-size: 12px; }
.hero[data-layout="stack"] { min-height: 110svh; padding-bottom: 42svh; }
.hero[data-layout="stack"] .hero-copy { max-width: min(840px, 80vw); margin: 2svh auto 0; text-align: center; justify-items: center; gap: 16px; }
.hero[data-layout="stack"] h1 { font-size: clamp(44px, min(7vw, 9svh), 104px); }
.hero[data-layout="stack"] .cta-row { justify-content: center; }
.hero[data-layout="stack"] > .readout { top: auto; bottom: 8svh; right: var(--pad); width: min(260px, 22vw); }
.hero[data-layout="bleed"] .hero-copy { max-width: min(580px, 39vw); margin-top: 9svh; }
.hero[data-layout="bleed"] > .readout { top: auto; bottom: 7svh; left: var(--pad); right: auto; }
.hero[data-layout="type-only"] { min-height: 100svh; padding-bottom: 22svh; }
.hero[data-layout="type-only"] .hero-copy { max-width: 88vw; margin-top: 2svh; }
.hero[data-layout="type-only"] h1 { max-width: 10ch; font-size: clamp(66px, min(13vw, 17svh), 208px); line-height: .94; }
.hero-variant[data-wordmark="true"][data-layout="stack"] .hero-word { height: 18svh; }
body[data-scroll="static"] .act .copy { max-width: 40vw; }
body[data-scroll="static"] .act[data-side="left"] { justify-content: flex-start; text-align: left; }
body[data-scroll="static"] .act[data-side="right"] { justify-content: flex-end; text-align: left; }
body[data-scroll="static"] .act-stat .stat-head, body[data-scroll="static"] .act-stat .stat-ctl { max-width: 40vw; margin-inline: 0; }
body[data-scroll="static"] .act-stat .numerals.wide { grid-template-columns: repeat(2, 1fr); }
body[data-scroll="static"][data-hero-layout="stack"] .act { align-items: flex-start; padding-bottom: 42svh; }
${mq(piece, `.hero-variant { padding-top: calc(var(--nav-h) + 24px); }
.hero-variant .hero-copy { max-width: none; }
.hero[data-layout="stack"] { min-height: 108svh; padding-bottom: 38svh; }
.hero[data-layout="stack"] .hero-copy { max-width: none; padding-top: 0; margin-top: 0; }
.hero[data-layout="stack"] h1 { font-size: clamp(40px, 11vw, 66px); }
.hero[data-layout="stack"] > .readout { position: static; width: auto; margin: 20px auto 0; }
.hero[data-layout="bleed"] .hero-copy { max-width: none; margin-top: 0; padding-top: 38svh; }
.hero[data-layout="bleed"] > .readout { position: static; width: auto; }
.hero[data-layout="type-only"] .hero-copy { padding-top: 0; margin-top: 4svh; }
.hero[data-layout="type-only"] h1 { font-size: clamp(60px, 17vw, 100px); }
.hero[data-layout="type-only"] { padding-bottom: 34svh; }
.hero-variant .readout-inline { margin-top: 0; }
.hero-poster { top: calc(var(--nav-h) + 3svh); right: 10%; width: 80%; height: 32svh; }
.hero[data-layout="stack"] .hero-poster { right: 10%; width: 80%; height: 32svh; bottom: 3svh; }
.hero[data-layout="type-only"] .hero-poster { right: 5%; width: 50%; height: 26svh; }
body[data-scroll="static"] .act .copy, body[data-scroll="static"] .act-stat .stat-head, body[data-scroll="static"] .act-stat .stat-ctl { max-width: none; }
body[data-scroll="static"][data-hero-layout="stack"] .act { align-items: flex-end; padding-bottom: 7svh; }
.hero-variant[data-wordmark="false"] .hero-copy { min-width: 0; }`)}
`;
}
