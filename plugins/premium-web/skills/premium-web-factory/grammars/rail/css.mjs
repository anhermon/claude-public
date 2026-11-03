import { SHARED_CSS, mq } from '../../archetypes/_shared.mjs';
import { ARCHETYPES } from '../../archetypes/index.mjs';

export function css(piece) {
  const commerce = [...new Set(piece.chapters.map((c) => c.archetype))].map((id) => ARCHETYPES[id].css(piece)).join('\n');
  return SHARED_CSS(piece) + commerce + `
/* Rail: vertical is the baseline, including without JS and in reduced motion. */
body { background: var(--ground); }
.rail { position: relative; }
.rail-viewport { position: relative; overflow: clip; }
.rail-track { position: relative; }
.rail-panel { position: relative; isolation: isolate; display: grid; grid-template-columns: 1fr 1fr; grid-template-rows: auto auto 1fr; gap: 24px 6vw; min-height: 100svh; padding: calc(var(--nav-h) + 40px) var(--pad) 9svh; background: color-mix(in srgb, var(--panel-ground) 94%, transparent); border-bottom: 1px solid var(--hair); }
.rail-panel:nth-child(even) { background:linear-gradient(115deg,color-mix(in srgb,var(--panel-accent) 16%,var(--panel-ground)),var(--panel-ground)); }
.rail-eyebrow { grid-column: 1 / -1; color: var(--accent-text); font-size: 12px; letter-spacing: .09em; text-transform: uppercase; }
.rail-title { grid-column: 1 / -1; max-width: 100%; font-size: clamp(60px, min(9vw, 15svh), 156px); line-height: .98; letter-spacing: -.055em; font-weight: var(--display-weight); }
.kinetic-word { display: inline-block; white-space: nowrap; }
[data-letter] { display: inline-block; transform-origin: 50% 70%; }
.rail-copy { display: grid; align-content: end; gap: 28px; max-width: 36ch; padding-bottom: 4svh; }
.rail-copy p { color: var(--ink-soft); font-size: clamp(18px, 1.8vw, 26px); line-height: 1.4; }
.rail-copy a { justify-self: start; min-height: 44px; display: inline-flex; align-items: center; gap: 22px; }
.rail-figure { min-width: 0; align-self: center; display: grid; gap: 20px; transform-origin: center; }
.rail-figure svg { display: block; width: 100%; max-height: 40svh; overflow: visible; fill: none; stroke: var(--panel-accent); stroke-width: 1.5; }
.rail-figure svg circle { fill: var(--panel-ground); }
.rail-figure svg text { fill: var(--ink); stroke: none; font: 14px var(--mono); }
.rail-figure figcaption { font-size: 12px; color: var(--ink-soft); padding-top: 16px; border-top: 1px solid var(--hair); }
.rail-stat { font: var(--display-weight) clamp(90px, min(17vw, 29svh), 280px)/1 var(--font-display); letter-spacing: -.07em; color: var(--panel-accent); overflow-wrap: anywhere; }
.rail-timeline { list-style: none; padding: 0; display: grid; gap: 18px; }
.rail-timeline li { display: grid; grid-template-columns: 36px 1fr; gap: 16px; padding-top: 12px; border-top: 1px solid var(--hair); }
.rail-timeline span { font-size: 12px; color: var(--panel-accent); }
.rail-labels { list-style: none; padding: 0; display: flex; justify-content: space-between; gap: 16px; font-size: 14px; }
.rail-note { font: var(--display-weight) clamp(24px, 3vw, 42px)/1.2 var(--font-display); }
.rail-ambient { position: absolute; inset: 0; width: 100%; height: 100%; opacity: .08; z-index: 2; pointer-events: none; fill: none; stroke: var(--accent); stroke-width: .7; }
.rail-progress { display: none; position: absolute; z-index: 3; bottom: 24px; left: var(--pad); right: var(--pad); grid-template-columns: auto 1fr auto; align-items: center; gap: 20px; font-size: 12px; }
.rail-progress-rule { height: 2px; background: var(--hair); }
.rail-progress-rule i { display: block; height: 100%; background: var(--accent); transform-origin: left; transform: scaleX(var(--rail-progress, 0)); }
.rail.is-pinned .rail-viewport { position: sticky; top: 0; height: 100svh; overflow: hidden; }
.rail.is-pinned .rail-track { display: flex; width: max-content; will-change: transform; }
.rail.is-pinned .rail-panel { flex: 0 0 ${piece.rail.params.panelVw}vw; width: ${piece.rail.params.panelVw}vw; height: 100svh; border-right: 1px solid var(--hair); border-bottom: 0; }
.rail.is-pinned .rail-progress { display: grid; }
.rail-commerce.act { min-height: 0; padding-top: calc(var(--nav-h) + 7svh); padding-bottom: 9svh; justify-content: center; text-align: left; border-top: 1px solid var(--hair); }
.rail-commerce.act .copy { width: 100%; max-width: 960px; justify-items: stretch; }
.rail-commerce .deck { max-width: 56ch; }
.rail-commerce .matrix { background: var(--glass-bg); }
.rail-commerce.act-pricing { background:#e6d5b8; color:#231a13; --ink:#231a13; --ink-soft:#524332; --accent:#715014; --accent-text:#715014; --hair:#b3a185; --glass-bg:#dbc6a1; --glass-line:#a98d62; --glass-hi:#f4e9d5; }
.rail-commerce.act-faq { background:#2f2921; }
.rail-interlude { position:relative; min-height:85svh; display:flex; align-items:flex-end; padding:9svh var(--pad); overflow:hidden; background:#594730; }
.rail-interlude > svg { position:absolute; inset:0; width:100%; height:100%; }
.rail-interlude > div { position:relative; display:grid; gap:24px; max-width:70vw; }
.rail-interlude h2 { font-size:clamp(80px,12vw,190px); line-height:.9; max-width:10ch; }
.rail-interlude p { max-width:40ch; }
.rail-interlude .mono { font-size:12px; letter-spacing:.09em; }
.rail-commerce .copy { max-width:none; }
.rail-commerce h2 { font-size:clamp(60px,8vw,128px); max-width:14ch; }
.rail-commerce .matrix { border-radius:0; border-inline:0; box-shadow:none; }
.rail-commerce .trow { border-radius:0; grid-template-columns:2fr 1fr; }
.rail-commerce .trow:nth-child(even) { margin-left:12%; }
.rail-end { padding: 4svh var(--pad); border-top: 1px solid var(--hair); display: flex; gap: 24px; justify-content: space-between; flex-wrap: wrap; }
.rail-end p { font-size: 12px; max-width: 70ch; color: var(--ink-soft); }
.rail-end a { min-height: 44px; display: inline-flex; align-items: center; }
${mq(piece, `.rail-panel { display: flex; flex-direction: column; gap: 24px; min-height: 100svh; padding-top: calc(var(--nav-h) + 32px); padding-bottom: 48px; }
.rail-title { font-size: clamp(44px, 12vw, 76px); overflow-wrap: anywhere; }
.kinetic-word { white-space: normal; }
.rail-copy { padding-bottom: 0; gap: 16px; }
.rail-copy p { font-size: 18px; }
.rail-figure { align-self: stretch; margin-top: auto; padding-top: 24px; }
.rail-stat { font-size: clamp(100px, 27vw, 180px); }
.rail-figure svg { max-height: 30svh; }
.rail-ambient { opacity: .06; }
.rail-commerce.act { padding-top: calc(var(--nav-h) + 32px); padding-bottom: 48px; }
.rail-commerce.act .copy { max-width: none; }
.rail-interlude { min-height:80svh; padding-block:64px; }.rail-interlude > div { max-width:none; }.rail-interlude h2 { font-size:18vw; }
.rail-labels { flex-wrap: wrap; }
.rail-end { padding-block: 32px; }`)}
@media (prefers-reduced-motion: reduce) { [data-letter], .rail-figure { transform: none !important; clip-path: none !important; } }
`;
}
