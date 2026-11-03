// Generator constants (named, so nothing below is a magic number).
export const FACTORY_VERSION = '1.0.0';
export const MANIFEST_FILE = '.factory-manifest.json';
export const MOBILE_MAX_W_DEFAULT = 820;
export const DEFAULT_BUDGETS = { dprMax: 2, dprMaxMobile: 1.5, frameMs: 22 };
export const WORLD_STOPS = [0, 0.26, 0.55, 0.88];   // glow stop positions: bright core, mid, deep edge, base
export const DEFAULT_PLACE = { desktop: 'right', mobile: 'top', scale: 1, pitch: 0.16, yaw: 0.4 };
export const SUBJECT_DEFAULTS = {
  'glass-lattice': { items: 96, count: 96, seed: 20261101, params: { radius: 0.27, rodRadius: 0.034, ior: 1.75, thickness: 2.4, dust: 7000, tints: ['#ffffff', '#bfeaff', '#d4dcff', '#a9f0e4'], rodsPerNode: 3 } },
  'point-cloud': { items: 64, count: 24000, seed: 20261102, params: { size: 2.1, gain: 0.8, rim: 0.9, lit: '#ffd9a0', shade: '#c0431f', rimColor: '#fff1d6', swirl: 1.2, anchorSize: 7 } },
  'shader-field': { items: 24, count: 24, seed: 20261103, params: { scale: 2.2, warp: 1.5, speed: 0.6, contrast: 1.3, veins: 0.7, refract: 0.045, wells: 0.55 } },
  'custom-module': { items: 64, count: 64, seed: 1, params: {} },
};
// Files copied verbatim from sibling skills at generation time (never duplicated inside the plugin).
export const WEBGL_SRC_FILES = ['stage.js', 'backdrop.js', 'util.js'];
export const THREE_VENDOR = ['three.module.min.js', 'LICENSE-three', 'LICENSES.md'];
export const MOTION_PATCH = {
  file: 'motion.js',
  from: 'const reveal = () => {',
  to: 'const reveal = () => { config.onReveal?.();',
  why: 'the motion template spreads its own onReveal over the loader options; a piece must be able to start the subject assembly when the curtain lifts',
};
export const REDUCED_FLAG = 'rm';
export const GRAMMAR_MORPH = 'morph-subject', GRAMMAR_RAIL = 'rail';
export const HERO_DEFAULTS = { layout: 'split', wordmark: true };
export const SCROLL_DEFAULTS = { mode: 'morph' };
export const READOUT_DEFAULT = 'card';
export const RAIL_DEFAULTS = { damping: 0.12, panelVw: 100, scrollRatio: 1, velocityMax: 1.2, ambientLines: 12, transition: 'scale' };
export const MORPH_MIN_CHAPTERS = 3;
