// Scroll reveals + header state. One IntersectionObserver toggles .in; CSS does the motion.
// Why not CSS scroll-driven animations alone: iOS Safari <= 18 lacks animation-timeline (26+ has it),
// and the UA string is frozen, so never UA-sniff; IO works everywhere.
// Markup: <div data-r style="--i:2">  (--i = stagger index, 60ms each). CSS lives in site.css (.js [data-r]).
// Adds class "in" to each revealed element: never use .in as a layout class (sealref r2: a `.in {display:grid}`
// install grid turned every revealed block on the page into two columns).
(function () {
  "use strict";
  var doc = document.documentElement;
  doc.classList.add("js"); // content is visible without JS; hidden-until-revealed only when this runs
  var els = document.querySelectorAll("[data-r]");
  if (!("IntersectionObserver" in window) || matchMedia("(prefers-reduced-motion: reduce)").matches) {
    els.forEach(function (el) { el.classList.add("in"); });
  } else {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) { if (e.isIntersecting) { e.target.classList.add("in"); io.unobserve(e.target); } });
    }, { rootMargin: "0px 0px -10% 0px", threshold: 0.08 });
    els.forEach(function (el) { io.observe(el); });
  }
  // Header gets a solid, blurred background after 8px of scroll (passive listener, rAF-throttled).
  var head = document.querySelector(".top"), ticking = false;
  if (head) {
    var f = function () { ticking = false; head.classList.toggle("solid", scrollY > 8); };
    addEventListener("scroll", function () { if (!ticking) { ticking = true; requestAnimationFrame(f); } }, { passive: true });
    f();
  }
})();
