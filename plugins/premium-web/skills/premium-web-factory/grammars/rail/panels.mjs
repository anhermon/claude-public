import { esc, lines } from '../../archetypes/_shared.mjs';

const SVG = { width: 600, height: 360, midY: 180, nodeRadius: 22, inset: 65, outerRadius: 145, innerRadius: 96 };
const LINE_STEPS = 28, LINE_SPACING = 44, LINE_AMP = 45, LINE_PHASE = 0.4;
const ordinal = (i) => String(i + 1).padStart(2, '0');

export function ambient(count) {
  const paths = Array.from({ length: count }, (_, i) => {
    const points = Array.from({ length: LINE_STEPS + 1 }, (_, k) => {
      const x = k / LINE_STEPS * SVG.width;
      const y = i * LINE_SPACING + Math.sin(k / LINE_STEPS * Math.PI * 2 + i * LINE_PHASE) * LINE_AMP;
      return `${k ? 'L' : 'M'}${x.toFixed(1)},${y.toFixed(1)}`;
    });
    return `<path d="${points.join(' ')}"/>`;
  });
  return `<svg class="rail-ambient" viewBox="0 0 ${SVG.width} ${SVG.height}" preserveAspectRatio="none" aria-hidden="true"><g data-contours>${paths.join('')}</g></svg>`;
}

export function graphic(figure) {
  const f = figure;
  if (f.kind === 'stat') return `<p class="rail-stat">${esc(f.value)}</p>`;
  if (f.kind === 'timeline') return `<ol class="rail-timeline">${f.items.map((item, i) => `<li><span class="mono">${ordinal(i)}</span><p>${esc(item)}</p></li>`).join('')}</ol>`;
  if (f.kind === 'diagram') {
    const nodes = f.items.map((_, i) => {
      const x = SVG.inset + i / (f.items.length - 1) * (SVG.width - SVG.inset * 2);
      return `<circle cx="${x}" cy="${SVG.midY}" r="${SVG.nodeRadius}"/><text x="${x}" y="${SVG.midY}" dominant-baseline="central" text-anchor="middle">${ordinal(i)}</text>`;
    }).join('');
    return `<svg viewBox="0 0 ${SVG.width} ${SVG.height}" aria-hidden="true"><path d="M${SVG.inset},${SVG.midY}H${SVG.width - SVG.inset}"/>${nodes}</svg><ol class="rail-labels">${f.items.map((item) => `<li>${esc(item)}</li>`).join('')}</ol>`;
  }
  return `<svg class="rail-seal" viewBox="0 0 ${SVG.width} ${SVG.height}" aria-hidden="true"><circle cx="${SVG.width / 2}" cy="${SVG.midY}" r="${SVG.outerRadius}"/><circle cx="${SVG.width / 2}" cy="${SVG.midY}" r="${SVG.innerRadius}"/><path d="M0,${SVG.midY}H${SVG.width}M${SVG.width / 2},0V${SVG.height}"/></svg>${f.value ? `<p class="rail-note">${esc(f.value)}</p>` : ''}`;
}

function kinetic(title) {
  return title.split(/\s+/).map((word) => `<span class="kinetic-word" data-letter aria-hidden="true">${esc(word)}</span>`).join(' ');
}

export function renderPanels(piece) {
  return piece.rail.panels.map((p, i) => {
    const tag = i ? 'h2' : 'h1', world = piece.worlds[i];
    return `<article class="rail-panel" id="${p.id}" data-panel="${i}" aria-labelledby="h-${p.id}" style="--panel-ground:${world.base};--panel-accent:${world.accent}">
    <p class="rail-eyebrow mono">${ordinal(i)} / ${esc(p.eyebrow || piece.name)}</p>
    <${tag} id="h-${p.id}" class="rail-title" aria-label="${esc(p.title)}">${kinetic(p.title)}</${tag}>
    <div class="rail-copy"><p>${lines(p.copy)}</p><a class="link" href="#${piece.rail.panels[i + 1]?.id || piece.chapters[0]?.id || 'rail-end'}">${i < piece.rail.panels.length - 1 ? 'Next study' : 'Continue'} <span aria-hidden="true">↗</span></a></div>
    <figure class="rail-figure" data-figure="${p.figure.kind}">${graphic(p.figure)}<figcaption class="mono">${esc(p.figure.label)}</figcaption></figure>
  </article>`;
  }).join('\n');
}
