// claim: the pointer query as an argument. Headline + deck + group chips (filter the subject) + a live ranked result list.
import { esc, h2, deck, actOpen } from './_shared.mjs';

export const meta = {
  id: 'claim', needsTarget: true, needsCommerce: false, copyRequired: ['title', 'deck'],
  params: { rows: 5 },
  doc: { copy: 'title, em?, deck (chips come from interaction.groups)', params: 'rows (ranked rows shown, default 5)' },
};

export function render(ch, piece) {
  const rows = Array.from({ length: ch.params.rows }, () => '<li><i>-</i><span>-</span><b></b></li>').join('');
  return `${actOpen(ch, 'act-claim')}
  <div class="copy">
    ${h2(ch)}
    ${deck(ch.copy.deck)}
    <div class="chips" data-role="chips" role="group" aria-label="Filter"></div>
    <div class="results glass card" aria-live="polite">
      <ol class="rows mono" data-role="list">${rows}</ol>
      <p class="r-foot mono" data-role="count"></p>
    </div>
  </div>
</section>`;
}

export const css = () => `
/* claim */
.results { min-width: min(100%, 380px); }
`;
