// index.html from the PIECE config. No LLM, no network: string templates over the archetype renderers.
import { ARCHETYPES } from '../../archetypes/index.mjs';
import { esc } from '../../archetypes/_shared.mjs';

const MARK = (accent) => `<svg viewBox="0 0 24 24" width="22" height="22" aria-hidden="true"><circle cx="12" cy="12" r="9" fill="none" stroke="currentColor" stroke-width="2"/><circle cx="12" cy="12" r="3.4" fill="${accent}"/></svg>`;

export function indexHtml(piece, env) {
  const heroCh = env.hero || piece.chapters[0];
  const nav = (env.navigation || piece.chapters).filter((c) => c.nav).map((c) => `<a href="#${c.id}">${esc(c.nav)}</a>`).join('');
  const cta = (heroCh.copy.ctas || [])[0];
  const body = env.body ?? piece.chapters.map((c) => (env.archetypes || ARCHETYPES)[c.archetype].render(c, piece, env)).join('\n\n');
  const preload = (piece.fontFiles || []).map((f) => `<link rel="preload" href="fonts/${esc(f)}" as="font" type="font/woff2" crossorigin>`).join('\n');
  const bg = piece.worlds[0].base;
  return `<!doctype html>
<html lang="${esc(piece.lang)}" data-world="dark">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>${esc(piece.name)}, a concept page</title>
<meta name="description" content="${esc(piece.concept.description)}">
<meta name="theme-color" content="${bg}">
<meta property="og:title" content="${esc(piece.name)}, a concept page">
<meta property="og:description" content="${esc(piece.concept.description)}">
<link rel="icon" href="data:image/svg+xml,${encodeURIComponent(`<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'><circle cx='12' cy='12' r='9' fill='none' stroke='${piece.palette.accent}' stroke-width='2'/><circle cx='12' cy='12' r='3.4' fill='${piece.palette.accent}'/></svg>`)}">
${preload}
${piece.hasFontCss ? '<link rel="stylesheet" href="fonts/fonts.css">\n' : ''}<link rel="stylesheet" href="css/base.css">
<link rel="stylesheet" href="css/sections.css">
<script>document.documentElement.classList.add('is-loading');setTimeout(function(){document.documentElement.classList.remove('is-loading')},8000);</script>
</head>
<body class="finish">
<a class="skip" href="#main">Skip to content</a>

<header class="nav glass">
  <a class="brand" href="#${heroCh.id}" aria-label="${esc(piece.name)} home">${MARK(piece.palette.accent)}<span>${esc(piece.name)}</span></a>
  <nav aria-label="Primary">${nav}</nav>
  <div class="concept-tag" role="note"><span class="long">${esc(piece.concept.notice)}</span><span class="short">${esc(piece.concept.noticeShort)}</span></div>
  ${cta ? `<a class="btn sm" href="${esc(cta.href)}">${esc(cta.label)}</a>` : ''}
</header>

<main id="main">
${body.replace(/<footer[\s\S]*<\/footer>/, '')}
</main>

${(body.match(/<footer[\s\S]*<\/footer>/) || [''])[0]}

<noscript><style>[data-ck-hidden]{opacity:1!important;filter:none!important}</style></noscript>
<script type="module" src="js/main.js"></script>
</body>
</html>
`;
}
