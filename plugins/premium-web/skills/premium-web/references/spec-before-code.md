# Spec before code

Write this as `SPEC.md` in the project before the first line of HTML, CSS or JS. It is the countermeasure for
failure modes F1, F2, F3, F4, F7 and F8 (failure-modes.md): every open decision left to the model resolves to the
genre average. Fill every field with a concrete answer. "TBD", "modern", "clean" and "premium" are not answers.
Checkpoint the file as you go; later steps read it, and the critic receives its acceptance tests.

Contents: 1 Brief - 2 Truth inventory - 3 Genre test - 4 Subject and chapters - 5 Palette world - 6 Type - 7 Motion
grammar - 8 Finishing layer - 9 Asset plan - 10 Mobile composition - 11 Acceptance tests

## 1. Brief
- Audience: who arrives, from where, knowing what.
- The page's ONE job (one primary action) and ONE claim, each in one sentence.
- Constraints: brand assets already owned, fonts, hosting, stack (single file or named framework), size budget.

## 2. Truth inventory
List only real, checkable facts: repos, releases, dated numbers, named people who agreed. Everything else is
labelled sample data or cut. Concept pages carry a visible "concept / sample data" tag placed in the nav, not in a
fixed overlay. See trust.md.

## 3. Genre test
- "Left alone this page becomes ___" (name the genre template, for example "dark developer tool with bordered mono
  panels", "centred SaaS hero with three cards", "cream editorial with a serif").
- Four concrete changes that escape it (ground, scale, subject, structure, not decoration).
- External reference: 3 live pages that are NOT the category average, with what you borrow from each. A banned
  default (direction.md) is allowed only if one of these references uses it deliberately.

## 4. Subject and chapters
- Hero subject: the ONE object, world or image that persists (3D object, particle field, shader, photographed
  or rendered object, drawn figure). One sentence on what a stranger sees.
- Chapters (4-6), one row each:

| # | chapter | one message | subject state (form / position / camera) | ground and palette | transition in |
|---|---|---|---|---|---|

- Every chapter changes at least two of: subject state, ground, scale of type, layout shape. No more than two
  consecutive chapters share a layout shape.

## 5. Palette world
Tokens as hex values with a role each: ground, surface, ink, ink-soft, hairline (8-16 percent of ink), one or two
accents. State the hot-pixel budget (share of any frame at S > 0.72 and V > 0.5; target under 0.05). Large fields
stay neutral or low-chroma. Per-chapter grade shifts are listed in the chapter table.

## 6. Type
Display family, text family, optional mono (data only); the measured scale from direction.md (h1, h2, body,
display-to-body ratio, tracking, line-height, weights); where the one giant-type moment is. Fonts are fetched at
build time (`scripts/get-font.sh`), never bundled in the skill.

## 7. Motion grammar
Fill with numbers (premium-web-motion has the modules):
- Entrance / loader: what it is, duration, how it hands off to the hero.
- Text reveal: unit (line / word / char), duration, stagger, easing, blur and offset, trigger threshold.
- Scroll timeline: segments as [start, end, what changes], damping.
- Chapter hand-offs: transition type and duration (under 0.7 s), what stays, what changes.
- Pointer coupling: what responds, lerp factor, maximum tilt.
- Reduced-motion state: the final, fully labelled composition. Fallbacks: no WebGL, Save-Data, slow-frame watchdog.

## 8. Finishing layer
Light direction, environment, grain amount (3-10 percent), vignette, glow / bloom ceiling, material per surface.
Banned as finish: default box-shadow, flat panels, uniform gradients without grain.

## 9. Asset plan
One row per visual element. Class is code (CSS / SVG / canvas), procedural (shader, particles, generated
geometry) or media (generated or photographic image, video).

| element | class | tool (sub-skill) | style sheet / seed | size / format | fallback if the tool is missing |
|---|---|---|---|---|---|

Rules: detect image generation before planning (premium-web-imagery); media sets come from one style sheet and
one seed for consistency; text and diagrams are never generated; every media row has a code or procedural
fallback; nothing generated is shipped inside a reusable skill or template.

## 10. Mobile composition (390 px)
Per chapter: what leads, what is cut, where the subject sits, tap targets. This is a separate composition, not a
squeeze. State the 390 first-viewport content: the subject plus the one action.

## 11. Acceptance tests
- Wow test: "A stranger screenshotting this would say: ___" plus two numeric checks (wow.md).
- Craft numbers (section-craft.md): panel run, scale changes, type ratio.
- Gates: no horizontal scroll at 390, zero console errors, fonts rendered, Lighthouse as a gate (qa-loop.md).
- Round budget and the external references the critic is calibrated against.
