// gl/fx-canvas: the tiny shared helper under every shader-field module (raw WebGL2, no three.js).
// Fullscreen triangle, readable shader errors, uniforms, DPR cap, offscreen/visibility pause, resize,
// context loss, poster fallback, reduced-motion static frame, optional extra passes (setup/draw hooks).
import { reducedMotion } from './util.js';

export const FX_DEFAULTS = {
  dpr: 2,                    // DPR cap 2 (measured from public reference sites, 2026-11)
  dprMobile: 1.5,            // mobile cap 1.5 (same source)
  mobileMaxWidth: 820,       // px; below this the mobile cap applies
  renderScale: 1,            // internal resolution factor (colour-field blur look renders at 0.15-0.5)
  staticTime: 6,             // s; the frame shown for reduced-motion / ?nogl-less static render
  timeScale: 1,              // multiplies uTime
  clear: [0, 0, 0, 1],       // clear colour before the quad
  autoStart: true,           // false => caller (e.g. a stage tick) calls fx.render(t) itself
  preserveDrawingBuffer: false, // true when the canvas is read as a texture by another renderer
  measure: false,            // true => gl.finish() after each draw and record GPU-inclusive ms (distorts rAF; test only)
  alpha: false,
  antialias: false,
  poster: '',                // CSS `background` value (gradient / url(...)) used when WebGL2 is missing or ?nogl
  noglParam: 'nogl',         // query flag that forces the poster path
  statSamples: 600,
};
const MS_PER_S = 1000;
const MAX_DT_S = 0.1;        // clamp after tab-switch / long frames so time never jumps
const LOG_CONTEXT_LINES = 3;
const HEADER_LINES = 4;      // lines in HEADER below (for error line mapping)
const HEADER = '#version 300 es\nprecision highp float;\nprecision highp int;\nin vec2 vUv; out vec4 fragColor;\n';
const VERT = `#version 300 es
out vec2 vUv;
void main(){ vec2 p = vec2(float((gl_VertexID << 1) & 2), float(gl_VertexID & 2)); vUv = p; gl_Position = vec4(p * 2. - 1., 0., 1.); }`;

const isEl = (x) => typeof Element !== 'undefined' && x instanceof Element;
const resolveEl = (t) => (typeof t === 'string' ? document.querySelector(t) : t);

/** Compile with a readable error: shader type, driver message and the offending source lines. */
function compile(gl, type, src, label, headerLines) {
  const sh = gl.createShader(type);
  gl.shaderSource(sh, src);
  gl.compileShader(sh);
  if (!gl.getShaderParameter(sh, gl.COMPILE_STATUS)) {
    const log = gl.getShaderInfoLog(sh) || 'unknown error';
    const lines = src.split('\n');
    const m = /ERROR:\s*\d+:(\d+)/.exec(log);
    let ctx = '';
    if (m) {
      const n = +m[1];
      ctx = '\n' + lines.slice(Math.max(0, n - 1 - LOG_CONTEXT_LINES), n + LOG_CONTEXT_LINES).map((l, i) => `${Math.max(1, n - LOG_CONTEXT_LINES) + i}${Math.max(1, n - LOG_CONTEXT_LINES) + i === n ? ' >' : '  '} ${l}`).join('\n');
    }
    gl.deleteShader(sh);
    throw new Error(`[fx-canvas] ${label} shader failed to compile (module line = reported - ${headerLines}):\n${log}${ctx}`);
  }
  return sh;
}

/** Program wrapper: cached uniform locations + typed setters. Used for the main quad and for extra passes. */
export function createProgram(gl, vs, fs, label = 'fx', headerLines = 0) {
  const v = compile(gl, gl.VERTEX_SHADER, vs, label + ' vertex', headerLines);
  const f = compile(gl, gl.FRAGMENT_SHADER, fs, label + ' fragment', headerLines);
  const program = gl.createProgram();
  gl.attachShader(program, v); gl.attachShader(program, f);
  gl.linkProgram(program);
  gl.deleteShader(v); gl.deleteShader(f);
  if (!gl.getProgramParameter(program, gl.LINK_STATUS)) {
    const log = gl.getProgramInfoLog(program);
    gl.deleteProgram(program);
    throw new Error(`[fx-canvas] ${label} program failed to link:\n${log}`);
  }
  const info = new Map();
  const n = gl.getProgramParameter(program, gl.ACTIVE_UNIFORMS);
  for (let i = 0; i < n; i++) {
    const u = gl.getActiveUniform(program, i);
    const name = u.name.replace(/\[0\]$/, '');
    info.set(name, { loc: gl.getUniformLocation(program, u.name), type: u.type, size: u.size });
  }
  const api = {
    program, info,
    has: (name) => info.has(name),
    use: () => gl.useProgram(program),
    /** set a uniform (program must be in use). number | bool | number[] | Float32Array */
    set(name, v) {
      const u = info.get(name);
      if (!u) return;
      const arr = typeof v === 'number' ? null : v;
      switch (u.type) {
        case gl.FLOAT: u.size > 1 ? gl.uniform1fv(u.loc, arr) : gl.uniform1f(u.loc, +v); break;
        case gl.FLOAT_VEC2: u.size > 1 ? gl.uniform2fv(u.loc, arr) : gl.uniform2f(u.loc, arr[0], arr[1]); break;
        case gl.FLOAT_VEC3: u.size > 1 ? gl.uniform3fv(u.loc, arr) : gl.uniform3f(u.loc, arr[0], arr[1], arr[2]); break;
        case gl.FLOAT_VEC4: u.size > 1 ? gl.uniform4fv(u.loc, arr) : gl.uniform4f(u.loc, arr[0], arr[1], arr[2], arr[3]); break;
        case gl.INT: case gl.BOOL: case gl.SAMPLER_2D: gl.uniform1i(u.loc, +v); break;
        default: break;
      }
    },
    destroy: () => gl.deleteProgram(program),
  };
  return api;
}

/** Fallback shown when WebGL2 is missing or ?nogl: poster background, same API, no GL. */
function posterOnly(host, o, reason) {
  if (o.poster) host.style.background = o.poster;
  host.classList.add('fx-fallback');
  host.dataset.fxFallback = reason;
  const noop = () => {};
  return { fallback: true, reason, canvas: null, gl: null, set: noop, texture: noop, setTexture: noop, render: noop, resize: noop, pause: noop, resume: noop, frameTimes: () => [], destroy: noop, program: null, stats: { frames: 0 } };
}

/**
 * createFx(target, { frag, ... }) -> fx
 *  frag     : GLSL body appended after the header (declares uniforms/functions + main() writing `fragColor`)
 *  chunks   : GLSL strings (from fx-glsl.js) inserted between header and frag
 *  uniforms : initial uniform values { uName: value }
 *  setup(gl, fx)        : after every (re)build: create extra programs / buffers
 *  update(t, dt, fx)    : per frame before drawing (set uniforms here); t is seconds * timeScale
 *  draw(gl, fx, t)      : after the quad, for extra passes (strands etc.); must restore state it changes
 *  onResize(w, h, fx)   : after the drawing buffer changed size
 * Returns { canvas, gl, set, texture, setTexture, render, resize, pause, resume, destroy, frameTimes, stats, createProgram }.
 */
export function createFx(target, options = {}) {
  const host = resolveEl(target);
  if (!isEl(host)) throw new Error('[fx-canvas] target not found');
  host.__fx && host.__fx.destroy();                          // safe to init twice: replaces, never stacks
  const o = { ...FX_DEFAULTS, ...options };
  const reduced = reducedMotion(o);
  const nogl = new URLSearchParams(location.search).has(o.noglParam) || o.nogl === true;

  const own = host.tagName !== 'CANVAS';
  const canvas = own ? document.createElement('canvas') : host;
  if (nogl) return posterOnly(own ? host : host.parentElement, o, 'nogl');

  const glOpts = { alpha: o.alpha, antialias: o.antialias, powerPreference: 'high-performance', preserveDrawingBuffer: o.preserveDrawingBuffer, premultipliedAlpha: true };
  const gl = canvas.getContext('webgl2', glOpts);
  if (!gl) return posterOnly(own ? host : host.parentElement, o, 'no-webgl2');

  if (own) {
    if (getComputedStyle(host).position === 'static') host.style.position = 'relative';
    Object.assign(canvas.style, { position: 'absolute', inset: '0', width: '100%', height: '100%', display: 'block' });
    canvas.setAttribute('aria-hidden', 'true');
    host.prepend(canvas);
  }
  const posterHost = own ? host : host.parentElement;

  let main = null, vao = null, raf = 0, last = 0, tAcc = 0, visible = true, tabVisible = !document.hidden, dead = false, lost = false;
  let w = 0, h = 0;
  const entries = [];                                       // pending/dirty uniform values
  const byName = new Map();
  const textures = new Map();                               // name -> {tex, unit, source, live, opts}
  const stats = { frames: 0, cpuMs: 0 };
  const times = new Float32Array(o.statSamples);
  const frame = { t: 0 };
  const resArr = new Float32Array(2);

  const fx = {
    canvas, gl, stats, fallback: false, createProgram: (vs, fs, label) => createProgram(gl, vs, fs, label),
    get program() { return main; }, get size() { return [w, h]; },
    /** set a uniform on the main program (applied on the next render) */
    set(name, v) {
      let e = byName.get(name);
      if (!e) { e = { name, v: null, dirty: true }; byName.set(name, e); entries.push(e); }
      e.v = typeof v === 'number' || typeof v === 'boolean' ? +v : v; e.dirty = true;
    },
    /** register a texture sampler uniform. source: img | video | canvas | ImageBitmap. live: re-upload every frame (video/canvas). */
    texture(name, source, opts = {}) {
      const prev = textures.get(name);
      const rec = prev || { name, unit: textures.size, tex: null, opts: {} };
      rec.source = source; rec.opts = { ...rec.opts, ...opts };
      rec.live = opts.live ?? (source instanceof HTMLVideoElement || source instanceof HTMLCanvasElement);
      rec.pending = true;
      textures.set(name, rec);
      if (main && !rec.tex) uploadInit(rec);
      this.set(name, rec.unit);
      if (!raf) requestStatic();
    },
    setTexture(name, source, opts) { this.texture(name, source, opts); },
    /** draw one frame at time t (seconds). Used by the loop, by reduced-motion, and by stage layers. */
    render(t = frame.t, dt = 0) { draw(t, dt); },
    pause() { running(false); },
    resume() { running(true); },
    resize() { measureSize(); },
    frameTimes: () => Array.from(times.subarray(0, Math.min(stats.frames, times.length))),
    destroy,
  };

  /* ---------- build / rebuild ---------- */
  function build() {
    const src = HEADER + (o.chunks || []).join('\n') + '\n' + o.frag;
    main = createProgram(gl, VERT, src, o.label || 'fx', HEADER_LINES);
    vao = gl.createVertexArray();
    for (const e of entries) e.dirty = true;
    for (const rec of textures.values()) { rec.tex = null; uploadInit(rec); }
    gl.clearColor(...o.clear);
    o.setup && o.setup(gl, fx);
  }
  function uploadInit(rec) {
    rec.tex = gl.createTexture();
    gl.activeTexture(gl.TEXTURE0 + rec.unit);
    gl.bindTexture(gl.TEXTURE_2D, rec.tex);
    const wrap = rec.opts.wrap === 'repeat' ? gl.REPEAT : gl.CLAMP_TO_EDGE;
    const filt = rec.opts.filter === 'nearest' ? gl.NEAREST : gl.LINEAR;
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, wrap);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, wrap);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, filt);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, filt);
    gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, 1, 1, 0, gl.RGBA, gl.UNSIGNED_BYTE, new Uint8Array([0, 0, 0, 255]));
    rec.pending = true;
  }
  function sourceReady(s) {
    if (s instanceof HTMLVideoElement) return s.readyState >= s.HAVE_CURRENT_DATA && s.videoWidth > 0;
    if (s instanceof HTMLImageElement) return s.complete && s.naturalWidth > 0;
    return true;
  }
  function uploadTex(rec) {
    if (!rec.tex || !rec.source || !sourceReady(rec.source)) return;
    if (!rec.live && !rec.pending) return;
    gl.activeTexture(gl.TEXTURE0 + rec.unit);
    gl.bindTexture(gl.TEXTURE_2D, rec.tex);
    gl.pixelStorei(gl.UNPACK_FLIP_Y_WEBGL, rec.opts.flipY !== false);
    gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, rec.source);
    rec.pending = false;
    rec.ready = true;
  }

  /* ---------- size ---------- */
  function effectiveDpr() {
    const cap = innerWidth <= o.mobileMaxWidth ? o.dprMobile : o.dpr;
    return Math.min(window.devicePixelRatio || 1, cap);
  }
  function measureSize() {
    const r = host.getBoundingClientRect();
    const s = effectiveDpr() * o.renderScale;
    const nw = Math.max(1, Math.round((own ? r.width : canvas.clientWidth) * s)), nh = Math.max(1, Math.round((own ? r.height : canvas.clientHeight) * s));
    if (nw === w && nh === h) return;
    w = canvas.width = nw; h = canvas.height = nh;
    o.onResize && o.onResize(w, h, fx);
    if (!raf) requestStatic();
  }

  /* ---------- draw ---------- */
  function draw(t, dt) {
    if (lost || !main || dead) return;
    const c0 = o.measure ? performance.now() : 0;
    o.update && o.update(t, dt, fx);
    gl.viewport(0, 0, w, h);
    main.use();
    resArr[0] = w; resArr[1] = h;
    main.set('uTime', t); main.set('uRes', resArr);
    for (const rec of textures.values()) uploadTex(rec);
    for (const e of entries) if (e.dirty) { main.set(e.name, e.v); e.dirty = false; }
    gl.disable(gl.BLEND);
    gl.clear(gl.COLOR_BUFFER_BIT);
    gl.bindVertexArray(vao);
    gl.drawArrays(gl.TRIANGLES, 0, 3);
    if (o.draw) { o.draw(gl, fx, t); gl.disable(gl.BLEND); }
    if (o.measure) { gl.finish(); times[stats.frames % times.length] = performance.now() - c0; }
    stats.frames++;
    frame.t = t;
  }
  const requestStatic = () => {                              // reduced-motion / paused: one frame, no loop
    if (dead || raf || staticQueued) return;
    staticQueued = true;
    requestAnimationFrame(() => { staticQueued = false; if (!raf) draw(reduced ? o.staticTime : frame.t, 0); });
  };
  let staticQueued = false;

  function tick(now) {
    raf = requestAnimationFrame(tick);
    const dt = Math.min(MAX_DT_S, last ? (now - last) / MS_PER_S : 0);
    last = now;
    tAcc += dt * o.timeScale;
    draw(tAcc + (o.startTime || 0), dt);
  }
  function running(on) {
    const want = on && !reduced && visible && tabVisible && !dead && !lost;
    if (want && !raf) { last = 0; raf = requestAnimationFrame(tick); }
    else if (!want && raf) { cancelAnimationFrame(raf); raf = 0; }
  }

  /* ---------- observers + context events ---------- */
  const ro = new ResizeObserver(() => { measureSize(); });
  ro.observe(own ? host : canvas);
  const io = new IntersectionObserver((es) => { visible = es[es.length - 1].isIntersecting; if (o.autoStart) running(true); });
  io.observe(host);
  const onVis = () => { tabVisible = !document.hidden; if (o.autoStart) running(true); };
  const onLost = (e) => { e.preventDefault(); lost = true; running(false); };
  const onRestored = () => { lost = false; try { build(); measureSize(); } catch (err) { console.error(err); } w = 0; measureSize(); if (o.autoStart) running(true); requestStatic(); };
  document.addEventListener('visibilitychange', onVis);
  canvas.addEventListener('webglcontextlost', onLost);
  canvas.addEventListener('webglcontextrestored', onRestored);

  function destroy() {
    if (dead) return;
    dead = true;
    running(false);
    ro.disconnect(); io.disconnect();
    document.removeEventListener('visibilitychange', onVis);
    canvas.removeEventListener('webglcontextlost', onLost);
    canvas.removeEventListener('webglcontextrestored', onRestored);
    o.dispose && o.dispose(gl, fx);
    for (const rec of textures.values()) rec.tex && gl.deleteTexture(rec.tex);
    textures.clear();
    main && main.destroy();
    vao && gl.deleteVertexArray(vao);
    const ext = gl.getExtension('WEBGL_lose_context');
    ext && ext.loseContext();
    if (own) canvas.remove();
    if (host.__fx === fx) delete host.__fx;
  }

  try { build(); } catch (err) {
    console.error(err);
    destroy();
    return posterOnly(posterHost, o, 'shader-error');
  }
  for (const [k, v] of Object.entries(o.uniforms || {})) fx.set(k, v);
  measureSize();
  host.__fx = fx;
  if (o.autoStart) running(true);
  requestStatic();
  return fx;
}
