// svgfig: config -> one animated, accessible, self-contained SVG figure. No dependencies.
//   node svgfig.mjs diagram.config.json > figure.svg        (kind "diagram" or "bars")
// Draw-on uses pathLength="1" + stroke-dashoffset, bars use scaleX, everything else fades; all in CSS inside the SVG (no JS needed to play).
// trigger "load": plays on load (right for a standalone <img>/file). "inview": hidden state only while svg.pending, played when
// figure.js swaps pending -> live, so the figure is fully visible with JS off, with reduced motion, and in print.
// Timings are authored starting values (no source corpus); easing is the expo-out used elsewhere in this plugin.
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';

export const K = {
  FONT_PX: 14, SUB_PX: 12, STROKE: 1.5, RADIUS: 10, PAD: 16, ARROW: 7, LEAD_GAP: 6,
  STAGGER_MS: 300, DRAW_MS: 600, FADE_MS: 500, ARROW_AFTER: 0.8, EDGE_AT: 0.5,
  EASE: 'cubic-bezier(.16,1,.3,1)',
  BAR_H: 26, BAR_GAP: 14, LABEL_W: 150, VALUE_W: 70, BAR_GROW_MS: 700, BAR_STAGGER_MS: 120, SOURCE_PX: 12,
  COLORS: { ink: '#16181d', line: '#16181d', accent: '#e4572e', bg: 'transparent' },
};
const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
const num = (n) => +n.toFixed(2);
const lines = (x, y, text, anchor = 'middle', lh = K.FONT_PX * 1.25) => (Array.isArray(text) ? text : [text])
  .map((t, i) => `<text x="${num(x)}" y="${num(y + i * lh)}" text-anchor="${anchor}">${esc(t)}</text>`).join('');

function css(id, trigger) {
  const F = `.${id}`, hide = trigger === 'load' ? F : `${F}.pending`, play = trigger === 'load' ? F : `${F}.live`;
  const c = K.COLORS;
  return `${F}{--fig-ink:${c.ink};--fig-line:${c.line};--fig-accent:${c.accent};--fig-bg:${c.bg};font:${K.FONT_PX}px var(--fig-font,system-ui,sans-serif);color:var(--fig-ink)}`
    + `${F} text{fill:var(--fig-ink)}${F} .sub{font-size:${K.SUB_PX}px}${F} .sub text,${F} .src{fill-opacity:.7}${F} .src{font-size:${K.SOURCE_PX}px}`
    + `${F} .node rect{fill:var(--fig-bg);stroke:var(--fig-line);stroke-width:${K.STROKE}}${F} .accent rect{stroke:var(--fig-accent)}`
    + `${F} .draw,${F} .lead{fill:none;stroke:var(--fig-line);stroke-width:${K.STROKE};stroke-linecap:round;stroke-linejoin:round}${F} .lead{stroke-opacity:.5}`
    + `${F} .arrow{fill:var(--fig-line)}${F} .bar{fill:var(--fig-line);transform-box:fill-box;transform-origin:0 50%}${F} .hi{fill:var(--fig-accent)}`
    + `${hide} .draw{stroke-dasharray:1;stroke-dashoffset:1}${hide} .node,${hide} .note{opacity:0}${hide} .bar{transform:scaleX(0)}`
    + `${play} .draw{stroke-dasharray:1;stroke-dashoffset:1;animation:${id}-d ${K.DRAW_MS}ms ${K.EASE} var(--d,0ms) forwards}`
    + `${play} .node,${play} .note{opacity:0;animation:${id}-f ${K.FADE_MS}ms ${K.EASE} var(--d,0ms) forwards}`
    + `${play} .bar{transform:scaleX(0);animation:${id}-g ${K.BAR_GROW_MS}ms ${K.EASE} var(--d,0ms) forwards}`
    + `@keyframes ${id}-d{to{stroke-dashoffset:0}}@keyframes ${id}-f{to{opacity:1}}@keyframes ${id}-g{to{transform:scaleX(1)}}`
    + `@media (prefers-reduced-motion:reduce){${hide} .draw,${play} .draw{stroke-dasharray:none;stroke-dashoffset:0;animation:none}`
    + `${hide} .node,${hide} .note,${play} .node,${play} .note{opacity:1;animation:none}${hide} .bar,${play} .bar{transform:none;animation:none}}`;
}

function edgePath(a, b) {
  if (b.x >= a.x + a.w) {                                   // left-to-right: right edge to left edge, elbow at mid x
    const x1 = a.x + a.w, y1 = a.y + a.h / 2, x2 = b.x, y2 = b.y + b.h / 2, mx = (x1 + x2) / 2;
    return { d: y1 === y2 ? `M${x1} ${y1}H${x2}` : `M${x1} ${y1}H${mx}V${y2}H${x2}`, tip: [x2, y2], dir: [1, 0] };
  }
  const x1 = a.x + a.w / 2, y1 = b.y > a.y ? a.y + a.h : a.y, x2 = b.x + b.w / 2, y2 = b.y > a.y ? b.y : b.y + b.h, my = (y1 + y2) / 2;
  return { d: x1 === x2 ? `M${x1} ${y1}V${y2}` : `M${x1} ${y1}V${my}H${x2}V${y2}`, tip: [x2, y2], dir: [0, y2 > y1 ? 1 : -1] };
}
const arrowHead = ([x, y], [dx, dy]) => `M${x} ${y}L${num(x - dx * K.ARROW - dy * K.ARROW / 2)} ${num(y - dy * K.ARROW - dx * K.ARROW / 2)}L${num(x - dx * K.ARROW + dy * K.ARROW / 2)} ${num(y - dy * K.ARROW + dx * K.ARROW / 2)}Z`;

function diagram(cfg) {
  const by = Object.fromEntries(cfg.nodes.map((n) => [n.id, n])), idx = Object.fromEntries(cfg.nodes.map((n, i) => [n.id, i]));
  const out = [];
  cfg.nodes.forEach((n, i) => {
    const cy = n.y + n.h / 2, two = n.sub != null;
    out.push(`<g class="node${n.accent ? ' accent' : ''}" style="--d:${i * K.STAGGER_MS}ms"><rect x="${n.x}" y="${n.y}" width="${n.w}" height="${n.h}" rx="${K.RADIUS}"/>`
      + lines(n.x + n.w / 2, two ? cy - 2 : cy + K.FONT_PX * 0.35, n.label) + (two ? `<g class="sub">${lines(n.x + n.w / 2, cy + K.SUB_PX + 2, n.sub, 'middle', K.SUB_PX * 1.25)}</g>` : '') + '</g>');
  });
  for (const e of cfg.edges || []) {
    const a = by[e.from], b = by[e.to], p = edgePath(a, b), at = (idx[e.from] + K.EDGE_AT) * K.STAGGER_MS;
    out.push(`<path class="draw" pathLength="1" d="${p.d}" style="--d:${at}ms"/>`
      + `<path class="arrow note" d="${arrowHead(p.tip, p.dir)}" style="--d:${at + K.DRAW_MS * K.ARROW_AFTER}ms"/>`);
    if (e.label) out.push(`<g class="note sub" style="--d:${at + K.DRAW_MS * K.ARROW_AFTER}ms">${lines(...[(a.x + a.w + b.x) / 2, Math.min(a.y, b.y) + Math.min(a.h, b.h) / 2 - 8, e.label])}</g>`);
  }
  const end = cfg.nodes.length * K.STAGGER_MS;
  (cfg.callouts || []).forEach((c, i) => {
    const n = by[c.node], top = (c.side || 'top') === 'top', x = n.x + n.w / 2, y1 = top ? n.y - K.LEAD_GAP : n.y + n.h + K.LEAD_GAP, y2 = top ? y1 - (c.dy || 28) : y1 + (c.dy || 28);
    out.push(`<g class="note" style="--d:${end + i * K.STAGGER_MS}ms"><path class="lead" d="M${x} ${y1}V${y2}"/>${lines(x, top ? y2 - 6 - ((Array.isArray(c.text) ? c.text.length : 1) - 1) * K.FONT_PX * 1.25 : y2 + K.FONT_PX + 2, c.text)}</g>`);
  });
  return out.join('');
}

function bars(cfg) {
  const max = Math.max(...cfg.values.map((v) => v.value)), w = cfg.width - K.LABEL_W - K.VALUE_W - K.PAD, out = [];
  cfg.values.forEach((v, i) => {
    const y = K.PAD + i * (K.BAR_H + K.BAR_GAP), bw = num((v.value / max) * w), d = `${i * K.BAR_STAGGER_MS}ms`;   // baseline is zero: bars are never truncated
    out.push(`<text x="${K.LABEL_W - 10}" y="${y + K.BAR_H / 2 + K.FONT_PX * 0.35}" text-anchor="end">${esc(v.label)}</text>`
      + `<rect class="bar${v.highlight ? ' hi' : ''}" x="${K.LABEL_W}" y="${y}" width="${bw}" height="${K.BAR_H}" rx="3" style="--d:${d}"/>`
      + `<g class="note" style="--d:${i * K.BAR_STAGGER_MS + K.BAR_GROW_MS * 0.6}ms">${lines(K.LABEL_W + bw + 8, y + K.BAR_H / 2 + K.FONT_PX * 0.35, `${v.value}${cfg.unit || ''}`, 'start')}</g>`);   // direct labels, no legend, no axis
  });
  if (cfg.source) out.push(`<text class="src" x="${K.LABEL_W}" y="${cfg.height - 6}">${esc(cfg.source)}</text>`);
  return out.join('');
}

/** render(config) -> SVG string. Required: id, kind, width, title, desc, and height (diagram only). */
export function render(cfg) {
  if (cfg.kind === 'bars') cfg = { ...cfg, height: cfg.height ?? K.PAD * 2 + cfg.values.length * (K.BAR_H + K.BAR_GAP) + K.SOURCE_PX * 2 };   // bars size themselves
  for (const k of ['id', 'kind', 'width', 'height', 'title', 'desc']) if (cfg[k] == null) throw new Error(`svgfig: config.${k} is required (title and desc are the accessible name and description)`);
  const trigger = cfg.trigger || 'load', body = cfg.kind === 'bars' ? bars(cfg) : diagram(cfg);
  return `<svg xmlns="http://www.w3.org/2000/svg" class="${cfg.id}" data-fig="" viewBox="0 0 ${cfg.width} ${cfg.height}" role="img" aria-labelledby="${cfg.id}-t ${cfg.id}-d">`
    + `<title id="${cfg.id}-t">${esc(cfg.title)}</title><desc id="${cfg.id}-d">${esc(cfg.desc)}</desc><style>${css(cfg.id, trigger)}</style>${body}</svg>`;
}

if (process.argv[1] === fileURLToPath(import.meta.url)) {
  if (!process.argv[2]) { console.error('usage: node svgfig.mjs <config.json>  (writes the SVG to stdout)'); process.exit(2); }
  process.stdout.write(render(JSON.parse(readFileSync(process.argv[2], 'utf8'))) + '\n');
}
