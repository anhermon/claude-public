// Hero light strands: raw WebGL1, no library (~4KB). A bundle of thin additive lines flows along a bezier path
// over a static poster <img>. The poster is the LCP element and the fallback; the canvas only fades in after its
// first good frame (html[data-hero="gl"]).
// Markup: <div class="hero-media"><img class="poster" ...><canvas id="strands" data-path="..." ...></canvas></div>
// Parameters (data-* on the canvas, all optional):
//   data-path    "x0,y0 x1,y1 x2,y2 x3,y3"  cubic bezier in 0..1 canvas space (default: gentle S across the right side)
//   data-count   strands on desktop (default 420); data-count-touch (default 180)
//   data-spread  bundle half-width in px (default 46); data-seed integer (default 7)
//   data-color   "#7FA2FF" strand colour; data-hot "#FFFFFF" colour of the exposing head
// Falls back to the poster (html[data-hero="poster"]) on: prefers-reduced-motion, Save-Data, no WebGL,
// webglcontextlost, or a slow-frame watchdog (> 60 of the first 90 frames over 24ms: Low Power Mode, weak GPU).
// Test flags in the URL force each path: ?nogl ?rm ?savedata ?slow (adds 30ms of work per frame).
(function () {
  "use strict";
  var doc = document.documentElement, q = new URLSearchParams(location.search);
  var canvas = document.getElementById("strands");
  if (!canvas) return;
  function fail(why) { doc.dataset.hero = "poster"; doc.dataset.heroWhy = why; canvas.remove(); }
  var conn = navigator.connection;
  if (q.has("rm") || matchMedia("(prefers-reduced-motion: reduce)").matches) return fail("reduced-motion");
  if (q.has("savedata") || (conn && conn.saveData)) return fail("save-data");
  var gl = !q.has("nogl") && (canvas.getContext("webgl", { antialias: false, alpha: false, powerPreference: "low-power", premultipliedAlpha: false }));
  if (!gl) return fail("no-webgl");

  var d = canvas.dataset, touch = matchMedia("(pointer: coarse)").matches;
  var P = (d.path || "0.30,0.62 0.52,0.30 0.74,0.80 1.02,0.42").split(" ").map(function (p) { return p.split(",").map(Number); });
  var N = +(touch ? d.countTouch || 180 : d.count || 420), SEG = 80, SPREAD = +(d.spread || 110);
  function hex(h) { h = h.replace("#", ""); return [0, 2, 4].map(function (i) { return parseInt(h.substr(i, 2), 16) / 255; }); }
  // Deterministic per-strand attributes (same seed -> same picture on every device).
  var a = (+d.seed || 7) >>> 0;
  function rnd() { a = (a + 0x6d2b79f5) | 0; var t = Math.imul(a ^ (a >>> 15), 1 | a); t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t; return ((t ^ (t >>> 14)) >>> 0) / 4294967296; }
  // gl.LINES: 2 vertices per segment; attribute = (t, strandSeed, lane offset -1..1)
  var data = new Float32Array(N * SEG * 2 * 3), k = 0;
  for (var s = 0; s < N; s++) {
    var seed = rnd(), lane = (rnd() + rnd() + rnd()) / 1.5 - 1; // roughly gaussian: dense core, soft edges
    for (var i = 0; i < SEG; i++) for (var j = 0; j < 2; j++) { data[k++] = (i + j) / SEG; data[k++] = seed; data[k++] = lane; }
  }
  function sh(type, src) { var o = gl.createShader(type); gl.shaderSource(o, src); gl.compileShader(o); return o; }
  var prog = gl.createProgram();
  gl.attachShader(prog, sh(gl.VERTEX_SHADER, [
    "attribute vec3 a; uniform vec2 uP[4]; uniform vec2 uRes; uniform float uTime, uSpread;",
    "varying float vT, vEdge;",
    "vec2 bez(float t){ float u=1.-t; return u*u*u*uP[0]+3.*u*u*t*uP[1]+3.*u*t*t*uP[2]+t*t*t*uP[3]; }",
    "float h(float n){ return fract(sin(n)*43758.5453); }",
    "float nz(float x){ float i=floor(x), f=fract(x); return mix(h(i),h(i+1.),f*f*(3.-2.*f))*2.-1.; }",
    "void main(){",
    "  float t=a.x, seed=a.y, lane=a.z;",
    "  vec2 p=bez(t)*uRes, q=bez(min(1.,t+.01))*uRes - bez(max(0.,t-.01))*uRes;",
    "  vec2 n=normalize(vec2(-q.y,q.x));",
    "  float bow=sin(t*3.14159)*(.6+.4*sin(seed*40.));",            // bundle swells mid-path
    "  float off=lane*uSpread*bow*(.7+.6*seed) + nz(t*2.+seed*31.)*34.*bow + nz(t*9.+seed*7.)*4. + sin(uTime*.5+seed*6.283)*1.5;",
    "  p+=n*off; vec2 c=p/uRes*2.-1.; gl_Position=vec4(c.x,-c.y,0.,1.);",
    "  vT=t; vEdge=1.-abs(lane);",
    "}"].join("\n")));
  gl.attachShader(prog, sh(gl.FRAGMENT_SHADER, [
    "precision mediump float; uniform float uExpose, uK; uniform vec3 uCol, uHot; varying float vT, vEdge;",
    "void main(){",
    "  if (vT > uExpose) discard;",
    "  float head=exp(-(uExpose-vT)*60.)*(1.-step(.999,uExpose));",
    "  float alpha=smoothstep(0.,.08,vT)*smoothstep(1.,.9,vT)*(.015+.05*vEdge*vEdge)*uK*(1.+head*5.);",
    "  gl_FragColor=vec4(mix(uCol,uHot,head)*alpha,1.);",
    "}"].join("\n")));
  gl.linkProgram(prog);
  if (!gl.getProgramParameter(prog, gl.LINK_STATUS)) return fail("shader");
  gl.useProgram(prog);
  gl.bindBuffer(gl.ARRAY_BUFFER, gl.createBuffer());
  gl.bufferData(gl.ARRAY_BUFFER, data, gl.STATIC_DRAW);
  var loc = gl.getAttribLocation(prog, "a"); gl.enableVertexAttribArray(loc); gl.vertexAttribPointer(loc, 3, gl.FLOAT, false, 0, 0);
  var U = {}; ["uP", "uRes", "uTime", "uSpread", "uExpose", "uCol", "uHot", "uK"].forEach(function (n) { U[n] = gl.getUniformLocation(prog, n); });
  gl.uniform2fv(U.uP, new Float32Array([].concat.apply([], P)));
  gl.uniform1f(U.uK, Math.min(2, 520 / N)); // constant brightness whatever the strand count
  gl.uniform3fv(U.uCol, hex(d.color || "#7FA2FF")); gl.uniform3fv(U.uHot, hex(d.hot || "#FFFFFF"));
  gl.enable(gl.BLEND); gl.blendFunc(gl.ONE, gl.ONE); gl.clearColor(0, 0, 0, 1); // black + additive; canvas uses mix-blend-mode: screen

  var dpr = Math.min(devicePixelRatio || 1, touch ? 1.5 : 2), W = 0, H = 0;
  function size() {
    W = canvas.clientWidth; H = canvas.clientHeight;
    canvas.width = Math.round(W * dpr); canvas.height = Math.round(H * dpr);
    gl.viewport(0, 0, canvas.width, canvas.height);
    gl.uniform2f(U.uRes, W, H); gl.uniform1f(U.uSpread, SPREAD * Math.min(1, W / 900 + 0.35));
  }
  size(); addEventListener("resize", size);

  var raf = 0, t0 = 0, last = 0, frames = 0, slow = 0, visible = true, dead = false, DUR = 2400;
  function frame(now) {
    raf = 0;
    if (dead || !visible || document.hidden) return;
    if (q.has("slow")) { var b = performance.now(); while (performance.now() - b < 30) {} }
    if (!t0) t0 = now;
    if (last && frames < 90) { frames++; if (now - last > 24) slow++; }
    last = now;
    if (frames >= 90 && slow > 60) { dead = true; return fail("slow-frames"); }
    var p = Math.min(1, (now - t0) / DUR);
    gl.uniform1f(U.uExpose, 1 - Math.pow(1 - p, 3));
    gl.uniform1f(U.uTime, now / 1000);
    gl.clear(gl.COLOR_BUFFER_BIT);
    gl.drawArrays(gl.LINES, 0, N * SEG * 2);
    if (!doc.dataset.hero) doc.dataset.hero = "gl"; // first good frame: fade the canvas in
    raf = requestAnimationFrame(frame);
  }
  function kick() { if (!raf && !dead && visible && !document.hidden) raf = requestAnimationFrame(frame); }
  canvas.addEventListener("webglcontextlost", function (e) { e.preventDefault(); dead = true; cancelAnimationFrame(raf); fail("context-lost"); });
  if ("IntersectionObserver" in window) new IntersectionObserver(function (es) { visible = es[0].isIntersecting; kick(); }).observe(canvas);
  document.addEventListener("visibilitychange", function () { last = 0; kick(); });
  kick();
})();
