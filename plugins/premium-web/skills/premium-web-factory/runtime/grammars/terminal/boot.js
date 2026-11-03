import { TYPE_MS, GLITCH_MS, CLOCK_MS, SESSION_STATE, characterCount, sessionIndex } from './session.js';

const GLITCH_CLASS = 'is-glitching', STATIC_KEY = 'staticSession';
const inert = () => {};
export function boot(piece, mounts, bespoke) {
  const root = document.documentElement, media = matchMedia('(prefers-reduced-motion: reduce)');
  const query = new URLSearchParams(location.search), sections = [...document.querySelectorAll('[data-session]')];
  const subject = { live:false, M:1, setCustom:inert, setHover:inert, setDrive:inert, box:() => null };
  const controllers = piece.chapters.map((ch) => mounts[ch.archetype]?.(document.getElementById(ch.id), { piece, ch, subject }));
  let active = -1, start = 0, frame = 0, glitchTimer = 0;
  const reduced = () => media.matches || query.has('rm');
  function show(index, count) {
    const section = sections[index], entry = piece.terminal.session[index], complete = count >= entry.cmd.length;
    section.querySelector('[data-command]').textContent = entry.cmd.slice(0, count);
    section.querySelector('[data-output]').textContent = complete ? entry.output.join('\n') : '';
    section.querySelector('[data-session-state]').textContent = complete ? SESSION_STATE.complete : SESSION_STATE.typing;
  }
  function tick(now) {
    frame = 0;
    const length = piece.terminal.session[active].cmd.length, count = characterCount(now - start, length);
    show(active, count);
    if (count < length) frame = requestAnimationFrame(tick);
  }
  function update() {
    const index = sessionIndex(sections.map((section) => section.getBoundingClientRect().top), innerHeight);
    if (index === active) return;
    cancelAnimationFrame(frame); clearTimeout(glitchTimer);
    sections.forEach((section, i) => { section.querySelector('.terminal-window').classList.remove(GLITCH_CLASS); show(i, piece.terminal.session[i].cmd.length); });
    active = index;
    if (reduced()) return;
    const window = sections[active].querySelector('.terminal-window');
    window.classList.add(GLITCH_CLASS);
    glitchTimer = setTimeout(() => window.classList.remove(GLITCH_CLASS), GLITCH_MS);
    start = performance.now(); show(active, 0); frame = requestAnimationFrame(tick);
  }
  function preference() {
    cancelAnimationFrame(frame); active = -1;
    if (reduced()) root.dataset[STATIC_KEY] = ''; else delete root.dataset[STATIC_KEY];
    update();
  }
  const clocks = [...document.querySelectorAll('[data-clock]')];
  function clock() {
    if (document.hidden) return;
    const now = new Date(), time = now.toLocaleTimeString('en-GB', { hour12:false });
    clocks.forEach((el) => { el.textContent = time; el.dateTime = now.toISOString(); });
  }
  const clockTimer = setInterval(clock, CLOCK_MS); clock();
  addEventListener('scroll', update, { passive:true }); addEventListener('resize', update);
  document.addEventListener('visibilitychange', clock); media.addEventListener('change', preference);
  addEventListener('pagehide', () => { cancelAnimationFrame(frame); clearInterval(clockTimer); clearTimeout(glitchTimer); }, { once:true });
  root.classList.remove('is-loading'); root.dataset.gl = 'none'; preference();
  window.__piece = { piece, subject, controllers, terminal:{ get active() { return active; }, typeMs:TYPE_MS } };
  bespoke?.({ piece, subject, root, stage:null, motion:null });
}
