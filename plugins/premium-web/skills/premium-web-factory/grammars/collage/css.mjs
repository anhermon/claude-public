import { mq } from '../../archetypes/_shared.mjs';
export function css(piece) {
  return `
.collage-page { --collage-ink:${piece.palette.ink}; --cursor-limit:22px; }
.collage-page .nav { border-radius:0; background:var(--ground); }
.collage-chapter { position:relative; background:var(--paper); color:var(--collage-ink); padding:calc(var(--nav-h) + 40px) var(--pad) 0; overflow:clip; }
.collage-meta { display:flex; justify-content:space-between; gap:24px; font-size:11px; letter-spacing:.06em; padding-bottom:22px; border-bottom:2px solid currentColor; }
.collage-title { font-size:clamp(22px,3vw,48px); letter-spacing:-.03em; margin:22px 0; max-width:30ch; line-height:1.1; }
.collage-words { display:flex; align-items:baseline; flex-wrap:wrap; gap:0 3vw; padding:12px 24px 28px; margin-inline:-24px; }
.collage-word { display:block; font:900 clamp(64px,calc(140vw / var(--letters)),230px)/.85 var(--font-display); letter-spacing:-.07em; transform:translate(var(--word-x,0px),var(--word-y,0px)) scale(var(--word-scale,1)); transform-origin:center; will-change:transform; }
.collage-word:nth-child(2n) { font-family:Georgia,serif; font-weight:400; font-style:italic; }
.collage-word:nth-child(3n) { -webkit-text-stroke:2px var(--collage-ink); color:transparent; }
.collage-chapter:nth-child(even) .collage-words { flex-direction:row-reverse; }
.collage-chapter:nth-child(3n + 2) .collage-words { flex-direction:column; align-items:flex-start; }
.collage-chapter:nth-child(3n) .collage-word { font-size:clamp(64px,calc(120vw / var(--letters)),194px); }
.collage-bottom { display:grid; grid-template-columns:1fr 1.25fr 1fr; align-items:center; gap:32px; padding-block:24px 40px; }
.collage-deck { max-width:30ch; font-size:clamp(18px,1.5vw,24px); line-height:1.4; }
.collage-plate { transform:rotate(-5deg); color:var(--collage-ink); }
.collage-plate svg { display:block; width:100%; max-height:260px; }
.collage-plate figcaption { font-size:10px; padding-top:14px; }
.collage-cutouts { display:flex; flex-direction:column; gap:12px; }
.collage-block { border:2px solid var(--collage-ink); color:var(--collage-ink); background:var(--cutout); padding:18px; text-align:left; font:700 clamp(18px,2vw,30px)/1.1 var(--font-display); cursor:pointer; transform:rotate(calc((var(--block-order) - 1) * 3deg)); min-height:76px; }
.collage-block:nth-child(even) { margin-left:20%; }
.collage-caption { display:block; max-height:0; overflow:hidden; opacity:0; font:400 13px/1.4 var(--font); transition:max-height .25s,opacity .25s; }
.collage-block:hover .collage-caption,.collage-block:focus-visible .collage-caption,.collage-block[aria-expanded="true"] .collage-caption { max-height:160px; opacity:1; margin-top:10px; }
.collage-marquee { margin-inline:calc(-1 * var(--pad)); padding:16px 0; border-top:2px solid currentColor; border-bottom:2px solid currentColor; overflow:hidden; font-size:16px; font-weight:600; }
.collage-marquee span { display:block; width:max-content; animation:collage-marquee 24s linear infinite; }
.collage-marquee:hover span { animation-play-state:paused; }
@keyframes collage-marquee { to { transform:translateX(-50%); } }
.collage-end { padding:36px var(--pad); display:flex; justify-content:space-between; gap:20px; font-size:12px; }
.collage-end a { display:inline-flex; min-height:44px; align-items:center; }
${mq(piece, `.collage-chapter { padding-top:calc(var(--nav-h) + 28px); }.collage-meta { font-size:9px; }.collage-meta span:last-child { display:none; }
.collage-title { font-size:24px; }.collage-words { padding:18px 12px 24px; margin-inline:-12px; gap:8px 12px; }
.collage-meta { font-size:12px; }.collage-plate figcaption { font-size:12px; }
.collage-word,.collage-chapter:nth-child(3n) .collage-word { font-size:clamp(52px,calc(134vw / var(--letters)),100px); }.collage-word:nth-child(3n) { -webkit-text-stroke:1px var(--collage-ink); }
.collage-bottom { grid-template-columns:1fr; gap:28px; }.collage-deck { max-width:none; }.collage-plate { width:85%; justify-self:center; }
.collage-cutouts { flex-direction:row; flex-wrap:wrap; }.collage-block { flex:1 1 130px; font-size:22px; }.collage-block:nth-child(even) { margin-left:0; }
.collage-end { flex-direction:column; }.collage-caption { max-height:none; opacity:1; margin-top:10px; }`)}
@media(max-width:${piece.mobileMaxW}px) { .collage-chapter.is-reflowed .collage-words { flex-direction:column; align-items:flex-end; } }
@media(prefers-reduced-motion:reduce) { .collage-word { transform:none; }.collage-marquee span { animation:none; }.collage-caption { transition:none; } }
html[data-static-collage] .collage-word { transform:none; } html[data-static-collage] .collage-marquee span { animation:none; }
`;
}
