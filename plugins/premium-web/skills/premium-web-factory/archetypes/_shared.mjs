// Shared helpers + component CSS used by every archetype. Pure functions: no I/O.
export const esc = (s) => String(s ?? '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
export const lines = (s) => esc(s).split('\n').join('<br>');
export const mq = (piece, css) => `@media (max-width: ${piece.mobileMaxW}px) {\n${css}\n}`;

/** h2 with an accent tail: copy.title + copy.em */
export const h2 = (ch, extra = '') => `<h2 id="h-${ch.id}" data-motion="blur-line"${extra}>${lines(ch.copy.title)}${ch.copy.em ? ` <em>${esc(ch.copy.em)}</em>` : ''}</h2>`;
export const deck = (text, cls = '') => (text ? `<p class="deck${cls ? ' ' + cls : ''}" data-motion="word-blur">${esc(text)}</p>` : '');

/** Opening tag of an act section. Every archetype section carries data-act (subject state) and data-side (where the copy sits). */
export const actOpen = (ch, cls = '', extra = '') =>
  `<section class="act ${cls}" id="${ch.id}" data-act="${ch.act}" data-side="${ch.textSide}" data-archetype="${ch.archetype}" aria-labelledby="h-${ch.id}"${extra}>`;

export const SHARED_CSS = (piece) => `
/* ---- shared layout: copy sits opposite the subject (data-side), act height gives the morph room ---- */
.act, .hero { position: relative; padding: 0 var(--pad); }
.act { min-height: 115svh; display: flex; align-items: center; padding-top: calc(var(--nav-h) + 6svh); padding-bottom: 12svh; scroll-margin-top: 0; }
.act[data-side="left"] { justify-content: flex-start; } .act[data-side="right"] { justify-content: flex-end; } .act[data-side="center"] { justify-content: center; text-align: center; }
.act .copy { display: grid; gap: 24px; max-width: min(560px, 46vw); }
.act[data-side="center"] .copy { max-width: min(860px, 100%); justify-items: center; }
.fine { font-size: 12px; color: var(--ink-soft); line-height: 1.5; }
.center { text-align: center; margin-inline: auto; }
.r-foot { font-size: 12px; color: var(--ink-soft); margin-top: 12px; line-height: 1.45; } .r-foot b { color: var(--ink); font-weight: 400; }
.r-title { font-size: 13px; color: var(--ink-soft); margin-bottom: 10px; }
.rows { list-style: none; padding: 0; display: grid; gap: 7px; font-size: 13px; }
.rows li { display: grid; grid-template-columns: 18px 1fr auto; gap: 10px; align-items: baseline; }
.rows i { font-style: normal; color: var(--accent-text); } .rows b { font-weight: 400; color: var(--ink); }
.card { border-radius: 20px; padding: 16px 18px; }
.chips { display: flex; flex-wrap: wrap; gap: 8px; }
.chip { font: 400 13px/1 var(--font); color: var(--ink); background: transparent; border: 1px solid var(--hair); border-radius: 999px; min-height: 40px; padding: 0 16px; cursor: pointer; transition: background-color .3s, border-color .3s; }
.chip[aria-pressed="true"], .chip[aria-checked="true"] { background: color-mix(in srgb, var(--accent) 22%, transparent); border-color: var(--accent); }
.slider { display: grid; grid-template-columns: auto 1fr auto; gap: 14px; align-items: center; font-size: 14px; color: var(--ink-soft); }
.slider output { color: var(--ink); min-width: 5ch; text-align: right; font-size: 13px; }
input[type="range"] { -webkit-appearance: none; appearance: none; width: 100%; height: 28px; background: transparent; cursor: pointer; }
input[type="range"]::-webkit-slider-runnable-track { height: 2px; background: var(--hair); border-radius: 2px; }
input[type="range"]::-webkit-slider-thumb { -webkit-appearance: none; width: 22px; height: 22px; margin-top: -10px; border-radius: 50%; background: var(--accent); border: 4px solid var(--ground); box-shadow: 0 0 0 1px var(--accent), 0 0 18px color-mix(in srgb, var(--accent) 60%, transparent); }
input[type="range"]::-moz-range-track { height: 2px; background: var(--hair); }
input[type="range"]::-moz-range-thumb { width: 14px; height: 14px; border-radius: 50%; background: var(--accent); border: 4px solid var(--ground); }
.numerals { display: grid; grid-template-columns: repeat(3, auto); gap: 24px 40px; justify-content: start; padding-top: 6px; margin: 0; }
.numerals.wide { grid-template-columns: repeat(4, 1fr); justify-content: stretch; text-align: center; }
.numerals dd { font: var(--display-weight) clamp(32px, 4vw, 62px)/1 var(--font-display); font-stretch: var(--display-stretch); letter-spacing: -0.03em; font-variant-numeric: tabular-nums; margin: 0; }
.numerals dt { font-size: 13px; color: var(--ink-soft); margin-top: 8px; }
${mq(piece, `.act { min-height: 100svh; align-items: flex-end; padding-top: 38svh; padding-bottom: 7svh; }
.act[data-side] { justify-content: flex-start; } .act[data-side="center"] { text-align: left; justify-content: flex-start; }
.act .copy, .act[data-side="center"] .copy { max-width: none; justify-items: stretch; }
.numerals { grid-template-columns: repeat(3, auto); gap: 16px 22px; } .numerals.wide { grid-template-columns: repeat(2, 1fr); }`)}
`;
