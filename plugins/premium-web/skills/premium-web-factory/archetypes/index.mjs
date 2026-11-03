// Archetype registry. Each module: { meta, render(chapter, piece, env) -> html, css(piece, chapter) -> css }.
import * as hero from './hero.mjs';
import * as claim from './claim.mjs';
import * as explainer from './explainer.mjs';
import * as band from './band.mjs';
import * as stat from './stat.mjs';
import * as ship from './ship.mjs';
import * as pricing from './pricing.mjs';
import * as faq from './faq.mjs';
import * as footer from './footer.mjs';

export const ARCHETYPES = { hero, claim, explainer, band, stat, ship, pricing, faq, footer };
