# Spec prompts: a reproduction contract any coding agent can follow

Use this when the output must be reproduced by another agent or model, handed to a client, or rebuilt in another
stack. A good prompt here is not a creative brief; it is a machine-extractable spec of a decided design: tokens,
timings, shader code, asset manifest and acceptance checks. The coding agent contributes transcription, assembly
and verification, not taste. Observed on a public explainer of a prompt-library product (2026-11): a contract that
fixed the output file, hardcoded every constant, gave per-section numeric motion values and quoted shaders
verbatim produced a single-file reproduction much faster than the same site rebuilt in a framework (about half an
hour, with two corrupted spec fragments repaired by the agent). The spec, not the model, carried the quality.

Contents: 1 Contract header - 2 Stack and delivery - 3 Global tokens - 4 Asset manifest - 5 Section specs -
6 Shared utilities - 7 Performance and fallbacks - 8 Acceptance checks - 9 Writing rules - 10 Extracting a spec from a site

## Skeleton (fill every field; delete nothing)

```
# Recreate this page as <single self-contained index.html | named stack>: <name>

## 1. Contract
You are an expert front-end developer. Produce <deliverable> that reproduces the spec below exactly: same layout,
sections, visuals, motion and interaction. Do not redesign. If the spec is silent, choose the simplest option and
list it under "Assumptions" in your final message.

## 2. Stack and delivery
Single file or exact stack and versions; no build step (or the exact build); libraries vendored at pinned
versions, not CDN at runtime (CDN only if the brief allows it, with the pinned URL and a licence note);
hardcode every value below as a named constant at the top of the file; no magic numbers.

## 3. Global tokens
Colours (hex, role), type (family, weights, sizes at 1440 and 390, tracking, line-height), spacing, radii,
hairlines, easing curves (cubic-bezier values), z-order, grain / vignette amounts.

## 4. Asset manifest
| id | what | how it is produced | prompt / seed / style sheet | size / format | fallback |
Every asset says how it is made (code, shader, generated with this prompt and seed, photographed). Never
hot-link assets from another site. If an asset cannot be produced, specify the fallback and ship that.

## 5. Sections (one block each, in page order)
For each: id, one message, layout at 1440 and at 390, content (exact copy or its rules), the persistent subject's
state, and motion with numbers: trigger and threshold, duration, easing, stagger, offset/blur values, scroll
segments [start, end, what changes], pointer coupling, reduced-motion state.

## 6. Shared utilities
Text-reveal engine (unit, duration, stagger, easing), scroll timeline (damping), smooth scroll (if any),
IntersectionObserver thresholds, loader, cursor.

## 7. Performance and fallbacks
DPR cap, point or pixel caps, frame-rate caps, pause when hidden, poster-first LCP, flags ?rm ?nogl ?savedata ?slow.

## 8. Acceptance checks (the agent must run them and report results)
Measurable list, e.g.: no horizontal scroll at 390; zero console errors; fonts rendered (not system); the hero
object occupies >= 55 percent of the first viewport width at 1440; reduced-motion shows the final labelled
state; each section's motion matches its numbers (name the frame captures to take).

## 9. Do not
Banned defaults, banned copy, no invented proof, no extra sections, no framework unless stated.
```

## Writing rules

1. **Decide everything the agent would otherwise guess.** Each omission resolves to the average (F1). If you do not
   know a value, take it from the SPEC.md the build was made with, or measure a reference (section 10).
2. **Numbers, not adjectives.** "Fades in smoothly" becomes "opacity 0 to 1 and blur 10 px to 0, 0.6 s, easing
   cubic-bezier(.16,1,.3,1), 40 ms word stagger, trigger at 50 percent visibility". Timings measured from
   recordings are +-0.3 s; say so.
3. **Quote non-trivial code verbatim.** Shaders, particle morph kernels and scramble engines go into the prompt as
   code blocks; an agent will paraphrase prose and break the look. Mark corrupted-looking fragments as such and
   ask the agent to repair, not to guess.
4. **One manifest, no hot-links.** Reproduction fails when assets live on someone else's server. State how each is
   produced so any agent can regenerate it (premium-web-imagery for generated media, premium-web-svg and
   premium-web-webgl for code-drawn ones).
5. **Hardcode constants.** Constants at the top of the file with names; no environment lookups for design values.
6. **State the delivery contract** (file names, entry point, how to run) and what to report.
7. **Order of sections is the order in the file**, and each section is a direct child of the main container so a
   reviewer can map spec block to DOM node.
8. **Include the verification recipe**: the commands from qa-loop.md and the exact frames to capture, so the agent
   cannot claim it works having checked one viewport. Reproduction runs have claimed success after verifying
   desktop only.
9. **Size**: long is fine (a full spec is thousands of words), but structure it so a reader can jump: stable
   numbered headings and one block per section.
10. **Library conflicts**: a source contract may say "ES modules via CDN". The plugin's rule for templates is
    vendored, pinned libraries with a licence note; a client reproduction brief may allow CDN explicitly, but the
    default is vendored.

## 10. Extracting a spec from an existing site

1. Record the site scrolling (about 8 s at 1440, a mobile pass at 390) and take full-resolution frames at 4, 25, 50,
   75 and 95 percent plus the transitions.
2. `scripts/measure-site.js` for type, header, button, padding; sample palette from frames.
3. Read the page's CSS custom properties and keyframes for tokens and easings; derive timings from 30 fps frame
   pairs (+-0.3 s at 10 fps sampling; say which).
4. List the techniques as named primitives with parameters (blur-resolve, mask-rise, scroll timeline, point-morph,
   glass card) and the asset classes (code, procedural, media).
5. Write sections 3 to 8 of the skeleton. Mark every inferred value `INF` and every measured value `OBS`, and prefer
   OBS in the contract.
Do not copy proprietary copy, imagery or code; reproduce structure and parameters, and rewrite content.
