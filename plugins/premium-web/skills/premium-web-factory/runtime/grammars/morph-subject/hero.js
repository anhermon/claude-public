import { mount as originalMount } from './hero-base.js';
export function mount(el, ctx) {
  return el.querySelector('[data-role=ms]') ? originalMount(el, ctx) : {};
}
