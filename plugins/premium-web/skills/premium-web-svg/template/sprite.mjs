// icons.json -> one inline sprite. 24 px grid, 1.5 stroke, round caps, colour from currentColor (inherits text colour, no per-icon colours).
//   node sprite.mjs icons.json > sprite.svg      use:  <svg class="icon" aria-hidden="true"><use href="#i-check"/></svg>
// An icon next to text is decorative (aria-hidden); an icon that is the only content of a button needs aria-label on the BUTTON.
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';

export const GRID = 24, STROKE = 1.5, ID_PREFIX = 'i-';
export const ICON_CSS = `.icon{width:1.5em;height:1.5em;fill:none;stroke:currentColor;stroke-width:${STROKE};stroke-linecap:round;stroke-linejoin:round;vertical-align:-.3em}`;

export function sprite(icons) {
  const sym = Object.entries(icons).map(([name, paths]) => `<symbol id="${ID_PREFIX}${name}" viewBox="0 0 ${GRID} ${GRID}">${paths.map((d) => `<path d="${d}"/>`).join('')}</symbol>`).join('');
  return `<svg xmlns="http://www.w3.org/2000/svg" width="0" height="0" style="position:absolute" aria-hidden="true" focusable="false">${sym}</svg>`;
}
if (process.argv[1] === fileURLToPath(import.meta.url)) {
  if (!process.argv[2]) { console.error('usage: node sprite.mjs icons.json'); process.exit(2); }
  process.stdout.write(sprite(JSON.parse(readFileSync(process.argv[2], 'utf8'))) + '\n');
}
