// The ONE file to edit per project. Effect defaults (with provenance) live in each module's DEFAULTS; override here.
// Markup contract: data-motion="blur-line|mask-line|word-blur|stagger-grid|count-up|scramble|typewriter" on any element;
// data-motion-when="entrance" waits for the loader reveal; data-motion-delay="0.2" adds seconds; data-motion-scrub on word-blur.
export const CONFIG = {
  // Entrance chapter: 'curtain-progress' | 'hole-expand' | 'slab-to-node' | 'none'
  loader: { type: 'curtain-progress', options: { wordmark: 'STUDIO', minDuration: 1.0 } },
  trigger: 'view',                      // default trigger for [data-motion]: 'view' (IntersectionObserver 0.5) | 'load'
  effects: {                            // per-effect overrides; empty = module defaults
    'blur-line': {}, 'mask-line': {}, 'word-blur': {}, 'stagger-grid': {}, 'count-up': {}, 'scramble': {}, 'typewriter': {},
  },
  // Chapters of the pinned stage: ONE palette world per chapter; the hero object/camera follows --stage-p.
  stage: {
    selector: '[data-stage]',
    handoff: 0.7,                       // s palette tween per chapter change
    rail: '[data-rail]',                // horizontal track inside the stage (optional)
    steps: '[data-step]',               // crossfaded step items inside the stage (optional)
    chapters: [
      { id: 'arrival', bg: '#0b0c10', fg: '#f4f1ea', accent: '#7fa2ff' },
      { id: 'method', bg: '#1b1410', fg: '#f4ece2', accent: '#ff9d5c' },
      { id: 'proof', bg: '#eee9df', fg: '#14161a', accent: '#2c4bff' },
    ],
  },
  curtain: { selector: '[data-curtain]', options: {} },          // overlapping panels
  fullbleed: { selector: '[data-fullbleed]', options: { nav: '.nav-island' } },
  cursor: true,
  smoothScroll: true,                   // damped lerp over native scroll (never hijacks)
};
