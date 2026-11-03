// base.css (tokens, type, nav, glass, finish) and sections.css (shared layout + the CSS of exactly the archetypes used).
import { ARCHETYPES } from '../../archetypes/index.mjs';
import { SHARED_CSS } from '../../archetypes/_shared.mjs';

const hexToRgb = (h) => [1, 3, 5].map((i) => parseInt(h.slice(i, i + 2), 16));
const rgba = (h, a) => `rgba(${hexToRgb(h).join(', ')}, ${a})`;
const mix = (a, b, t) => { const A = hexToRgb(a), B = hexToRgb(b); return '#' + A.map((v, i) => Math.round(v + (B[i] - v) * t).toString(16).padStart(2, '0')).join(''); };
const GLASS_LIFT = 0.1;     // dark glass = ground lifted toward ink by this much
const HAIR_ALPHA = 0.14, GLASS_ALPHA = 0.5, GLASS_LINE_ALPHA = 0.16;

const stack = (f, extra = '') => `"${f.family}"${extra}, ${f.fallback === 'monospace' ? 'ui-monospace, "SF Mono", Menlo, monospace' : f.fallback}`;

export function baseCss(piece) {
  const p = piece.palette, L = p.light, F = piece.fonts;
  const glassDark = mix(p.ground, p.ink, GLASS_LIFT);
  const faces = piece.fontFaces || '';
  return `${faces}
:root {
  --ground: ${p.ground}; --ink: ${p.ink}; --ink-soft: ${p.inkSoft}; --hair: ${rgba(p.ink, HAIR_ALPHA)}; --accent: ${p.accent}; --accent-text: ${p.accentText};
  --glass-bg: ${rgba(glassDark, GLASS_ALPHA)}; --glass-line: ${rgba(p.ink, GLASS_LINE_ALPHA)}; --glass-hi: rgba(255, 255, 255, 0.2);
  --font: ${stack(F.body)}; --font-display: ${stack(F.display)}; --mono: ${stack(F.mono)};
  --display-weight: ${F.display.weight || 300}; --display-stretch: ${F.display.stretch || 100}%;
  --pad: clamp(20px, 5vw, 88px); --nav-h: 64px; --ease: cubic-bezier(0.16, 1, 0.3, 1); --world-t: 0.7s;
  --ck-loader-bg: ${p.ground}; --ck-loader-fg: ${p.ink}; --ck-font-sans: ${stack(F.body)}; --ck-font-mono: ${stack(F.mono)};
  color-scheme: dark;
}
html[data-world="light"] {
  --ground: ${L.ground}; --ink: ${L.ink}; --ink-soft: ${L.inkSoft}; --hair: ${rgba(L.ink, HAIR_ALPHA)}; --accent-text: ${L.accentText};
  --glass-bg: rgba(255, 255, 255, 0.46); --glass-line: ${rgba(L.ink, GLASS_LINE_ALPHA)}; --glass-hi: rgba(255, 255, 255, 0.9); color-scheme: light;
}
* { box-sizing: border-box; }
html { background: var(--ground); scroll-behavior: smooth; }
body { margin: 0; color: var(--ink); font: 400 clamp(16px, 1.25vw, 19px)/1.55 var(--font); -webkit-font-smoothing: antialiased; transition: color var(--world-t) var(--ease); overflow-x: clip; }
h1, h2, h3, p, ol, ul, dl, dd, figure { margin: 0; }
a { color: inherit; }
:focus-visible { outline: 2px solid var(--accent); outline-offset: 3px; border-radius: 4px; }
.skip { position: absolute; left: -999px; top: 8px; z-index: 100; background: #fff; color: #000; padding: 10px 14px; border-radius: 8px; } .skip:focus { left: 8px; }
.mono { font-family: var(--mono); font-weight: 400; letter-spacing: 0; }
.vh, .ck-sr { position: absolute; width: 1px; height: 1px; overflow: hidden; clip: rect(0 0 0 0); white-space: nowrap; }
.gl-stage-poster { background-color: var(--ground); }

h1, h2 { font-family: var(--font-display); font-weight: var(--display-weight); font-stretch: var(--display-stretch); letter-spacing: -0.035em; line-height: 1.0; text-wrap: balance; }
h1 { font-size: clamp(46px, 8vw, 128px); }
h2 { font-size: clamp(36px, 5.2vw, 84px); line-height: 1.04; letter-spacing: -0.03em; }
h1 em, h2 em { font-style: normal; color: var(--accent-text); transition: color var(--world-t) var(--ease); }
.deck { color: var(--ink-soft); max-width: 44ch; transition: color var(--world-t) var(--ease); }

.nav { position: fixed; top: 14px; left: 50%; transform: translateX(-50%); z-index: 50; width: min(1180px, calc(100% - 28px)); height: 52px; display: flex; align-items: center; gap: 6px; padding: 0 8px 0 16px; border-radius: 999px; }
.glass { background: var(--glass-bg); -webkit-backdrop-filter: blur(24px) saturate(1.4); backdrop-filter: blur(24px) saturate(1.4); border: 1px solid var(--glass-line); box-shadow: inset 0 1px 0 var(--glass-hi); transition: background-color var(--world-t), border-color var(--world-t); }
.brand { min-height: 44px; display: flex; align-items: center; gap: 9px; font: 600 17px/1 var(--font-display); font-stretch: var(--display-stretch); text-decoration: none; margin-right: auto; }
.nav nav { display: flex; gap: 2px; }
.nav nav a { padding: 8px 14px; border-radius: 999px; text-decoration: none; font-size: 14px; color: var(--ink-soft); transition: color .3s, background-color .3s; }
.nav nav a:hover, .nav nav a[aria-current="true"] { color: var(--ink); background: ${rgba(p.ink, 0.1)}; }
html[data-world="light"] .nav nav a:hover, html[data-world="light"] .nav nav a[aria-current="true"] { background: ${rgba(L.ink, 0.08)}; }
.concept-tag { font: 400 11.5px/1 var(--mono); color: var(--ink-soft); padding: 8px 12px; border: 1px solid var(--hair); border-radius: 999px; white-space: nowrap; }
.concept-tag .short { display: none; }
.btn { display: inline-flex; align-items: center; justify-content: center; min-height: 44px; padding: 0 22px; border-radius: 999px; background: var(--ink); color: var(--ground); font-weight: 500; text-decoration: none; font-size: 15px; transition: transform .4s var(--ease), background-color var(--world-t), color var(--world-t); }
.btn:hover { transform: translateY(-2px); } .btn.sm { min-height: 38px; padding: 0 16px; font-size: 14px; }
.link { color: var(--ink); text-underline-offset: 5px; text-decoration-thickness: 1px; }

.finish::before, .finish::after { content: ""; position: fixed; inset: 0; pointer-events: none; z-index: 40; }
.finish::before { opacity: 0.06; mix-blend-mode: overlay; background-size: 220px; background-image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='220' height='220'><filter id='n'><feTurbulence type='fractalNoise' baseFrequency='.8' numOctaves='2' stitchTiles='stitch'/><feColorMatrix values='0 0 0 0 .5  0 0 0 0 .5  0 0 0 0 .5  0 0 0 1 0'/></filter><rect width='100%' height='100%' filter='url(%23n)'/></svg>"); }
.finish::after { background: radial-gradient(ellipse at 50% 45%, transparent 58%, rgba(0, 0, 0, 0.32)); transition: opacity var(--world-t); }
html[data-world="light"] .finish::after { opacity: 0.25; }
[data-ck-hidden] { will-change: opacity, filter, transform; }
.ck-line { display: block; } .ck-word, .ck-char { display: inline-block; white-space: pre; }
html.is-loading body::before { content: ""; position: fixed; inset: 0; z-index: 9998; background: var(--ground); }
@media (max-width: ${piece.mobileMaxW}px) {
  .nav nav { display: none; } .nav { padding-left: 14px; } .concept-tag { font-size: 12px; padding: 7px 10px; } .brand { font-size: 16px; }
  .concept-tag .long { display: none; } .concept-tag .short { display: inline; }
}
@media (max-width: 430px) { .btn.sm { padding: 0 12px; } }
.nav .btn.sm { white-space: nowrap; flex: none; } .concept-tag { min-width: 0; overflow: hidden; white-space: nowrap; text-overflow: ellipsis; }
@media (prefers-reduced-motion: reduce) { html { scroll-behavior: auto; } [data-ck-hidden] { opacity: 1 !important; filter: none !important; transform: none !important; } }
`;
}

export function sectionsCss(piece) {
  const seen = new Set(), parts = [SHARED_CSS(piece)];
  for (const ch of piece.chapters) {
    if (seen.has(ch.archetype)) continue;
    seen.add(ch.archetype);
    parts.push(ARCHETYPES[ch.archetype].css(piece, ch));
  }
  return parts.join('\n');
}
