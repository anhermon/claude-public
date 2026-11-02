// core/split: accessible line/word/char splitting. Original text stays on the parent as aria-label;
// every generated span is aria-hidden. Re-splits when the element width changes (line breaks move).
const DEFAULTS = {
  chars: false,       // also split words into chars
  mask: false,        // wrap each line in an overflow-clip (for mask-line-rise)
  resplitMs: 120,     // debounce for width-change re-split
};
const span = (cls, text) => { const s = document.createElement('span'); s.className = cls; s.setAttribute('aria-hidden', 'true'); if (text != null) s.textContent = text; return s; };

export function split(el, options = {}) {
  const o = { ...DEFAULTS, ...options };
  // <br> is kept as a forced line break (textContent would silently drop it and merge the lines)
  const raw = el.dataset.ckText || [...el.childNodes].map((n) => (n.nodeName === 'BR' ? '\n' : n.textContent)).join('');
  const text = raw.replace(/[^\S\n]+/g, ' ').replace(/ ?\n ?/g, '\n').trim();
  el.dataset.ckText = text;
  el.setAttribute('aria-label', text.replace(/\n/g, ' '));
  const res = { el, text, lines: [], inners: [], words: [], chars: [], revert, destroy };
  let lastW = 0, timer = 0, ro = null, dead = false;

  function build() {
    el.textContent = '';
    const words = [];
    text.split('\n').forEach((seg, si) => {      // a <br> between segments forces the next word onto a new measured line
      if (si) el.append(document.createElement('br'));
      seg.split(' ').filter(Boolean).forEach((t, i) => { const w = span('ck-word', t); words.push(w); if (i) el.append(' '); el.append(w); });
    });
    const groups = [];
    let top = null;
    for (const w of words) {                      // one read pass, no writes in between
      const t = w.offsetTop;
      if (top === null || Math.abs(t - top) > 2) { groups.push([]); top = t; }
      groups[groups.length - 1].push(w);
    }
    el.textContent = '';
    res.lines = []; res.inners = []; res.words = words; res.chars = [];
    for (const g of groups) {
      const line = span('ck-line' + (o.mask ? ' ck-mask' : ''));
      const inner = o.mask ? span('ck-line-inner') : line;
      g.forEach((w, i) => { if (i) inner.append(' '); inner.append(w); });
      if (o.mask) line.append(inner);
      el.append(line);
      res.lines.push(line); res.inners.push(inner);
    }
    if (o.chars) for (const w of words) {
      const t = w.textContent; w.textContent = '';
      for (const c of t) { const cs = span('ck-char', c); w.append(cs); res.chars.push(cs); }
    }
    lastW = el.clientWidth;
  }
  function revert() { destroy(); el.textContent = ''; text.split('\n').forEach((seg, i) => { if (i) el.append(document.createElement('br')); el.append(seg); }); }
  function destroy() { dead = true; clearTimeout(timer); ro && ro.disconnect(); }
  build();
  if (typeof ResizeObserver === 'function') {
    ro = new ResizeObserver(() => {
      if (dead || el.clientWidth === lastW) return;
      clearTimeout(timer);
      timer = setTimeout(() => { if (dead) return; build(); o.onResplit && o.onResplit(res); }, o.resplitMs);
    });
    ro.observe(el);
  }
  return res;
}
