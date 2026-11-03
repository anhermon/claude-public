# Archetypes

Nine section types. Each is a server-side renderer plus CSS (`archetypes/<id>.mjs`) and a client mount (`runtime/archetypes/<id>.js`).
Only the archetypes a spec uses are rendered and copied. All sections carry `data-act` (subject state), `data-side` (copy side) and
`min-height` that gives the morph room. Mobile is a separate composition: the subject sits in the top 38svh and copy starts below it.

| Archetype | Target | Copy fields | Params | What it does |
|---|---|---|---|---|
| `hero` | yes | `title`, `em?`, `deck`, `ctas[{label,href,kind}]` | `readoutRows` (3), `wordmarkBandVh` (30) | Headline, CTAs, live query readout, giant wordmark in a reserved bottom band, drawn in GL so the subject refracts it. |
| `claim` | yes | `title`, `em?`, `deck` | `rows` (5) | Group chips and ranked live hits for the cursor query (brute-force screen-space distance, honours the chip filter). |
| `explainer` | yes | `title`, `em?`, `deck`, `layers[{label,detail}]`, `slider?`, `numerals?`, `fine?` | none | Layer list that lights a group, a slider that drives a sample curve, three numerals. |
| `band` | no | `line`, `caption?` | `slot`, `lineCount`, `heightSvh` | Full-bleed art plate (procedural contours or `img/` file) with one line; the subject shrinks away while it is current and returns after. |
| `stat` | yes | `title` (hidden h2), `giant`, `deck?`, `steps[]`, `stepLabel?`, `numerals[]`, `fine?` | none | Giant number, a stepper that fans the subject out, four modelled numerals (`divide`, `log`, `linear`, `inverse`). |
| `ship` | yes | `title`, `em?`, `deck?`, `tabs[{id,label,code}]`, `response?[{name,score}]` | none | Code tabs (roving tabindex) and a sample response. |
| `pricing` | yes | `title`, `em?`, `deck?`, `fine?` | none | Calculator matrix from `commerce`: every tier priced live, best fit highlighted, sliders drive the subject. |
| `faq` | yes | `title`, `em?` | `openFirst` (true) | Disclosure list from `commerce.faq`; clears the fixed nav. |
| `footer` | no | none | `slot`, `lineCount` | CTA card from `commerce.cta`, DOM wordmark fitted to the width, notice line. The subject hides here. |

## Critic fixes built in

These came from the critic pass on the hand-built piece, so the factory does not reintroduce them:

- Pricing is a calculator, not a card row, and it drives the subject (lit fraction = usage, tower height = cost).
- The subject refracts the wordmark (GL plane behind it, glass or flow in front). The DOM wordmark shows only when GL is off.
- The readout sits top-right on desktop and in flow below the CTAs on mobile; the hero reserves a wordmark band (`wordmarkBandVh`)
  and the headline is capped by viewport height, so copy and CTAs never enter the band.
- `faq` and every act pad below the fixed nav.
- No big mobile gaps: mobile acts are `min-height: 100svh` with a fixed top pad for the subject, and the subject shrinks away
  (`setHide`) once a section taller than the viewport has scrolled, so long copy never runs under it.
- Pricing on mobile puts sliders and the total first so the calculator and the subject are in the same screen.
- `stat` reserves its bottom 40svh for the subject so the numerals never overlap it.

## Motion and fallbacks

Reveals use the motion template (`blur-line`, `word-blur`, `stagger-grid`, curtain-progress loader). Reduced motion renders a static
GL frame (no scroll morph, assembled subject). No WebGL, or `?nogl`: poster mode, DOM wordmark, readout shows `n/a`. `?slow` forces
the quality governor. `html[data-gl]` is `live` or `poster`.
