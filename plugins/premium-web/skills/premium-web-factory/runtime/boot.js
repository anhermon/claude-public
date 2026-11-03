// Orchestrator: motion grammar (loader, reveals, cursor), the stage + subject, scroll -> act -> world, archetype mounts, bespoke hook.
// Test flags: ?nogl (poster), ?rm (reduced motion), ?slow (force the governor to degrade).
import { startMotion } from '../../motion/src/motion.js';
import { init as initStage } from '../../gl/src/stage.js';
import { createSubject } from './subjects/index.js';
import { createNullSubject } from './subjects/core.js';
import { createWorlds } from './worlds.js';
import { createActTracker } from './act.js';

const SLOW_BUDGET_MS = 1, LOADER_MIN_S = 1.0, CAMERA = { fov: 40, pos: [0, 0.8, 12.5] }, DISPLAY_LOAD_PX = 100;

export function boot(piece, mounts, bespoke) {
  const qs = new URLSearchParams(location.search), root = document.documentElement;
  const reduced = qs.has('rm') || matchMedia('(prefers-reduced-motion: reduce)').matches;
  const mobile = matchMedia(`(max-width: ${piece.mobileMaxW}px)`).matches || matchMedia('(pointer: coarse)').matches;
  const noGl = qs.has('nogl') || qs.has('savedata') || navigator.connection?.saveData;
  let subject = createNullSubject(piece), worlds = null, stage = null, resolveScene;
  const sceneReady = new Promise((r) => (resolveScene = r));

  const motion = startMotion({
    loader: { type: 'curtain-progress', options: { wordmark: piece.wordmark, minDuration: LOADER_MIN_S, waitFor: [sceneReady, document.fonts.ready] } },
    trigger: 'view', effects: {}, cursor: true, smoothScroll: false,
    onReveal: () => { root.classList.remove('is-loading'); subject.assemble(); },
  }, reduced ? { reduced: true } : {});

  const HIDES_SUBJECT = new Set(['band', 'footer']);   // opaque art plates: the subject rests (shrinks away) instead of peeking around them
  const LONG_SECTION = 1.02, HIDE_AFTER = 0.04, FIT_SHARE = 0.96, FIT_PROBE_PX = 100, FIT_MAX_PX = 420;
  const pastCopyZone = () => {   // mobile: once a section taller than the viewport has scrolled this far, the subject shrinks away so copy never runs under it
    if (!mobile) return false;
    const el = sections()[Math.max(lastChapter, 0)], r = el?.getBoundingClientRect();
    return !!r && r.height > innerHeight * LONG_SECTION && -r.top > innerHeight * HIDE_AFTER;
  };
  const tracker = createActTracker(), sections = () => [...document.querySelectorAll('[data-act]')];
  let controllers = [], lastChapter = -1, shownNav = -1;
  const onScroll = () => {
    subject.setAct(Math.min(tracker.act(), piece.nActs - 1));
    const idx = tracker.chapter(); if (idx !== lastChapter) { controllers[lastChapter]?.leave?.(); lastChapter = idx; controllers[idx]?.enter?.(); worlds?.to(piece.chapters[idx].act); }
    subject.setHide(pastCopyZone() || HIDES_SUBJECT.has(piece.chapters[idx].archetype));
    if (idx === shownNav) return; shownNav = idx;
    document.querySelectorAll('.nav nav a').forEach((l) => l.setAttribute('aria-current', String(l.getAttribute('href') === '#' + piece.chapters[idx].id)));
  };
  const fitWords = () => document.querySelectorAll('[data-fit]').forEach((el) => {   // DOM wordmarks: size the type so the word fills FIT_SHARE of its box whatever the font, stretch or word length
    el.style.fontSize = `${FIT_PROBE_PX}px`;
    const w = el.firstElementChild.getBoundingClientRect().width;
    if (w > 0) el.style.fontSize = `${Math.min(FIT_MAX_PX, (FIT_PROBE_PX * el.clientWidth * FIT_SHARE) / w)}px`;
  });
  const remeasure = () => { fitWords(); tracker.measure(); onScroll(); };
  addEventListener('scroll', onScroll, { passive: true }); addEventListener('resize', remeasure);

  async function run() {
    stage = initStage(document.body, { backdrop: piece.worlds[0], zIndex: -1, fov: CAMERA.fov, cameraPos: CAMERA.pos, portraitShiftY: 0, exposure: 1, dprMax: piece.budgets.dprMax, dprMaxMobile: piece.budgets.dprMaxMobile,
      mobileMaxWidth: piece.mobileMaxW + 1, reduced: reduced || undefined, forceNoGl: !!noGl, budgetMs: qs.has('slow') ? SLOW_BUDGET_MS : piece.budgets.frameMs });
    window.stage = stage;
    if (!noGl) {
      await document.fonts.load(`800 ${DISPLAY_LOAD_PX}px "${piece.fonts.display.family}"`).catch(() => {});
      try { subject = await createSubject(piece, { mobile }); stage.addScene(subject.scene); } catch (e) { console.error('subject failed', e); subject = createNullSubject(piece); }
    }
    const mode = await stage.ready;
    root.dataset.gl = mode === 'poster' ? 'poster' : 'live';
    if (mode === 'poster') subject = createNullSubject(piece);
    else { worlds = createWorlds({ stage, subject, reduced, worlds: piece.worlds }); if (reduced) subject.assemble(); }
    const els = sections();
    controllers = piece.chapters.map((ch, i) => mounts[ch.archetype]?.(els[i], { subject, piece, ch }) || {});
    window.__piece = { piece, subject, stage, motion, controllers };
    remeasure(); lastChapter = -1; shownNav = -1; onScroll();
    try { bespoke?.({ piece, subject, stage, motion, root }); } catch (e) { console.error('bespoke hook failed', e); }
    resolveScene(mode);
  }
  run();
  addEventListener('load', remeasure);
  document.fonts.ready.then(remeasure);
}
