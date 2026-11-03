// ship: code-in-three-lines with language tabs and a sample response. Highlighting is done here, once, as plain spans.
import { esc, h2, deck, actOpen } from './_shared.mjs';

export const meta = {
  id: 'ship', needsTarget: true, needsCommerce: false, copyRequired: ['title', 'tabs'],
  params: {},
  doc: { copy: 'title, em?, deck?, tabs[{id,label,code}], response?[{name,score}]', params: '(none)' },
};

const KEYWORDS = 'from|import|const|let|await|new|def|return|curl|async|function';
const TOKEN = new RegExp(`("[^"\\n]*"|'[^'\\n]*'|\\b(?:${KEYWORDS})\\b)`, 'g');
export function highlight(code) {
  return code.split(TOKEN).map((part, i) => (i % 2 === 0 ? esc(part) : /^["']/.test(part) ? `<span class="s">${esc(part)}</span>` : `<span class="k">${esc(part)}</span>`)).join('');
}

export function render(ch) {
  const c = ch.copy;
  const tabs = c.tabs.map((t, k) => `<button role="tab" type="button" id="tab-${ch.id}-${t.id}" aria-controls="code-${ch.id}-${t.id}" aria-selected="${k === 0}" tabindex="${k === 0 ? 0 : -1}">${esc(t.label)}</button>`).join('');
  const panes = c.tabs.map((t, k) => `<pre role="tabpanel" id="code-${ch.id}-${t.id}" aria-labelledby="tab-${ch.id}-${t.id}"${k ? ' hidden' : ''}>${highlight(t.code)}</pre>`).join('\n');
  const resp = (c.response || []).map((r, k) => `<li><i>${k + 1}</i><span>${esc(r.name)}</span><b>${esc(r.score)}</b></li>`).join('');
  return `${actOpen(ch, 'act-ship')}
  <div class="copy">
    ${h2(ch)}
    ${deck(c.deck)}
    <div class="tabs" role="tablist" aria-label="Language" data-role="tabs">${tabs}</div>
    <div class="codeblock mono">${panes}</div>
    ${resp ? `<ol class="rows hits mono" aria-label="Sample response">${resp}</ol>` : ''}
  </div>
</section>`;
}

export const css = () => `
/* ship */
.tabs { display: flex; gap: 22px; border-bottom: 1px solid var(--hair); flex-wrap: wrap; }
.tabs button { background: none; border: 0; border-bottom: 2px solid transparent; margin-bottom: -1px; color: var(--ink-soft); font: 500 15px/1 var(--font); min-height: 44px; padding: 0 2px; cursor: pointer; transition: color .3s, border-color .3s; }
.tabs button[aria-selected="true"] { color: var(--ink); border-bottom-color: var(--accent-text); }
.codeblock pre { margin: 0; font-size: clamp(13px, 1.3vw, 19px); line-height: 1.7; white-space: pre-wrap; color: var(--ink); overflow-wrap: anywhere; }
.codeblock .k { color: var(--accent-text); } .codeblock .s { color: var(--ink-soft); }
.hits { padding-top: 16px; border-top: 1px solid var(--hair); font-size: 14px; }
.act-ship h2 { font-size: clamp(44px, 6.4vw, 108px); }
`;
