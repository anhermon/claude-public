// Scroll -> act: linear between section centres (the hero counts from 30% of its height), so the subject morphs continuously.
const HERO_ANCHOR = 0.3, MID_ANCHOR = 0.5, VIEW_MID = 0.5;

export function createActTracker() {
  let marks = [], sections = [];
  return {
    measure() {
      sections = [...document.querySelectorAll('[data-act]')];
      marks = sections.map((el) => {
        const r = el.getBoundingClientRect(), top = r.top + scrollY, hero = el.classList.contains('hero');
        return { a: +el.dataset.act, y: top + (hero ? Math.min(r.height, innerHeight) * HERO_ANCHOR : r.height * MID_ANCHOR) };
      });
    },
    act() {
      const mid = scrollY + innerHeight * VIEW_MID;
      if (!marks.length || mid <= marks[0].y) return 0;
      for (let i = 0; i < marks.length - 1; i++) {
        if (mid < marks[i + 1].y) { const m0 = marks[i], m1 = marks[i + 1]; return m0.a + ((mid - m0.y) / (m1.y - m0.y || 1)) * (m1.a - m0.a); }
      }
      return marks[marks.length - 1].a;
    },
    /** index (into the data-act section list) of the section under the viewport middle */
    chapter() {
      const mid = scrollY + innerHeight * VIEW_MID;
      let idx = 0;
      sections.forEach((el, i) => { const r = el.getBoundingClientRect(); if (r.top + scrollY <= mid) idx = i; });
      return idx;
    },
  };
}
