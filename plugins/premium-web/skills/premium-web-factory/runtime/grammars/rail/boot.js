import { clamp, FRAME_MS, SETTLE_PX, MOTION, travelFor, progressFor, damp, horizontal } from './scroll.js';

const ROOT_PINNED = 'is-pinned', DIGITS = 2, VIEW_MID = 0.5, LETTER_GROUP = 2;
const REST_TRANSFORM = '', FRAME_IDLE = 0, FIGURE_SCALE_MIN = 1 - MOTION.scale;
const MIN_DT_MS = 1;
const inertSubject = () => {
  const nothing = () => {};
  return { live: false, kind: 'none', M: 1, setCustom: nothing, setDrive: nothing, setHover: nothing, box: () => null };
};

export function boot(piece, mounts, bespoke) {
  const root = document.documentElement, rail = document.querySelector('.rail');
  const viewport = rail.querySelector('.rail-viewport'), track = rail.querySelector('.rail-track');
  const panels = [...track.querySelectorAll('[data-panel]')], letters = panels.map((p) => [...p.querySelectorAll('[data-letter]')]);
  const figures = panels.map((p) => p.querySelector('.rail-figure')), count = rail.querySelector('[data-panel-count]');
  const contours = rail.querySelector('[data-contours]'), subject = inertSubject();
  const media = matchMedia('(prefers-reduced-motion: reduce)'), query = new URLSearchParams(location.search);
  const reduced = () => query.has('rm') || media.matches;
  const controllers = piece.chapters.map((ch) => mounts[ch.archetype]?.(document.getElementById(ch.id), { piece, ch, subject }) || {});
  let travel = 0, x = 0, target = 0, pinned = false, frame = FRAME_IDLE, lastTime = 0, worldIndex = -1;
  const worldAt = (index) => {
    if (index === worldIndex) return;
    worldIndex = index;
    const w = piece.worlds[Math.min(index, piece.worlds.length - 1)];
    root.dataset.world = w.light ? 'light' : 'dark';
    root.style.setProperty('--ground', w.base); root.style.setProperty('--accent', w.accent);
    document.querySelectorAll('.nav nav a').forEach((a) => a.setAttribute('aria-current', String(a.hash === '#' + (piece.rail.panels[index]?.id || piece.chapters[index - panels.length]?.id))));
  };
  function paint(velocity = 0) {
    const progress = travel ? x / travel : 0;
    const flowProgress = pinned ? progress : clamp(-rail.getBoundingClientRect().top / Math.max(rail.scrollHeight - innerHeight, innerHeight));
    track.style.transform = pinned ? `translate3d(${-x}px,0,0)` : REST_TRANSFORM;
    viewport.style.setProperty('--rail-progress', progress);
    const index = pinned ? Math.round(progress * (panels.length - 1)) : panels.reduce((cur, p, i) => p.getBoundingClientRect().top < innerHeight * VIEW_MID ? i : cur, 0);
    let active = index;
    piece.chapters.forEach((ch, i) => { if (document.getElementById(ch.id).getBoundingClientRect().top < innerHeight * VIEW_MID) active = panels.length + i; });
    worldAt(active);
    count.textContent = String(index + 1).padStart(DIGITS, '0');
    const v = pinned ? clamp(velocity * MOTION.velocityGain, -piece.rail.params.velocityMax, piece.rail.params.velocityMax) : 0;
    panels.forEach((panel, i) => {
      const distance = pinned ? Math.min(1, Math.abs(i - progress * (panels.length - 1))) : 0;
      if (piece.rail.params.transition === 'wipe') figures[i].style.clipPath = `inset(0 ${distance * MOTION.wipePct}% 0 0)`;
      else figures[i].style.transform = `scale(${Math.max(FIGURE_SCALE_MIN, 1 - distance * MOTION.scale)})`;
      letters[i].forEach((letter, k) => {
        const direction = k % LETTER_GROUP ? 1 : -1;
        letter.style.transform = v ? `translateY(${v * MOTION.shiftPx * direction}px) skewX(${v * MOTION.skewDeg}deg) scaleX(${1 + Math.abs(v) * MOTION.stretch})` : REST_TRANSFORM;
      });
    });
    contours.style.transform = reduced() ? REST_TRANSFORM : `translate(${flowProgress * MOTION.contourShift}px,${-flowProgress * MOTION.contourShift}px)`;
  }
  function tick(now) {
    frame = FRAME_IDLE;
    const before = x, dt = lastTime ? now - lastTime : FRAME_MS; lastTime = now;
    x = damp(x, target, piece.rail.params.damping, dt);
    if (Math.abs(target - x) < SETTLE_PX) x = target;
    paint((x - before) * FRAME_MS / Math.max(dt, MIN_DT_MS));
    if (x !== target) frame = requestAnimationFrame(tick);
    else { lastTime = 0; paint(); }
  }
  function update() {
    target = pinned ? progressFor(rail.getBoundingClientRect().top, travel, piece.rail.params.scrollRatio) * travel : 0;
    if (!frame) frame = requestAnimationFrame(tick);
  }
  function measure() {
    cancelAnimationFrame(frame); frame = FRAME_IDLE; lastTime = 0;
    rail.classList.remove(ROOT_PINNED); rail.style.height = '';
    // Measure the horizontal candidate before deciding: tall copy gets a vertical fallback.
    const candidate = innerWidth > piece.mobileMaxW && !reduced();
    if (candidate) rail.classList.add(ROOT_PINNED);
    const fits = panels.every((p) => p.scrollHeight <= innerHeight);
    pinned = horizontal(innerWidth, piece.mobileMaxW, reduced(), fits);
    rail.classList.toggle(ROOT_PINNED, pinned);
    travel = pinned ? travelFor(track.scrollWidth, innerWidth) : 0;
    rail.style.height = pinned ? `${innerHeight + travel * piece.rail.params.scrollRatio}px` : '';
    x = target = pinned ? progressFor(rail.getBoundingClientRect().top, travel, piece.rail.params.scrollRatio) * travel : 0;
    paint(); update();
  }
  document.querySelectorAll('a[href^="#"]').forEach((a) => a.addEventListener('click', (event) => {
    const i = panels.findIndex((p) => '#' + p.id === a.getAttribute('href'));
    if (!pinned || i < 0) return;
    event.preventDefault();
    const start = rail.getBoundingClientRect().top + scrollY;
    scrollTo({ top: start + Math.min(travel, panels[i].offsetLeft) * piece.rail.params.scrollRatio, behavior: reduced() ? 'instant' : 'smooth' });
    history.replaceState(null, '', a.getAttribute('href'));
  }));
  track.addEventListener('focusin', (event) => {
    if (!pinned) return;
    const index = panels.findIndex((panel) => panel.contains(event.target));
    if (index < 0) return;
    viewport.scrollLeft = 0;
    const start = rail.getBoundingClientRect().top + scrollY;
    scrollTo({ top: start + Math.min(travel, panels[index].offsetLeft) * piece.rail.params.scrollRatio, behavior: 'instant' });
  });
  addEventListener('scroll', update, { passive: true }); addEventListener('resize', measure);
  media.addEventListener('change', measure);
  root.classList.remove('is-loading'); root.dataset.gl = 'none';
  window.__piece = { piece, subject, stage: null, motion: null, controllers, rail: { measure, get pinned() { return pinned; } } };
  measure(); document.fonts.ready.then(measure);
  if (location.hash) {
    const link = [...document.querySelectorAll('a[href^="#"]')].find((a) => a.getAttribute('href') === location.hash);
    link?.click();
  }
  try { bespoke?.({ piece, subject, stage: null, motion: null, root }); } catch (error) { console.error('bespoke hook failed', error); }
}
