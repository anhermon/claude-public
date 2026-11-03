import { SHARED_CSS, mq } from '../../archetypes/_shared.mjs';
import { ARCHETYPES } from '../../archetypes/index.mjs';
export function css(piece) {
  const T = piece.terminal.theme;
  const commerce = [...new Set(piece.chapters.map((c) => c.archetype))].map((id) => ARCHETYPES[id].css(piece)).join('\n');
  return SHARED_CSS(piece) + commerce + `
.terminal-page { --screen:${T.screen}; --terminal-text:${T.text}; --signal:${T.signal}; --glitch-time:260ms; }
.terminal-page .nav { border-radius:4px; }
.terminal-chapter { padding:calc(var(--nav-h) + 44px) var(--pad) 28px; min-height:100svh; background:radial-gradient(ellipse at 80% 10%,color-mix(in srgb,var(--accent) 18%,transparent),transparent 65%),repeating-linear-gradient(90deg,transparent 0 79px,var(--hair) 80px),var(--ground); }
.terminal-chapter:nth-child(even) { background:var(--accent); color:var(--ground); }
.terminal-chapter { min-height:0; }
.terminal-chapter:nth-child(3n) { background:var(--screen); color:var(--terminal-text); }
.terminal-chapter:nth-child(3n) .terminal-window { border:0; box-shadow:none; }
.terminal-window { color:var(--terminal-text); background:var(--screen); border:1px solid var(--signal); box-shadow:12px 12px 0 color-mix(in srgb,var(--ground) 50%,transparent),inset 0 0 90px color-mix(in srgb,var(--signal) 6%,transparent); position:relative; isolation:isolate; }
.terminal-window::after { content:''; position:absolute; inset:0; pointer-events:none; opacity:.13; background:repeating-linear-gradient(transparent 0 3px,var(--signal) 4px); }
.terminal-chrome,.terminal-status { display:flex; justify-content:space-between; align-items:center; gap:16px; padding:12px 22px; font-size:11px; border-bottom:1px solid color-mix(in srgb,var(--signal) 30%,transparent); color:var(--signal); }
.terminal-chrome span:first-child { letter-spacing:5px; }
.terminal-heading { padding:28px 28px 20px; }
.terminal-kicker { color:var(--signal); font-size:11px; letter-spacing:.12em; margin-bottom:16px; }
.terminal-heading h1 { font-size:clamp(52px,7.8vw,116px); max-width:15ch; line-height:.95; letter-spacing:-.065em; }
.terminal-heading h2 { font-size:clamp(36px,4.5vw,68px); max-width:20ch; }
.terminal-panes { display:grid; grid-template-columns:1.1fr 1fr; min-height:320px; }
.terminal-log { min-width:0; padding:28px; font-size:clamp(14px,1.25vw,18px); }
.terminal-command { min-height:3.2em; overflow-wrap:anywhere; color:var(--terminal-text); }
.terminal-prompt,.terminal-caret { color:var(--signal); }
.terminal-log pre { font:inherit; line-height:1.8; white-space:pre-wrap; overflow-wrap:anywhere; color:var(--terminal-text); margin:18px 0 0; }
.terminal-diagram { min-width:0; padding:24px 28px; display:grid; align-content:center; border-left:1px solid color-mix(in srgb,var(--signal) 30%,transparent); --panel-accent:var(--signal); --panel-ground:var(--screen); }
.terminal-diagram svg { width:100%; height:280px; fill:none; stroke:var(--signal); stroke-width:1.5; }
.terminal-diagram svg text { fill:var(--terminal-text); stroke:none; font:14px var(--mono); }
.terminal-diagram .rail-stat { color:var(--signal); font:600 clamp(100px,14vw,220px)/.9 var(--font-display); letter-spacing:-.08em; }
.terminal-diagram .rail-timeline,.terminal-diagram .rail-labels { list-style:none; padding:0; display:grid; gap:12px; }
.terminal-diagram .rail-timeline li { display:flex; gap:20px; border-bottom:1px solid var(--hair); padding-bottom:12px; }
.terminal-diagram .rail-labels { display:flex; justify-content:space-between; font-size:12px; }
.terminal-diagram figcaption { font-size:11px; color:var(--signal); border-top:1px solid var(--hair); padding-top:14px; margin-top:20px; }
.terminal-status { border-top:1px solid var(--hair); border-bottom:0; }
.terminal-margin { font-size:11px; display:flex; justify-content:space-between; margin-top:24px; letter-spacing:.1em; }
.terminal-end { padding:40px var(--pad); display:flex; gap:24px; justify-content:space-between; font-size:12px; }
.terminal-end a { display:inline-flex; min-height:44px; align-items:center; }
.terminal-window.is-glitching { animation:terminal-glitch var(--glitch-time) steps(2,end); }
@keyframes terminal-glitch { 20% { filter:contrast(1.5); transform:translateX(2px); } 45% { clip-path:inset(1% 0 2%); transform:translateX(-2px); } 80% { filter:brightness(1.15); } }
${mq(piece, `.terminal-chapter { padding:calc(var(--nav-h) + 28px) 16px 28px; min-height:0; }
.terminal-heading { padding:24px 18px 12px; }.terminal-heading h1 { font-size:54px; }.terminal-heading h2 { font-size:40px; }
.terminal-panes { display:block; }.terminal-log { padding:20px 18px; font-size:13px; }.terminal-diagram { border-left:0; border-top:1px solid var(--hair); padding:20px 18px; }
.terminal-chrome,.terminal-status { padding:12px; font-size:12px; gap:8px; }.terminal-chrome span:first-child { display:none; }
.terminal-kicker,.terminal-diagram figcaption,.terminal-margin { font-size:12px; }
.terminal-diagram svg { max-height:180px; }.terminal-diagram .rail-stat { font-size:140px; }.terminal-end { flex-direction:column; }`)}
@media(prefers-reduced-motion:reduce) { .terminal-window.is-glitching { animation:none; } }
html[data-static-session] .terminal-window.is-glitching { animation:none; }
`;
}
