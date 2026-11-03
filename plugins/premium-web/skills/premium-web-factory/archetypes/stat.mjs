// stat: scale / fan-out. One giant number, a stepper (shard / region / replica count) that fans the subject out, and four
// numerals from a labelled sample model (modes: divide | log | linear | inverse).
import { esc, deck, actOpen, mq } from './_shared.mjs';

const STAT_BAND_VH = 40;   // bottom band kept free for the subject

export const meta = {
  id: 'stat', needsTarget: true, needsCommerce: false, copyRequired: ['title', 'giant', 'steps'],
  params: {},
  doc: { copy: 'title (visually hidden h2), giant, deck?, steps[ints], stepLabel?, numerals[{label, mode, base?, per?, total?, decimals?, suffix?}], fine?', params: '(none)' },
};

export function render(ch) {
  const c = ch.copy;
  const n = (c.numerals || []).map((x, k) => `<div><dd data-role="num" data-k="${k}">0</dd><dt>${esc(x.label)}</dt></div>`).join('');
  return `${actOpen(ch, 'act-stat')}
  <div class="stat-head">
    <h2 id="h-${ch.id}" class="vh">${esc(c.title)}</h2>
    <p class="giant-num" aria-hidden="true" data-motion="blur-line">${esc(c.giant)}</p>
    ${deck(c.deck, 'center')}
  </div>
  <div class="stat-ctl">
    <div class="chips" data-role="steps" role="radiogroup" aria-label="${esc(c.stepLabel || 'Steps')}"></div>
    <dl class="numerals wide">${n}</dl>
    ${c.fine ? `<p class="fine mono center">${esc(c.fine)}</p>` : ''}
  </div>
</section>`;
}

export function css(piece) {
  return `
/* stat: head + controls stacked in the top ~60svh; the subject fans out in the reserved bottom band, so nothing overlaps it */
.act-stat { flex-direction: column; justify-content: flex-start; align-items: stretch; text-align: center; padding-top: calc(var(--nav-h) + 3svh); padding-bottom: ${STAT_BAND_VH}svh; gap: 3svh; min-height: 110svh; }
.giant-num { font: 200 clamp(90px, min(16vw, 22svh), 280px)/0.9 var(--font-display); font-stretch: 125%; letter-spacing: -0.05em; color: var(--ink); }
.stat-head { display: grid; gap: 14px; justify-items: center; }
.stat-ctl { display: grid; gap: 24px; width: 100%; max-width: 1040px; margin-inline: auto; }
.stat-ctl .chips { justify-content: center; }
${mq(piece, `.act-stat { justify-content: flex-start; padding-top: 38svh; padding-bottom: 7svh; min-height: 100svh; gap: 20px; text-align: left; }
.act-stat .stat-head { justify-items: start; } .giant-num { font-size: clamp(88px, 27vw, 150px); } .stat-ctl .chips { justify-content: flex-start; } .act-stat .center { margin-inline: 0; text-align: left; }`)}`;
}
