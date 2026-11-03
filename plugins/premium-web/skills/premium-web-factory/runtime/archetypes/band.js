// band: writes --band-p (0 -> 1) as the band scrolls in; CSS opens the inset frame from it.
import { clamp } from '../util.js';

const OPEN_VIEW = 0.9;
export function mount(el) {
  const upd = () => el.style.setProperty('--band-p', clamp(1 - el.getBoundingClientRect().top / (innerHeight * OPEN_VIEW)).toFixed(3));
  addEventListener('scroll', upd, { passive: true }); addEventListener('resize', upd); upd();
  return {};
}
