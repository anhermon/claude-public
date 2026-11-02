// motion.js: reads motion.config.js + data-motion attributes and starts everything. No other wiring needed.
import { createScroll } from './core/scroll.js';
import { reducedMotion } from './core/easing.js';
import { init as blurLine } from './text/blur-line-reveal.js';
import { init as maskLine } from './text/mask-line-rise.js';
import { init as wordBlur } from './text/word-blur-reveal.js';
import { init as staggerGrid } from './text/stagger-grid.js';
import { init as countUp } from './text/count-up-blur.js';
import { init as scramble } from './text/scramble-resolve.js';
import { init as typewriter } from './text/typewriter.js';
import { init as curtainProgress } from './loader/curtain-progress.js';
import { init as holeExpand } from './loader/hole-expand.js';
import { init as slabToNode } from './loader/slab-to-node.js';
import { init as curtainOverlap } from './transition/curtain-overlap.js';
import { pinStage } from './timeline.js';
import { fullbleed } from './fullbleed.js';
import { initCursor } from './cursor.js';

const EFFECTS = { 'blur-line': blurLine, 'mask-line': maskLine, 'word-blur': wordBlur, 'stagger-grid': staggerGrid,
  'count-up': countUp, scramble, typewriter };
const LOADERS = { 'curtain-progress': curtainProgress, 'hole-expand': holeExpand, 'slab-to-node': slabToNode };
const ENTRANCE = 'entrance';

export function startMotion(config, overrides = {}) {
  const reduced = reducedMotion(overrides);
  const scroll = config.smoothScroll ? createScroll({ smooth: true, ...overrides }) : null;
  const entrance = [], insts = [];

  document.querySelectorAll('[data-motion]').forEach((el) => {
    const make = EFFECTS[el.dataset.motion];
    if (!make) { console.warn('motion: unknown effect', el.dataset.motion); return; }
    const waits = el.dataset.motionWhen === ENTRANCE;
    const o = { ...config.effects[el.dataset.motion], trigger: waits ? 'manual' : config.trigger, ...overrides };
    if (el.dataset.motionDelay) o.delay = parseFloat(el.dataset.motionDelay);
    if (el.dataset.motion === 'word-blur' && 'motionScrub' in el.dataset) { o.scroll = scroll; o.trigger = 'manual'; }
    const inst = make(el, o);
    insts.push(inst);
    if (waits) entrance.push(inst);
  });

  const stages = [...document.querySelectorAll(config.stage?.selector || '[data-stage]')].map((el) =>
    pinStage(el, { ...config.stage, ...overrides }));
  const curtains = config.curtain ? [...document.querySelectorAll(config.curtain.selector)].map((el) =>
    curtainOverlap(el, { ...config.curtain.options, ...overrides })) : [];
  const fb = config.fullbleed ? [...document.querySelectorAll(config.fullbleed.selector)].map((el) =>
    fullbleed(el, { ...config.fullbleed.options, trigger: 'manual', ...overrides })) : [];
  const cursor = config.cursor ? initCursor(overrides) : null;

  const reveal = () => { fb.forEach((f) => f.play()); entrance.forEach((i) => i.play()); };
  let loader = null;
  const make = config.loader && LOADERS[config.loader.type];
  if (make) loader = make(document.body, { ...config.loader.options, onReveal: reveal, ...(reduced ? { reduced: true } : {}), ...overrides });
  else reveal();

  return { scroll, loader, stages, curtains, insts, destroy() {
    [...insts, ...stages, ...curtains, ...fb].forEach((i) => i.destroy?.());
    loader?.destroy?.(); cursor?.destroy(); scroll?.destroy();
  } };
}
