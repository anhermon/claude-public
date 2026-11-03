// band: a full-bleed media band that opens from an inset frame as it scrolls into view, with one big line. The plate is a
// procedural SVG (seeded contour lines) unless a generated file exists at img/<file> at generation time (env.assetFor).
import { esc, lines, mq } from './_shared.mjs';

export const meta = {
  id: 'band', needsTarget: false, needsCommerce: false, copyRequired: ['line'],
  params: { slot: 'band', lineCount: 16, heightSvh: 130 },
  doc: { copy: 'line (use \\n for a break), caption?', params: 'slot (asset slot name, default band), lineCount (procedural contours), heightSvh (scroll length)' },
};

const W = 1600, H = 900, STEPS = 48;
function rng(seed) { let a = seed >>> 0; return () => { a = (a + 0x6d2b79f5) >>> 0; let t = a; t = Math.imul(t ^ (t >>> 15), t | 1); t ^= t + Math.imul(t ^ (t >>> 7), t | 61); return ((t ^ (t >>> 14)) >>> 0) / 4294967296; }; }

/** Procedural plate: flowing contour lines around a soft glow. Deterministic per (seed). */
export function plateSvg(seed, n) {
  const r = rng(seed), paths = [];
  const f1 = 1 + r() * 1.5, f2 = 2 + r() * 2.5, ph = r() * 6.28, amp = 70 + r() * 60;
  for (let i = 0; i < n; i++) {
    const base = (i + 0.5) / n * H, pts = [];
    for (let s = 0; s <= STEPS; s++) {
      const x = (s / STEPS) * W, u = s / STEPS * 6.283;
      const y = base + Math.sin(u * f1 + ph + i * 0.21) * amp * (0.4 + i / n) + Math.sin(u * f2 + i * 0.5) * amp * 0.35;
      pts.push(`${s ? 'L' : 'M'}${x.toFixed(1)} ${y.toFixed(1)}`);
    }
    paths.push(`<path d="${pts.join('')}" opacity="${(0.12 + 0.5 * Math.pow(Math.sin((i / n) * Math.PI), 1.6)).toFixed(2)}"/>`);
  }
  return `<svg class="plate" viewBox="0 0 ${W} ${H}" preserveAspectRatio="xMidYMid slice" aria-hidden="true" focusable="false"><defs><radialGradient id="pg" cx="68%" cy="50%" r="60%"><stop offset="0" stop-color="var(--accent)" stop-opacity=".55"/><stop offset=".5" stop-color="var(--accent)" stop-opacity=".12"/><stop offset="1" stop-color="var(--accent)" stop-opacity="0"/></radialGradient></defs><rect width="${W}" height="${H}" fill="url(#pg)"/><g fill="none" stroke="var(--accent-text)" stroke-width="1.4">${paths.join('')}</g></svg>`;
}

export function render(ch, piece, env) {
  const a = env.assetFor(ch.params.slot);
  const art = a ? `<img class="plate" src="${esc(a.file)}" alt="${esc(a.alt || '')}" loading="lazy">` : plateSvg(piece.subject.seed, ch.params.lineCount);
  return `<section class="band" id="${ch.id}" data-act="${ch.act}" data-archetype="band" aria-label="${esc(ch.copy.caption || 'Material study')}" style="height:${ch.params.heightSvh}svh">
  <div class="band-frame">
    ${art}
    <p class="band-line" data-motion="blur-line">${lines(ch.copy.line)}</p>
    ${ch.copy.caption ? `<p class="fine mono band-cap">${esc(ch.copy.caption)}</p>` : ''}
  </div>
</section>`;
}

export function css(piece) {
  return `
/* band: sticky frame opens from an inset clip as --band-p goes 0 -> 1 (set by runtime/archetypes/band.js) */
.band { position: relative; padding: 0; }
.band-frame { position: sticky; top: 0; height: 100svh; overflow: hidden; clip-path: inset(calc((1 - var(--band-p, 1)) * 9vh) calc((1 - var(--band-p, 1)) * 9vw) round calc((1 - var(--band-p, 1)) * 28px)); background: var(--band-bg, #05080d); }
.band-frame .plate { position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; transform: scale(calc(1.14 - var(--band-p, 1) * 0.14)); }
.band-line { position: absolute; left: var(--pad); right: var(--pad); bottom: 14svh; font: var(--display-weight) clamp(40px, 6.4vw, 104px)/1.02 var(--font-display); font-stretch: var(--display-stretch); letter-spacing: -0.035em; max-width: 12em; color: #f2f7f6; text-wrap: balance; }
.band-cap { position: absolute; left: var(--pad); bottom: 5svh; color: rgba(242, 247, 246, 0.62); }
${mq(piece, `.band-line { bottom: 16svh; font-size: clamp(36px, 10.4vw, 64px); }`)}
@media (prefers-reduced-motion: reduce) { .band-frame { clip-path: none; } }`;
}
