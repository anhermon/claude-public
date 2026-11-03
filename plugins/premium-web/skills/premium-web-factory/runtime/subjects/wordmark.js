// The giant wordmark as a canvas texture (drawn with the page's display font) and its screen-fitted placement.
import { clamp } from '../util.js';

export const WORDMARK = { width: 2048, height: 560, fill: 0.94, baselineY: 0.54, weight: 800, planeZ: -6.5, bandMobile: 0.46, widthFrac: 0.94, capsLift: 0.06, bandVhDefault: 30 };
const NDC_SPAN = 2, PCT = 100;

/** NDC y of the wordmark plane centre: the centre of the hero's reserved bottom band (desktop) or the fixed band behind the subject (mobile). */
export function wordBandY(piece, mobile) {
  if (mobile) return WORDMARK.bandMobile;
  const hero = piece.chapters.find((c) => c.archetype === 'hero'), vh = hero?.params?.wordmarkBandVh ?? WORDMARK.bandVhDefault;
  return -1 + ((vh / PCT) * NDC_SPAN) / 2 - WORDMARK.capsLift;
}

export function makeWordmarkTexture(THREE, text, family, { top = '#ffffff', mid = '#9fb8c4', bottom = '#2a4a5a' } = {}) {
  const c = document.createElement('canvas'); c.width = WORDMARK.width; c.height = WORDMARK.height;
  const g = c.getContext('2d');
  g.textAlign = 'center'; g.textBaseline = 'middle';
  try { g.fontStretch = 'expanded'; } catch { /* optional */ }
  const font = (px) => `${WORDMARK.weight} ${px}px "${family}", sans-serif`;
  g.font = font(WORDMARK.height);
  const fit = Math.min(1, (WORDMARK.width * WORDMARK.fill) / g.measureText(text).width);
  g.font = font(Math.floor(WORDMARK.height * fit));
  const gr = g.createLinearGradient(0, 0, 0, WORDMARK.height);
  gr.addColorStop(0, top); gr.addColorStop(0.5, mid); gr.addColorStop(1, bottom);
  g.fillStyle = gr; g.fillText(text, WORDMARK.width / 2, WORDMARK.height * WORDMARK.baselineY);
  const tex = new THREE.CanvasTexture(c); tex.colorSpace = THREE.SRGBColorSpace; tex.anisotropy = 4; tex.needsUpdate = true;
  return tex;
}

/** Fit a unit plane to the viewport width at its depth and park it in the hero band (bottom on desktop, behind the subject on mobile). */
export function placeWordmark(mesh, camera, bandY, vanish = 0) {
  const dist = camera.position.z - WORDMARK.planeZ, halfH = Math.tan((camera.fov * Math.PI) / 360) * dist, halfW = halfH * camera.aspect;
  const w = Math.min(halfW * 2 * WORDMARK.widthFrac, halfH * 2 * (WORDMARK.width / WORDMARK.height) * 1.2);
  mesh.scale.set(w, (w * WORDMARK.height) / WORDMARK.width, 1);
  mesh.position.set(0, bandY * halfH - clamp(vanish) * halfH * 2, WORDMARK.planeZ);
}
