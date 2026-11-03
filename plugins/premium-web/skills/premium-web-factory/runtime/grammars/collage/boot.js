import { MOTION, clamp, damp, wordOffset } from './motion.js';
const STATIC_KEY = 'staticCollage', NORMALIZE_POINTER = 2;
const REFLOW_CLASS = 'is-reflowed';
export function boot(piece, mounts, bespoke) {
  void mounts;
  const root = document.documentElement, media = matchMedia('(prefers-reduced-motion: reduce)'), query = new URLSearchParams(location.search);
  const chapters = [...document.querySelectorAll('[data-collage]')];
  let pointerX = 0, pointerY = 0, x = 0, y = 0, frame = 0, lastTime = 0;
  const reduced = () => media.matches || query.has('rm');
  const desktop = () => innerWidth > piece.mobileMaxW && matchMedia('(pointer:fine)').matches;
  function tick(now) {
    frame = 0;
    const dt = lastTime ? now - lastTime : MOTION.frameMs; lastTime = now;
    x = damp(x, pointerX, dt); y = damp(y, pointerY, dt);
    chapters.forEach((chapter) => {
      const rect = chapter.getBoundingClientRect(), progress = clamp((innerHeight * MOTION.midpoint - rect.top) / Math.max(rect.height, innerHeight));
      chapter.querySelectorAll('[data-word]').forEach((word, index) => {
        const offset = wordOffset(desktop() ? x : 0, progress, index, desktop() ? y : 0);
        word.style.setProperty('--word-x', `${offset.x}px`);
        word.style.setProperty('--word-y', `${offset.y}px`);
        word.style.setProperty('--word-scale', 1 + progress * MOTION.scale * (index % 2 ? -1 : 1));
      });
    });
    if (Math.abs(x - pointerX) + Math.abs(y - pointerY) > MOTION.settle) frame = requestAnimationFrame(tick);
    else lastTime = 0;
  }
  function update() { if (!reduced() && !frame) frame = requestAnimationFrame(tick); }
  function preference() {
    cancelAnimationFrame(frame); frame = 0; lastTime = 0;
    if (reduced()) root.dataset[STATIC_KEY] = ''; else delete root.dataset[STATIC_KEY];
    update();
  }
  addEventListener('pointermove', (event) => { if (!desktop()) return; pointerX = clamp(event.clientX / innerWidth * NORMALIZE_POINTER - 1); pointerY = clamp(event.clientY / innerHeight * NORMALIZE_POINTER - 1); update(); }, { passive:true });
  document.addEventListener('pointerleave', () => { pointerX = pointerY = 0; update(); });
  addEventListener('scroll', update, { passive:true }); addEventListener('resize', preference); media.addEventListener('change', preference);
  document.querySelectorAll('.collage-block').forEach((block) => block.addEventListener('click', () => {
    block.setAttribute('aria-expanded', String(block.getAttribute('aria-expanded') !== 'true'));
    if (!desktop()) block.closest('[data-collage]')?.classList.toggle(REFLOW_CLASS);
    update();
  }));
  addEventListener('pagehide', () => cancelAnimationFrame(frame), { once:true });
  root.classList.remove('is-loading'); root.dataset.gl = 'none'; preference();
  const subject = { live:false, box:() => null };
  window.__piece = { piece, subject, collage:{ update } }; bespoke?.({ piece, subject, root, stage:null, motion:null });
}
