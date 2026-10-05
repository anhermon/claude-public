// Scroll scene: a sticky stage that plays N beats while its section scrolls past. Works on iOS Safari < 26
// (no scroll-driven CSS needed): IntersectionObserver turns a passive scroll listener on/off, one rAF per frame
// writes --p (0..1 over the whole scene) and data-step (0..N-1) on the section, and fires "scene" events.
// Markup:
//   <section class="scene" data-scene style="--steps:4">        height comes from the step blocks
//     <div class="scene-stage">...visual...</div>                  position: sticky; top: 0; height: 100svh
//     <div class="scene-step"></div> ... x N                       empty scroll spacers, 100svh each (first: margin-top -100svh)
//   Put the beat TEXT inside .scene-stage (absolute, swapped by [data-step]: old beat out in .2s, new beat in .3s after
//   a .2s delay, never overlapping; a true cross-fade double-exposes two headlines mid-frame), not inside the steps: a text block
//   that scrolls with its step crosses the canvas for half of every step (sealref r1 at 390: beat text over particles;
//   Plumb's beats did the same). Scrolling text over a live visual fails motion.md's "no particles over text".
//   </section>
// JS:  el.addEventListener("scene", (e) => e.detail /* {p, step, local} local = 0..1 inside the current step */)
// Reduced motion (or ?rm): no listener; the section gets data-step = last, --p = 1 and class "is-static", so
// CSS must make the final state fully labelled and readable. The stage still renders; nothing moves.
(function () {
  "use strict";
  var rm = matchMedia("(prefers-reduced-motion: reduce)").matches || /[?&]rm\b/.test(location.search);
  document.querySelectorAll("[data-scene]").forEach(function (el) {
    var steps = el.querySelectorAll(".scene-step").length || 1, raf = 0, last = -1;
    function emit(p) {
      var f = p * steps, step = Math.min(steps - 1, Math.floor(f)), local = Math.min(1, f - step);
      el.style.setProperty("--p", p.toFixed(4));
      el.style.setProperty("--local", local.toFixed(4));
      if (step !== last) { el.dataset.step = step; last = step; }
      el.dispatchEvent(new CustomEvent("scene", { detail: { p: p, step: step, local: local } }));
    }
    if (rm) { el.classList.add("is-static"); emit(1); return; }
    function measure() {
      raf = 0;
      var r = el.getBoundingClientRect(), span = Math.max(1, r.height - innerHeight);
      emit(Math.min(1, Math.max(0, -r.top / span)));
    }
    function onScroll() { if (!raf) raf = requestAnimationFrame(measure); }
    new IntersectionObserver(function (es) {
      if (es[0].isIntersecting) { addEventListener("scroll", onScroll, { passive: true }); addEventListener("resize", onScroll); onScroll(); }
      else { removeEventListener("scroll", onScroll); removeEventListener("resize", onScroll); }
    }).observe(el);
    measure();
  });
})();
