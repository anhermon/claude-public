# Forms done right

Short generic rules; verify each at a true 390 viewport.

- Scope text-input styles so they never hit checkboxes, radios or hidden inputs:
  `:is(input:not([type=checkbox]):not([type=radio]):not([type=hidden]), select, textarea)`. A global `input` rule
  produces oversized checkboxes and un-hides the honeypot.
- **Custom checkbox about 20 px**, inline with its label in a two-column grid; the whole label is the hit area (at
  least 24 px tall); visible focus ring; checked state uses the accent.
- **Honeypot fully hidden**: off-screen, clipped, `aria-hidden="true"`, `inert`, `tabindex="-1"`,
  `autocomplete="off"`; not `display:none` (some bots skip those). On a honeypot hit show the normal success message
  and send nothing.
- Labels above fields, 44 px inputs, 16 px or larger text (iOS zooms below 16), correct `type`, `autocomplete`,
  `inputmode`.
- Inline errors per field (`aria-describedby`, `aria-live="polite"`), validated on submit then on input; focus the
  first invalid field; do not disable the submit button.
- States: sending (the button text changes, not a spinner alone), success (what happens next and when), error (what
  to do, with a mailto fallback). 10 s timeout with `AbortController`.
- Say what is stored and why directly under the button, with a privacy link. A consent checkbox only for what the
  law requires; never pre-ticked.
- Concept or demo pages: a non-submitting form that still shows the success state, labelled as a demo.
- Screenshot check at 390: checkbox size, honeypot invisible, error state, success state.
