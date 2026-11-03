import { indexHtml } from '../../scripts/lib/html.mjs';
import { ARCHETYPES } from '../../archetypes/index.mjs';
import { esc } from '../../archetypes/_shared.mjs';
import { ambient, renderPanels } from './panels.mjs';
export { css } from './css.mjs';
export const runtime = 'boot.js';

export function html(piece, env) {
  const first = piece.rail.panels[0];
  const panels = renderPanels(piece);
  const commerce = piece.chapters.map((ch) => ARCHETYPES[ch.archetype].render(ch, piece, env).replace('class="act ', 'class="act rail-commerce ')).join('\n');
  const body = `<section class="rail" id="rail" aria-label="${esc(piece.name)} studies"><div class="rail-viewport">
  ${ambient(piece.rail.params.ambientLines)}<div class="rail-track">${panels}</div>
  <div class="rail-progress mono" aria-hidden="true"><span data-panel-count>01</span><div class="rail-progress-rule"><i></i></div><span>${String(piece.rail.panels.length).padStart(2, '0')} studies</span></div>
  </div></section>\n${commerce}
  <footer class="rail-end" id="rail-end"><p class="mono">${esc(piece.concept.notice)}</p><a class="link" href="#${first.id}">Back to first study ↑</a></footer>`;
  return indexHtml(piece, { ...env, body, hero: { ...first, copy: {} }, navigation: [...piece.rail.panels, ...piece.chapters] });
}
