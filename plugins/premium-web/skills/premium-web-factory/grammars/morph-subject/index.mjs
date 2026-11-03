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
export const css = (piece) => sectionsCss(piece, archetypes);
export const runtime = 'boot.js';
