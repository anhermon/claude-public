import { indexHtml } from '../../scripts/lib/html.mjs';
import { esc } from '../../archetypes/_shared.mjs';
export { css } from './css.mjs';
export const runtime = 'boot.js';
const DIGITS = 2, WORD_OFFSET = 1;
const ordinal = (i) => String(i + 1).padStart(DIGITS, '0');
const PLATE = `<svg viewBox="0 0 640 400" role="img" aria-label="Cut paper study: a sun, folded ribbon and ink grid"><path fill="currentColor" d="M20 340 190 60 340 340Z"/><circle cx="460" cy="160" r="130" fill="none" stroke="currentColor" stroke-width="28"/><path d="m160 360 160-290 160 290 140-240" fill="none" stroke="currentColor" stroke-width="8"/><path d="M20 380H620M20 350H620M20 320H620" stroke="currentColor" stroke-width="2"/></svg>`;

export function html(piece, env) {
  const C = piece.collage;
  const body = piece.chapters.map((ch, i) => {
    const tag = i ? 'h2' : 'h1';
    const words = C.words.map((_, k) => C.words[(k + i * WORD_OFFSET) % C.words.length]);
    const blocks = C.blocks.map((b, k) => `<button class="collage-block" type="button" aria-expanded="false" style="--cutout:${C.palette[b.color]};--block-order:${k}"><span>${esc(b.label)}</span><span class="collage-caption">${esc(b.caption)}</span></button>`).join('');
    return `<section class="collage-chapter" id="${ch.id}" data-collage="${i}" style="--paper:${C.palette[i % C.palette.length]}" aria-labelledby="h-${ch.id}">
      <div class="collage-meta mono"><span>${esc(piece.name.toUpperCase())} / EDITION ${ordinal(i)}</span><span>TYPE / FORM / PLAY</span></div>
      <${tag} class="collage-title" id="h-${ch.id}">${esc(ch.copy.title)}</${tag}>
      <div class="collage-words" data-wow aria-label="${esc(words.join(' '))}">${words.map((w, k) => `<span class="collage-word" data-word="${k}" aria-hidden="true" style="--letters:${Math.max(w.length, C.words.length)}">${esc(w)}</span>`).join('')}</div>
      <div class="collage-bottom"><p class="collage-deck">${esc(ch.copy.deck)}</p><figure class="collage-plate">${PLATE}<figcaption class="mono">${ordinal(i)} / A photograph-free paper study</figcaption></figure><div class="collage-cutouts">${blocks}</div></div>
      <div class="collage-marquee mono"><span>${esc(C.marquee || C.words.join(' / '))} / ${esc(C.marquee || C.words.join(' / '))} / </span></div>
    </section>`;
  }).join('\n') + `<footer class="collage-end mono"><p>${esc(piece.concept.notice)}</p><a href="#${piece.chapters[0].id}">Back to the first impression ↑</a></footer>`;
  return indexHtml(piece, { ...env, body, hero:piece.chapters[0] }).replace('<body class="finish">', '<body class="finish collage-page">');
}
