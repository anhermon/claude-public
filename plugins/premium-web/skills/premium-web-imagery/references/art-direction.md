# Art direction: one style sheet, one seed, per-slot briefs

Contents: the style sheet, the prompt template, what to generate vs draw, recipes by genre, subjects that work, review.

## Principle

Pick every image by what it COMMUNICATES in its section, never by how impressive it looks alone. If a section needs a caption to
explain its image, the image is wrong. Consistency across the set is half the premium feel: one light direction, one material
family, one palette, one grain, one framing logic. Generate the whole set from ONE style sheet, then judge the set side by side.

## The style sheet (template/imagery.config.json, `style`)

| Field | Decides | Example |
|---|---|---|
| `palette.ground / accent / highlight` | the page's own tokens, never provider defaults | `#0E0F12 / #7FA2FF / #ECE8DC` |
| `light` | ONE direction and quality | "one soft key light from upper left, long falloff" |
| `material` | a family, not a list | "matte ceramic and brushed metal" |
| `grain` | the same finish as the page's grain layer | "fine film grain" |
| `mood` | 2-3 adjectives, no hype words | "calm, expensive, quiet" |
| `seed` | reused for every asset where the provider supports it | `424242` |
| `negative` | the always-excluded list | no text, letters, numbers, watermarks, logos, UI, people, faces, hands |

Seed reuse reduces drift but does not guarantee identity. For a set that must match tightly, also generate in ONE session and
pass the first accepted image as a reference image when the provider supports it (image-to-image / style reference).

## Prompt template

`<aspect> image (<w>x<h>). <subject: ONE concrete physical thing and what it does>. <slot composition>. <look from the style sheet>. <negative list>`

`pipeline.py prompts` builds this for every asset (and `art_direct` does the same inside the MCP). Slot compositions
(from the config `slots`): hero keeps the left 40% empty for the headline; plate has one centred subject with breathing room;
backdrop has no focal point so text can sit on it; og keeps the left 55% empty (text is composited locally afterwards).
Always add colour tokens from the page; a light or muted page given the dark default looks wrong.

## Generate vs draw

| Situation | Choice | Why |
|---|---|---|
| Technical claim, mechanism, data, process, architecture | draw in code (`premium-web-svg`) | Code-drawn figures carry real labels and state; a photo can set mood next to a claim, it cannot make one. |
| Literal metaphor (gate, lock, shield, brain, circuit board) | neither; pick a physical analogue of the data | Literal metaphors read as stock and as "weird". |
| Atmosphere, material, place, still life at human scale | generate | Photographic texture is what generation does best. |
| Diagrams or "technical illustration" prompts | never generate | They produce sparse, meaningless sketches. |
| Anything with text, numbers, UI, logos | never generate; overlay in HTML/SVG | Generated text is wrong often enough to be disqualifying. |
| OG / social cards | generate the background only, composite text locally | Same reason. |
| A real person, a real product, a real place the page is about | the user supplies it | Never synthesise proof. |

A generated plate becomes specific when real labels, values or a real data point are overlaid in HTML on top of it.

## Recipes by genre (subject recipe + what to avoid)

| Genre | Subject recipe | Example subject | Avoid |
|---|---|---|---|
| cinematic / creative | a real place or object at human scale, one light direction | "a calm sea at dusk under heavy cloud, a thin band of warm light on the horizon" | sci-fi, neon, "epic" |
| tactile / clay | one chunky object per section doing the product's verb | "a stack of soft rounded pebbles in five pastel colours, the top one cream" | emoji-style 3D, gradient blobs |
| editorial dark product | a material close-up with a physical analogue of the data | "a row of fine metal pins along a glowing blue line on dark wood" | literal metaphors |
| terminal-native | the place the tool lives, not the tool | "a rack in a dark machine room lit by one amber status light" | a picture of a terminal, code on screens |
| Swiss / data | none: code-drawn charts, annotated figures, tables | n/a | photos, 3D |
| light / human | still life of the work's real objects | "a stack of printed invoices with a paperclip, window light" | stock office scenes |

Style presets in the MCP: `dark-studio`, `paper-editorial`, `neutral-product`, `tactile-clay`, `cinematic-film`, `terminal-world`, `material-texture`.

## Always-negative list

No text, letters, numbers, captions, watermarks, logos, UI, screens, people, faces, hands; no glowing brains, robots, circuit boards,
binary rain, fibre-optic stock imagery, lens-flare cliches, isometric icon clutter.

## Review (per image, then per set)

1. Does it explain its section without a caption? If not, cut it.
2. Stray text, letters, logos, UI, extra fingers? Reject.
3. Same light, palette, grain and material as the others? Lay the set side by side (`compare`); outliers get redone, not tolerated.
4. Is the area where the copy sits actually empty and low-contrast? Measure contrast on the final crop, not on the plate.
5. Generate 2 variants per slot, keep at most one, record the verdict for accepted AND rejected images with the reason.
