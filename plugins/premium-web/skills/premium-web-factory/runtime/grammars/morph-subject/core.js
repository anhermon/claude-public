// Selected only for hero/scroll variants; the original core remains byte-identical.
import { createCore as originalCore } from './core-base.js';
export { K_TOP, MORPH, POINTER, createNullSubject } from './core-base.js';

const SHAPE_FIXED = new Set(['orbit', 'static']);
const ORBIT = { yaw: 0.12, dolly: 0.05, rate: 0.7 };
const HERO_PLACES = {
  stack: { desktop: 'bottom', mobile: 'bottom', scale: 1 },
  bleed: { desktop: 'right', mobile: 'top', scale: 1.2 },
  'type-only': { desktop: 'bottom', mobile: 'bottom', scale: 0.6 },
};
const TYPE_AT = [0.65, -0.64], STACK_AT = [0, -0.55];
const STATIC_TIME = 0, STATIC_POINTER = { x: 0, y: 0, moved: false };
const MOBILE_BLEED_SCALE = .72;

export function createCore({ piece, mobile, N }) {
  const mode = piece.scroll?.mode || 'morph', layout = piece.hero?.layout || 'split';
  const targets = piece.chapters.filter((c) => c.hasTarget), first = targets[0];
  const composed = { ...piece, chapters: piece.chapters.map((c) => {
    if (!c.hasTarget) return c;
    const heroPlace = c === first ? HERO_PLACES[layout] : null;
    const place = mode === 'static' ? { ...first.place, ...HERO_PLACES[layout] } : { ...c.place, ...heroPlace };
    if (mobile && layout === 'bleed') place.scale = MOBILE_BLEED_SCALE;
    return { ...c, target: SHAPE_FIXED.has(mode) ? first.target : c.target, place };
  }) };
  const core = originalCore({ piece: composed, mobile, N });
  if (SHAPE_FIXED.has(mode)) core.forms.fill(core.forms[0]);
  if (!mobile && layout === 'type-only') core.keys[0].at = TYPE_AT;
  if (!mobile && layout === 'stack') core.keys[0].at = STACK_AT;
  if (mode === 'static') core.keys.fill(core.keys[0]);
  const frame = core.frame, view = core.view;
  let cameraDistance;
  core.view = (camera) => {
    if (mode === 'orbit') {
      cameraDistance ??= camera.position.length();
      const phase = core.st.act * ORBIT.rate;
      camera.position.x = Math.sin(phase) * cameraDistance * ORBIT.yaw;
      camera.position.z = cameraDistance * (1 + Math.sin(phase) * ORBIT.dolly);
      camera.lookAt(0, 0, 0);
    }
    return view(camera);
  };
  core.frame = (c, v) => {
    const fixed = mode === 'static';
    const result = frame(fixed ? { ...c, time: STATIC_TIME, pointer: STATIC_POINTER, reduced: true } : c, v);
    if (SHAPE_FIXED.has(mode)) { result.i0 = 0; result.t = 0; }
    return result;
  };
  return core;
}
