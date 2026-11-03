// hero: headline + deck + CTAs, a live pointer-query readout, and the giant wordmark that the subject refracts (drawn in GL;
// a DOM copy shows only while GL is off). The readout sits top-right on desktop and below the CTAs on mobile: never in the wordmark band.
import { esc, lines, mq } from './_shared.mjs';

const HERO_H1_VH = 10.5;   // headline height cap so copy + CTAs always clear the reserved wordmark band

export const meta = {
  id: 'hero', needsTarget: true, needsCommerce: false, copyRequired: ['title', 'deck'],
  params: { readoutRows: 3, wordmarkBandVh: 30 },
  doc: { copy: 'title, em?, deck, ctas[{label, href, kind: primary|link}]', params: 'readoutRows (default 3), wordmarkBandVh (height reserved for the wordmark, default 30)' },
};

export function render(ch, piece) {
  const c = ch.copy, I = piece.interaction;
  const ctas = (c.ctas || []).map((b) => (b.kind === 'link' ? `<a class="link" href="${esc(b.href)}">${esc(b.label)}</a>` : `<a class="btn" href="${esc(b.href)}">${esc(b.label)}</a>`)).join('');
  const rows = Array.from({ length: ch.params.readoutRows }, (_, i) => `<li><i>${i + 1}</i><span>-</span><b>-</b></li>`).join('');
  return `<section class="hero" id="${ch.id}" data-act="${ch.act}" data-archetype="hero" aria-label="${esc(piece.name)}">
  <div class="hero-copy">
    <h1 data-motion="blur-line" data-motion-when="entrance">${lines(c.title)}${c.em ? `<br><em>${esc(c.em)}</em>` : ''}</h1>
    <p class="deck" data-motion="word-blur" data-motion-when="entrance" data-motion-delay="0.35">${esc(c.deck)}</p>
    ${ctas ? `<div class="cta-row" data-motion="stagger-grid" data-motion-when="entrance" data-motion-delay="0.6">${ctas}</div>` : ''}
  </div>
  <aside class="readout glass" data-role="readout" aria-label="Live query readout">
    <p class="r-title">${esc(I.title)}</p>
    <ol class="rows mono" data-role="hits">${rows}</ol>
    <p class="r-foot mono"><span data-role="n">${piece.subject.items}</span> ${esc(I.scanLabel)} <b data-role="ms">-- ms</b>, on your device.${I.footnote ? ' ' + esc(I.footnote) : ''}</p>
  </aside>
  <div class="hero-word" data-fit aria-hidden="true"><span>${esc(piece.wordmark)}</span></div>
</section>`;
}

export function css(piece, ch) {
  const band = ch.params.wordmarkBandVh;
  return `
/* hero */
.hero { min-height: 100svh; display: block; padding-top: calc(var(--nav-h) + 24px); padding-bottom: ${band}svh; }
.hero-copy { display: grid; gap: 20px; max-width: min(620px, 50vw); margin-top: clamp(8px, 3svh, 40px); }
.hero h1 { font-size: clamp(46px, min(8vw, ${HERO_H1_VH}svh), 128px); }
.cta-row { display: flex; gap: 26px; align-items: center; flex-wrap: wrap; }
.readout { position: absolute; right: var(--pad); top: calc(var(--nav-h) + 40px); width: 280px; padding: 16px 18px; border-radius: 20px; z-index: 2; }
.hero-word { position: absolute; left: 0; right: 0; bottom: 0; height: ${band}svh; display: grid; align-items: center; justify-items: center; overflow: hidden; font: 800 clamp(80px, 17vw, 330px)/0.8 var(--font-display); font-stretch: 125%; letter-spacing: -0.04em; white-space: nowrap;
  color: transparent; background: linear-gradient(180deg, color-mix(in srgb, var(--ink) 38%, transparent), color-mix(in srgb, var(--ink) 6%, transparent)); -webkit-background-clip: text; background-clip: text; transition: opacity .8s var(--ease); user-select: none; }
html[data-gl="live"] .hero-word { opacity: 0; } .hero-word span { display: inline-block; }
${mq(piece, `.hero { min-height: 100svh; padding-bottom: 28px; }
.hero h1 { font-size: clamp(46px, 14vw, 72px); }
.hero-copy { max-width: none; margin-top: 0; padding-top: 38svh; gap: 16px; }
.readout { position: static; width: auto; margin-top: 18px; }
.hero-word { top: calc(var(--nav-h) + 4svh); bottom: auto; height: 22svh; font-size: 21vw; }`)}`;
}
