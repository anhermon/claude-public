// Scroll-scrubbed media: image sequence (default) or all-intra video, drawn to a canvas. Vanilla ES module, no deps.
// Pair with scrub.sh (produces manifest.json + frames/ + scrub.mp4). init(canvas, options) -> { destroy(), progress() }
export const DEFAULTS = {
  damp: 0.1,            // lerp factor per rAF toward the target frame; 0.08-0.1 (measured from public reference sites, 2026-11; +-0.02)
  sectionSelector: null, // tall element whose scroll range drives progress; defaults to canvas.parentElement.parentElement
  mode: 'sequence',     // 'sequence' | 'video'
  manifest: 'manifest.json',
  video: 'scrub.mp4',
  posterFraction: 0.5,  // frame shown for prefers-reduced-motion (0..1)
  eps: 0.001,           // stop the loop when |target - current| < eps
};

const clamp01 = (v) => Math.min(1, Math.max(0, v));

function coverDraw(ctx, src, sw, sh) {
  const { width: cw, height: ch } = ctx.canvas;
  const s = Math.max(cw / sw, ch / sh);
  ctx.drawImage(src, (cw - sw * s) / 2, (ch - sh * s) / 2, sw * s, sh * s);
}

export async function init(canvas, options = {}) {
  const o = { ...DEFAULTS, ...options };
  const ctx = canvas.getContext('2d');
  const section = o.sectionSelector ? document.querySelector(o.sectionSelector) : canvas.parentElement.parentElement;
  const reduced = o.reduced ?? matchMedia('(prefers-reduced-motion: reduce)').matches;
  const base = o.base ?? '';
  let frames = [], video = null, count = 0, w = 0, h = 0;

  if (o.mode === 'video') {
    video = document.createElement('video');
    Object.assign(video, { src: base + o.video, muted: true, playsInline: true, preload: 'auto' });
    await new Promise((res, rej) => { video.onloadedmetadata = res; video.onerror = () => rej(new Error('video load failed')); });
    w = video.videoWidth; h = video.videoHeight;
  } else {
    const m = await (await fetch(base + o.manifest)).json();
    count = m.frames; w = m.width; h = m.height;
    frames = new Array(count);
    const load = (i) => new Promise((res) => {
      const img = new Image();
      img.onload = () => { frames[i] = img; res(); };
      img.onerror = res;                       // a missing frame falls back to the nearest loaded one
      img.src = base + m.pattern.replace('%04d', String(m.start + i).padStart(4, '0'));
    });
    await load(0); await load(count >> 1);      // first + poster frame before anything else
    Promise.all(Array.from({ length: count }, (_, i) => i).map(load));
  }
  canvas.width = w; canvas.height = h;

  const nearest = (i) => { for (let d = 0; d < count; d++) { const a = frames[i - d] || frames[i + d]; if (a) return a; } return null; };
  const progress = () => {
    const r = section.getBoundingClientRect();
    return clamp01(-r.top / Math.max(1, r.height - innerHeight));
  };
  const draw = (p) => {
    if (video) { if (Math.abs(video.currentTime - p * video.duration) > 1e-3) video.currentTime = p * video.duration; coverDraw(ctx, video, w, h); canvas.dataset.t = video.currentTime.toFixed(3); return; }
    const idx = Math.round(p * (count - 1));
    const img = nearest(idx);
    if (img) coverDraw(ctx, img, w, h);
    canvas.dataset.frame = String(idx);        // exposed for tests and the demo readout
  };

  let cur = reduced ? o.posterFraction : progress(), raf = 0;
  if (video) video.addEventListener('seeked', () => coverDraw(ctx, video, w, h));
  draw(cur);
  if (reduced) return { destroy() {}, progress: () => cur };

  const tick = () => {
    const target = progress();
    cur += (target - cur) * o.damp;
    if (Math.abs(target - cur) < o.eps) cur = target;
    draw(cur);
    raf = requestAnimationFrame(tick);
  };
  raf = requestAnimationFrame(tick);
  return { destroy() { cancelAnimationFrame(raf); }, progress: () => cur };
}
