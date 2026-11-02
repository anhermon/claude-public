// Plays svgfig "inview" figures when they scroll into view. Without JS, with reduced motion or in print they are simply visible.
(() => {
  const OFFSET = '0px 0px -10% 0px', THRESHOLD = 0.3;
  const figs = [...document.querySelectorAll('svg[data-fig]')];
  if (!('IntersectionObserver' in window) || matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  const io = new IntersectionObserver((es) => es.forEach((e) => {
    if (!e.isIntersecting) return;
    e.target.classList.add('live'); e.target.classList.remove('pending'); io.unobserve(e.target);
  }), { rootMargin: OFFSET, threshold: THRESHOLD });
  figs.forEach((f) => { f.classList.add('pending'); io.observe(f); });
})();
