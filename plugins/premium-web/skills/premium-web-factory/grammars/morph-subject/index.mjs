// Grammar module set: the original renderers and runtime are the default path.
import { indexHtml } from '../../scripts/lib/html.mjs';
import { sectionsCss } from '../../scripts/lib/css.mjs';
import { ARCHETYPES } from '../../archetypes/index.mjs';
import * as hero from './hero.mjs';
const archetypes = { ...ARCHETYPES, hero };
export const html = (piece, env) => {
  const html = indexHtml(piece, { ...env, archetypes });
  return piece.hero ? html.replace('<body class="finish">', `<body class="finish" data-scroll="${piece.scroll.mode}" data-hero-layout="${piece.hero.layout}">`) : html;
};
export const css = (piece) => sectionsCss(piece, archetypes) + (piece.hero ? `
/* Variant editions use drawn plates to interrupt the persistent scene. */
.band:nth-of-type(even) .band-frame { --band-bg:#e5dfcf; }
.band:nth-of-type(even) .band-line { color:#181d1a; }
.band:nth-of-type(even) .band-cap { color:#3d4941; }
.band:nth-of-type(even) .plate { --accent:#697b62; --accent-text:#394936; }
.band-line { font-size:clamp(64px,10vw,160px); max-width:10em; }
.hero[data-layout="stack"] h1 { font-size:clamp(64px,min(9vw,12svh),138px); }
.act-stat .giant-num { font-size:clamp(150px,22vw,340px); }
@media(max-width:${piece.mobileMaxW}px) {
 .band-line { font-size:clamp(48px,13vw,72px); }
 .hero[data-layout="stack"] h1 { font-size:clamp(48px,13vw,76px); }
 .act-stat .giant-num { font-size:clamp(100px,32vw,160px); }
 .hero[data-layout="bleed"] .hero-copy { padding-top:30svh; }
}
` : '');
export const runtime = 'boot.js';
