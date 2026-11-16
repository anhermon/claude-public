# Forms done right

Working implementation: `assets/skeleton/form.css` + `form.js` + the form in `assets/skeleton/index.html`.

## The anti-pattern that shipped (anhermon form, fixed 2026-10-01)

The consent checkbox rendered at browser-default size scaled up by a generic `input { width: 100%; height: 44px }`
rule (a **huge checkbox**), and the honeypot "Website" field was **visible** on mobile because it was hidden with a
class that a later rule overrode. Both came from styling `input` globally.

## Rules

- Scope text-input styles so they never hit checkboxes, radios or hidden inputs:
  `:is(input:not([type=checkbox]):not([type=radio]):not([type=hidden]), select, textarea)`.
- **Custom checkbox ~20px**, inline with its label in a 2-column grid, the whole label is the hit area (>= 24px tall,
  WCAG 2.5.8), visible focus ring, checked state uses the accent:
  ```css
  .consent { display:grid; grid-template-columns:20px 1fr; gap:12px; align-items:start; min-height:24px; cursor:pointer }
  .consent input { appearance:none; width:20px; height:20px; margin:1px 0 0; display:grid; place-content:center;
    border:1.5px solid var(--rule-2); border-radius:5px; background:var(--bg) }
  .consent input::after { content:""; width:10px; height:6px; border:solid var(--on-accent); border-width:0 0 2px 2px;
    transform:translateY(-1px) rotate(-45deg) scale(0) }
  .consent input:checked { background:var(--accent); border-color:var(--accent) }
  .consent input:checked::after { transform:translateY(-1px) rotate(-45deg) scale(1) }
  ```
- **Honeypot fully hidden**: off-screen + clipped + `aria-hidden="true"` + `inert` + `tabindex="-1"` +
  `autocomplete="off"`; not `display:none` (some bots skip those fields). On a honeypot hit, show the normal success
  message and send nothing.
  ```html
  <label class="hp" aria-hidden="true" inert>Website <input name="website" tabindex="-1" autocomplete="off"></label>
  ```
  ```css
  .hp { position:absolute!important; left:-10000px; width:1px; height:1px; overflow:hidden; clip-path:inset(50%); opacity:0; pointer-events:none }
  ```
- Labels above fields, 44px inputs, 16px+ font (iOS zooms below 16px), correct `type`/`autocomplete`/`inputmode`.
- Inline errors per field (`aria-describedby` -> `.f-err`, `aria-live="polite"`), validated on submit then on input;
  focus the first invalid field. Don't disable the submit button.
- States: sending (button text changes, no spinner-only), success (what happens next and when), error (what to do,
  with a mailto fallback). 10s timeout via AbortController.
- Say what is stored and why, right under the button, with a privacy link. Consent checkbox only for what the
  law needs (marketing email); never pre-ticked.
- Verify in screenshots at 390: checkbox size, honeypot invisible, error state, success state.
- Concept/demo pages: a non-submitting form that still shows the success state, labelled as a demo.
