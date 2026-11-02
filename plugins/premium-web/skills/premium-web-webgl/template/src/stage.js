// gl/stage: one fixed full-viewport canvas behind scrolling DOM. Scenes register on it; it owns the
// renderer, camera, scroll-progress uniform, DPR cap, visibility pause, context loss, poster fallback
// (no WebGL / ?nogl / reduced-motion) and a render-budget governor. Technique: measured from public reference sites, 2026-11.
import { loadThree, clamp, resolveEl } from './util.js';
import { createBackdrop, backdropToCss, FIRE } from './backdrop.js';
import { reducedMotion } from './util.js';

const DEFAULTS = {
  dprMax: 2,              // DPR cap 2 (measured from public reference sites, 2026-11)
  dprMaxMobile: 1.5,      // mobile cap 1.5 (same source)
  mobileMaxWidth: 768,    // px; below this (or coarse pointer) counts as mobile
  budgetMs: 22,           // governor threshold: median frame above this degrades quality (~45 fps floor)
  budgetWindow: 40,       // frames per governor decision
  warmupFrames: 40,       // ignored while shaders compile
  dprStep: 0.8,           // DPR multiplier per degrade step
  dprMinAbs: 0.75,        // never render below this device-pixel ratio
  countStep: 0.25,        // point-count fraction removed per degrade step once DPR is at the floor
  countMin: 0.4,
  maxFrameGapS: 0.25,     // dt above this = tab was hidden; treated as one 60 Hz frame
  scrollLerp: 0.08,       // own damped progress when no `scroll` is supplied (damped scrub 0.08-0.1 per 60 Hz frame; same source)
  fov: 40, near: 0.1, far: 200,
  cameraPos: [0, 0, 12],
  portraitShiftY: 0.22,   // authored: fraction of viewport height the scene is pushed down in portrait (clears a stacked headline)
  exposure: 1,
  zIndex: 0,              // content must be position:relative to sit above; use -1 for drop-in behind
  fixed: true,            // false = absolutely fill `target` instead of the viewport
  backdrop: FIRE,         // floor-glow palette (see backdrop.js)
  poster: null,           // CSS background value or an Element; default derives from `backdrop`
  posterFadeMs: 500,
  governor: true,
  frameLog: 900,          // frame-time ring buffer length (tests read p50/p99)
};
const STATE_ATTR = 'glMode';
const NOGL_RE = /[?&]nogl(=|&|$)/;
const REF_FRAME_S = 1 / 60;

function probeWebGL() {
  try {
    const c = document.createElement('canvas');
    const g = c.getContext('webgl2') || c.getContext('webgl');
    if (!g) return false;
    g.getExtension('WEBGL_lose_context')?.loseContext();
    return true;
  } catch { return false; }
}

export function init(target, options = {}) {
  const host = resolveEl(target);
  if (host.__glStage) { host.__glStage.update(options); return host.__glStage; }
  const o = { ...DEFAULTS, ...options };
  const reduced = reducedMotion(o);
  const forceNoGl = o.forceNoGl ?? NOGL_RE.test(location.search);
  const posterGiven = o.poster != null;

  // ---- DOM
  const root = document.createElement('div');
  root.className = 'gl-stage';
  Object.assign(root.style, { position: o.fixed ? 'fixed' : 'absolute', inset: '0', zIndex: String(o.zIndex), pointerEvents: 'none', overflow: 'hidden' });
  root.setAttribute('aria-hidden', 'true');
  const poster = document.createElement('div');
  poster.className = 'gl-stage-poster';
  Object.assign(poster.style, { position: 'absolute', inset: '0', transition: `opacity ${o.posterFadeMs}ms ease`, backgroundSize: 'cover' });
  if (o.poster instanceof Element) poster.append(o.poster);
  else poster.style.background = o.poster || backdropToCss(o.backdrop);
  const canvas = document.createElement('canvas');
  Object.assign(canvas.style, { position: 'absolute', inset: '0', width: '100%', height: '100%', display: 'block' });
  root.append(poster, canvas);
  host.append(root);

  // ---- state
  const ctx = {
    THREE: null, renderer: null, scene: null, camera: null, stage: null,
    size: { w: 1, h: 1 }, dpr: 1, time: 0, dt: 0, progress: 0, velocity: 0, reduced, mobile: false,
    pointer: { x: 0, y: 0, moved: false },
    quality: { count: 1, dprScale: 1 },
    uniforms: null,
  };
  let mode = 'pending';          // pending | gl | static | poster
  let backdrop = null, raf = 0, last = 0, lost = false, inView = true, dead = false, firstFrame = false, manual = null;
  let ownTarget = 0, prevProgress = 0, needsRender = false, warm = 0, win = 0, degrades = 0, governorOn = o.governor;
  const scenes = [], hooks = new Set(), offs = [];
  const winBuf = new Float32Array(o.budgetWindow), winSort = new Float32Array(o.budgetWindow);
  const log = new Float32Array(o.frameLog); let logN = 0;
  let resolveReady; const ready = new Promise((r) => (resolveReady = r));

  const setMode = (m) => { mode = m; root.dataset[STATE_ATTR] = m; };
  const showPoster = (on) => { poster.style.opacity = on ? '1' : '0'; };
  const isMobile = () => matchMedia('(pointer: coarse)').matches || innerWidth < o.mobileMaxWidth;

  // ---- progress / pointer
  const ownProgress = () => { const m = document.documentElement.scrollHeight - innerHeight; return m > 0 ? clamp(scrollY / m) : 0; };
  const srcProgress = () => (manual != null ? manual : o.scroll ? (typeof o.scroll.progress === 'function' ? o.scroll.progress() : o.scroll.progress) : null);
  function updateProgress(dt) {
    const s = srcProgress();
    if (s != null) ctx.progress = s;
    else {
      ownTarget = ownProgress();
      ctx.progress += (ownTarget - ctx.progress) * (reduced ? 1 : 1 - Math.pow(1 - o.scrollLerp, dt / REF_FRAME_S));
    }
    ctx.velocity = dt > 0 ? (ctx.progress - prevProgress) / dt : 0;
    prevProgress = ctx.progress;
    ctx.uniforms.uProgress.value = ctx.progress;
  }
  const onPointer = (e) => { ctx.pointer.x = (e.clientX / innerWidth) * 2 - 1; ctx.pointer.y = -((e.clientY / innerHeight) * 2 - 1); ctx.pointer.moved = true; };

  // ---- sizing / quality
  function effectiveDpr() {
    const cap = ctx.mobile ? o.dprMaxMobile : o.dprMax;
    return Math.max(o.dprMinAbs, Math.min(devicePixelRatio || 1, cap) * ctx.quality.dprScale);
  }
  function resize() {
    if (!ctx.renderer) return;
    const w = Math.max(1, root.clientWidth), h = Math.max(1, root.clientHeight);
    ctx.mobile = isMobile();
    ctx.dpr = effectiveDpr();
    ctx.renderer.setPixelRatio(ctx.dpr);
    ctx.renderer.setSize(w, h, false);
    ctx.size.w = w; ctx.size.h = h;
    ctx.camera.aspect = w / h;
    // portrait: shift the whole scene down so the subject clears a headline stacked above it
    if (w < h && o.portraitShiftY > 0) ctx.camera.setViewOffset(w, h, 0, -o.portraitShiftY * h, w, h);
    else ctx.camera.clearViewOffset();
    ctx.camera.updateProjectionMatrix();
    for (const s of scenes) s.scene.resize?.(ctx);
    needsRender = true;
  }
  function applyQuality() { for (const s of scenes) s.scene.setQuality?.(ctx.quality, ctx); resize(); }
  function degrade() {
    const floorDpr = Math.max(o.dprMinAbs, 0) / Math.min(devicePixelRatio || 1, ctx.mobile ? o.dprMaxMobile : o.dprMax);
    if (ctx.quality.dprScale > floorDpr + 1e-3) ctx.quality.dprScale = Math.max(floorDpr, ctx.quality.dprScale * o.dprStep);
    else if (ctx.quality.count > o.countMin) ctx.quality.count = Math.max(o.countMin, ctx.quality.count - o.countStep);
    else return;
    degrades++; warm = Math.floor(o.warmupFrames / 2); win = 0;
    applyQuality();
  }
  function govern(ms) {
    if (!governorOn) return;
    if (warm < o.warmupFrames) { warm++; return; }
    winBuf[win++] = ms;
    if (win < o.budgetWindow) return;
    win = 0; winSort.set(winBuf); winSort.sort();
    if (winSort[o.budgetWindow >> 1] > o.budgetMs) degrade();
  }

  // ---- frame
  function render(dt) {
    ctx.dt = dt; ctx.time += dt;
    updateProgress(dt);
    backdrop.update(ctx);
    for (const h of hooks) h(ctx);
    const p = ctx.progress;
    for (const s of scenes) {
      const r = s.range, vis = !r || (p >= r[0] && p <= r[1]);
      if (s.scene.root) s.scene.root.visible = vis;
      if (vis) s.scene.update?.(ctx);
    }
    ctx.renderer.render(ctx.scene, ctx.camera);
    if (!firstFrame) { firstFrame = true; showPoster(false); }
    needsRender = false;
  }
  function frame(now) {
    raf = requestAnimationFrame(frame);
    let dt = (now - last) / 1000; last = now;
    if (dt > o.maxFrameGapS || dt <= 0) dt = REF_FRAME_S;
    render(dt);
    const ms = dt * 1000;
    log[logN++ % o.frameLog] = ms;
    govern(ms);
  }
  const shouldRun = () => mode === 'gl' && inView && !document.hidden && !lost && !dead;
  function sync() {
    if (shouldRun()) { if (!raf) { last = performance.now(); raf = requestAnimationFrame(frame); } }
    else if (raf) { cancelAnimationFrame(raf); raf = 0; }
  }
  function requestRender() {   // reduced-motion static mode: one frame on demand, no loop
    if (mode !== 'static' || needsRender === 'q' || lost) return;
    needsRender = 'q';
    requestAnimationFrame(() => { if (!dead && mode === 'static') render(0); });
  }

  // ---- scenes / hooks
  function attach(entry) {
    if (!ctx.THREE || entry.ready) return;
    entry.scene.init(ctx);
    if (entry.scene.root) ctx.scene.add(entry.scene.root);
    entry.scene.setQuality?.(ctx.quality, ctx);
    entry.scene.resize?.(ctx);
    entry.ready = true;
  }
  function detach(entry) {
    if (entry.ready && entry.scene.root) ctx.scene.remove(entry.scene.root);
    entry.scene.dispose?.(ctx);
  }

  // ---- boot
  async function boot() {
    if (forceNoGl || !probeWebGL() || (reduced && posterGiven)) { setMode('poster'); showPoster(true); canvas.style.display = 'none'; resolveReady(mode); return; }
    showPoster(true);
    let THREE;
    try { THREE = await loadThree(); } catch (e) { setMode('poster'); canvas.style.display = 'none'; resolveReady(mode); return; }
    if (dead) return;
    let renderer;
    try { renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: false, powerPreference: 'high-performance' }); }
    catch { setMode('poster'); canvas.style.display = 'none'; resolveReady(mode); return; }
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = o.exposure;
    renderer.outputColorSpace = THREE.SRGBColorSpace;
    ctx.THREE = THREE; ctx.renderer = renderer; ctx.scene = new THREE.Scene();
    ctx.camera = new THREE.PerspectiveCamera(o.fov, 1, o.near, o.far);
    ctx.camera.position.set(...o.cameraPos);
    ctx.uniforms = { uProgress: { value: 0 }, uTime: { value: 0 }, uTint: { value: 0 } };
    backdrop = createBackdrop(THREE, o.backdrop, { palette2: o.backdrop2 || null });
    ctx.scene.add(backdrop.mesh);
    ctx.backdrop = backdrop;
    ctx.mobile = isMobile();
    setMode(reduced ? 'static' : 'gl');
    resize();
    for (const s of scenes) attach(s);
    const ro = new ResizeObserver(() => { resize(); requestRender(); });
    ro.observe(root); offs.push(() => ro.disconnect());
    const io = new IntersectionObserver((es) => { inView = es[es.length - 1].isIntersecting; sync(); });
    io.observe(root); offs.push(() => io.disconnect());
    if (o.scroll?.on) offs.push(o.scroll.on(requestRender));
    addEventListener('scroll', requestRender, { passive: true }); offs.push(() => removeEventListener('scroll', requestRender));
    if (!reduced) { addEventListener('pointermove', onPointer, { passive: true }); offs.push(() => removeEventListener('pointermove', onPointer)); }
    const onVis = () => { last = performance.now(); sync(); };
    document.addEventListener('visibilitychange', onVis); offs.push(() => document.removeEventListener('visibilitychange', onVis));
    const onLost = (e) => { e.preventDefault(); lost = true; showPoster(true); sync(); };
    const onRestored = () => { lost = false; for (const s of scenes) s.scene.restore?.(ctx); showPoster(false); sync(); requestRender(); };
    canvas.addEventListener('webglcontextlost', onLost); canvas.addEventListener('webglcontextrestored', onRestored);
    offs.push(() => { canvas.removeEventListener('webglcontextlost', onLost); canvas.removeEventListener('webglcontextrestored', onRestored); });
    if (mode === 'static') requestRender(); else sync();
    resolveReady(mode);
  }
  boot();

  // ---- public api
  const api = {
    ready, canvas, root, ctx,
    get mode() { return mode; },
    get THREE() { return ctx.THREE; },
    get uniforms() { return ctx.uniforms; },
    get camera() { return ctx.camera; },
    get backdrop() { return backdrop; },
    /** add a scene { root?, init(ctx), update?(ctx), resize?, setQuality?({count,dprScale}), restore?, dispose? }; range [p0,p1] gates it by progress */
    addScene(scene, { range = null } = {}) {
      const entry = { scene, range, ready: false };
      scenes.push(entry); attach(entry);
      return () => { const i = scenes.indexOf(entry); if (i >= 0) { scenes.splice(i, 1); detach(entry); } };
    },
    /** per-frame hook (runs before scenes; used by scroll-camera-keys). Returns an unsubscribe. */
    onFrame(fn) { hooks.add(fn); return () => hooks.delete(fn); },
    setProgress(p) { manual = p; requestRender(); },       // null returns control to scroll
    setBackdrop(p, p2 = null) { backdrop?.setPalette(p, p2); if (!(o.poster instanceof Element)) poster.style.background = backdropToCss(p); requestRender(); },
    pause() { inView = false; sync(); }, resume() { inView = true; sync(); },
    update(opts = {}) {
      if (opts.governor != null) governorOn = opts.governor;
      if (opts.budgetMs != null) o.budgetMs = opts.budgetMs;
      if (opts.backdrop) api.setBackdrop(opts.backdrop);
      if (opts.dprMax != null) { o.dprMax = opts.dprMax; resize(); }
    },
    /** frame-time stats from the ring buffer (tests record these) */
    stats() {
      const n = Math.min(logN, o.frameLog), a = Array.from(log.subarray(0, n)).sort((x, y) => x - y);
      const q = (f) => (n ? a[Math.min(n - 1, Math.floor(f * n))] : 0);
      return { mode, frames: logN, p50: q(0.5), p99: q(0.99), dpr: ctx.dpr, quality: { ...ctx.quality }, degrades, running: !!raf };
    },
    resetStats() { logN = 0; },
    destroy() {
      if (dead) return;
      dead = true; sync();
      offs.forEach((f) => f()); offs.length = 0; hooks.clear();
      scenes.splice(0).forEach(detach);
      backdrop?.dispose();
      if (ctx.renderer) { ctx.renderer.dispose(); ctx.renderer.forceContextLoss(); }
      root.remove(); delete host.__glStage;
    },
  };
  ctx.stage = api;
  host.__glStage = api;
  return api;
}
