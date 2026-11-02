# Icons, favicon, accessibility, optimisation

Authored practice. Verified: sprite renders, inherits `currentColor`, figure aria wiring. NOT run: `svgo`, screen readers.

## Contents
- Icon system
- Favicon
- Accessibility checklist
- Optimisation

## Icon system

One 24 px grid, 1.5 px stroke, round caps and joins, no fills, colour from `currentColor`: `template/icons.json` holds paths,
`sprite.mjs` builds one inline `<svg>` of `<symbol>`s, pages use `<svg class="icon" aria-hidden="true"><use href="#i-name"/></svg>`.
Rules: one family only (never mix outline and filled); icons clarify a label, they do not replace it; no icon-in-a-circle feature
rows; 1.5em size inherits from the text; add new icons on the same grid by hand, not from a pack with a different stroke weight. Inline the sprite
(external `<use href="sprite.svg#i-x">` fails on `file://` and cross-origin).

## Favicon

`template/favicon.svg`: one SVG with an inline `prefers-color-scheme` style so it flips with the browser theme, rounded 32 px square,
one stroke mark from the page's accent. Link it with `<link rel="icon" href="/favicon.svg" type="image/svg+xml">` and also ship a PNG for
Safari/iOS touch icons (generate it from the SVG at build time; do not hand-draw a second one).

## Accessibility checklist

- Meaningful figure: `role="img"`, `<title>` (short name) and `<desc>` (what is learned), `aria-labelledby` pointing at both ids (ids unique per page: the generator prefixes with `id`).
- Decorative graphic: `aria-hidden="true"` and no title. Never both.
- Icon-only button: put `aria-label` on the `<button>`, not on the svg.
- Colour is never the only carrier (accent plus a label or position); 3:1 contrast for strokes, 4.5:1 for text against the real background.
- Text is `<text>`, at least 12 px at displayed size; test at 390 px width.
- Animation respects `prefers-reduced-motion`; nothing flashes more than 3 times a second.
- Long data figures also get the numbers in the surrounding HTML (a table or the paragraph) for readers who skip the graphic.

## Optimisation

- Inline above-the-fold figures (no request, themeable); `<img src=*.svg>` for decorative reuse (no CSS access, no inherited colour).
- Round coordinates to 1-2 decimals (the generator does); remove editor metadata, empty groups and default attributes (`svgo` with `removeViewBox: false`; NOT run here).
- Keep a figure under about 12 KB (the selftest asserts it); many small `<path>`s beat one huge `d` for animation but cost bytes.
- Reuse with `<symbol>`/`<use>` rather than copy-paste; gzip makes repeated markup cheap, repeated geometry less so.
- Set `viewBox` and let CSS size the svg (`width: 100%; height: auto`) so it never overflows a 390 px viewport.
