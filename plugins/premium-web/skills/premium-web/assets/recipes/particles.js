// Particle field for "the data is the brand": thousands of points easing toward targets you set per beat.
// Canvas 2D, typed arrays, no allocation per frame, DPR capped, pauses off-screen, slow-frame watchdog.
//   var pf = particleField(canvas, { n: 4000, colors: ["#111", "#ff3b00"], ease: 0.08 });
//   pf.targets(function (i, t) { t.x = ...; t.y = ...; t.s = 2; t.a = 1; t.c = 0; });  // CSS px in canvas space
//   t.h = height (optional, 0 = square): points become bar segments, so a sparse count (peak 9) can still fill
//   the stage height instead of leaving a tiny chart under empty space (Plumb round 2 lesson).
//   t.d = frames to wait before moving (optional): stagger by target x so a word assembles left to right instead of
//   every point flying at once into a horizontal smear (sealref r6 mid-frame).
//   pf.snap()   jump to targets (reduced motion / first paint);  pf.onfail = function (why) { show poster }
//   pf.overlay = function (ctx, w, h) { axis labels, counts }   drawn after the points every frame
//   pf.at(i) -> {x,y,s,h,a} current position of point i (redraw a hero point above an overlay card)
//   textPoints(lines, font, gap) -> {pts:[x0,y0,x1,y1,...], w, h}: points sampled from text set in `font`, so the
//   field can BE a word (the key, a token). Gap 3 at >=64px type stays legible; use >=1 point per sample, not fewer.
// Returns null (and leaves the canvas empty) when there is no 2D context. Draw cost: ~n fillRect per frame;
// 6000 points measured ~3ms/frame on an M-series Mac in Chrome. Keep n <= 2500 on touch devices.
function particleField(canvas, o) {
  "use strict";
  var ctx = canvas.getContext("2d"); if (!ctx) return null;
  var n = o.n, ease = o.ease || 0.08, colors = o.colors, touch = matchMedia("(pointer: coarse)").matches;
  var dpr = Math.min(devicePixelRatio || 1, touch ? 1.5 : 2), W = 0, H = 0;
  var x = new Float32Array(n), y = new Float32Array(n), s = new Float32Array(n), a = new Float32Array(n), h = new Float32Array(n), th = new Float32Array(n);
  var dl = new Uint16Array(n), tx = new Float32Array(n), ty = new Float32Array(n), ts = new Float32Array(n), ta = new Float32Array(n), c = new Uint8Array(n);
  var t = { x: 0, y: 0, s: 1, h: 0, a: 1, c: 0 }, raf = 0, visible = true, settled = false, frames = 0, slow = 0, last = 0, dead = false;
  var api = { onfail: null, width: function () { return W; }, height: function () { return H; } };
  function size() { W = canvas.clientWidth; H = canvas.clientHeight; canvas.width = Math.round(W * dpr); canvas.height = Math.round(H * dpr); ctx.setTransform(dpr, 0, 0, dpr, 0, 0); settled = false; kick(); }
  api.targets = function (fn) { for (var i = 0; i < n; i++) { t.x = tx[i]; t.y = ty[i]; t.s = ts[i] || 1; t.h = 0; t.d = 0; t.a = ta[i]; t.c = c[i]; fn(i, t); tx[i] = t.x; ty[i] = t.y; ts[i] = t.s; th[i] = t.h || t.s; ta[i] = t.a; c[i] = t.c; dl[i] = t.d || 0; } settled = false; kick(); };
  api.snap = function () { dl.fill(0); x.set(tx); y.set(ty); s.set(ts); h.set(th); a.set(ta); draw(); settled = true; };
  api.redraw = function () { if (settled) draw(); };
  api.at = function (i) { return { x: x[i], y: y[i], s: s[i], h: h[i] || s[i], a: a[i] }; }; // overlay can lift one point above its own drawing
  function draw() {
    ctx.clearRect(0, 0, W, H);
    for (var k = 0; k < colors.length; k++) {
      ctx.fillStyle = colors[k];
      for (var i = 0; i < n; i++) { if (c[i] !== k || a[i] < 0.02) continue; ctx.globalAlpha = a[i]; ctx.fillRect(x[i], y[i], s[i], h[i] || s[i]); }
    }
    ctx.globalAlpha = 1;
    if (api.overlay) api.overlay(ctx, W, H);
  }
  function frame(now) {
    raf = 0; if (dead || !visible || document.hidden) return;
    if (last && frames < 90) { frames++; if (now - last > 24) slow++; }
    last = now;
    if (frames >= 90 && slow > 60) { dead = true; if (api.onfail) api.onfail("slow-frames"); return; }
    var moving = 0;
    for (var i = 0; i < n; i++) {
      if (dl[i]) { dl[i]--; moving++; continue; }
      var dx = tx[i] - x[i], dy = ty[i] - y[i];
      x[i] += dx * ease; y[i] += dy * ease; s[i] += (ts[i] - s[i]) * ease; h[i] += (th[i] - h[i]) * ease; a[i] += (ta[i] - a[i]) * ease;
      if (dx * dx + dy * dy > 0.05) moving++;
    }
    draw();
    if (moving) raf = requestAnimationFrame(frame); else { settled = true; last = 0; }
  }
  function kick() { if (!raf && !dead && visible && !document.hidden && !settled) raf = requestAnimationFrame(frame); }
  if ("IntersectionObserver" in window) new IntersectionObserver(function (es) { visible = es[0].isIntersecting; last = 0; kick(); }).observe(canvas);
  document.addEventListener("visibilitychange", function () { last = 0; kick(); });
  addEventListener("resize", size);
  size();
  return api;
}

function textPoints(lines, font, gap) {
  "use strict";
  var c = document.createElement("canvas").getContext("2d"), size = parseFloat(/(\d+(\.\d+)?)px/.exec(font)[1]), lh = size * 1.12;
  c.font = font;
  var w = Math.ceil(Math.max.apply(null, lines.map(function (l) { return c.measureText(l).width; }))) + 4, h = Math.ceil(lh * lines.length);
  c.canvas.width = w; c.canvas.height = h; c.font = font; c.textBaseline = "top"; c.fillStyle = "#000";
  lines.forEach(function (l, k) { c.fillText(l, 2, k * lh + size * 0.06); });
  var d = c.getImageData(0, 0, w, h).data, pts = [];
  for (var y = 0; y < h; y += gap) for (var x = 0; x < w; x += gap) if (d[(y * w + x) * 4 + 3] > 120) pts.push(x, y);
  return { pts: pts, w: w, h: h };
}
