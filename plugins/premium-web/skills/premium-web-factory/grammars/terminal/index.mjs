import { indexHtml } from '../../scripts/lib/html.mjs';
import { ARCHETYPES } from '../../archetypes/index.mjs';
import { esc } from '../../archetypes/_shared.mjs';
import { graphic } from '../rail/panels.mjs';
export { css } from './css.mjs';
export const runtime = 'boot.js';
const DIGITS = 2;
const ordinal = (i) => String(i + 1).padStart(DIGITS, '0');

export function html(piece, env) {
  const T = piece.terminal, first = T.session[0];
  const session = T.session.map((s, i) => {
    const heading = i ? 'h2' : 'h1';
    return `<section class="terminal-chapter" id="${s.id}" data-session="${i}" aria-labelledby="h-${s.id}">
      <div class="terminal-window" data-wow>
        <div class="terminal-chrome mono"><span aria-hidden="true">● ● ●</span><span>${esc(piece.name)} / field console</span><span>${ordinal(i)} / ${ordinal(T.session.length - 1)}</span></div>
        <div class="terminal-heading"><p class="mono terminal-kicker">FIELD NOTES / ${ordinal(i)} / SIMULATED SESSION</p><${heading} id="h-${s.id}">${esc(s.title)}</${heading}></div>
        <div class="terminal-panes"><div class="terminal-log mono"><p class="terminal-command"><span class="terminal-prompt">${esc(T.prompt)}</span> <span data-command>${esc(s.cmd)}</span><span class="terminal-caret" aria-hidden="true">▌</span></p><pre data-output>${esc(s.output.join('\n'))}</pre></div>
          <figure class="terminal-diagram">${graphic(s.pane)}<figcaption class="mono">${esc(s.pane.label)}</figcaption></figure></div>
        <div class="terminal-status mono"><span>LOCAL / SAMPLE DATA</span><span data-session-state>COMPLETE</span><time data-clock aria-label="Current local time">--:--:--</time></div>
      </div>
      <p class="terminal-margin mono">${esc(piece.name.toUpperCase())} / ${ordinal(i)}<span>SCROLL TO ADVANCE ↓</span></p>
    </section>`;
  }).join('\n');
  const commerce = piece.chapters.map((ch) => ARCHETYPES[ch.archetype].render(ch, piece, env)).join('\n');
  const body = session + commerce + `<footer class="terminal-end mono"><span>${esc(piece.concept.notice)}</span><a href="#${first.id}">Replay from the beginning ↑</a></footer>`;
  return indexHtml(piece, { ...env, body, hero: { ...first, copy: {} }, navigation: T.session }).replace('<body class="finish">', '<body class="finish terminal-page">');
}
