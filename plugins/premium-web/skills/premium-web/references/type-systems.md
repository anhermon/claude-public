# Type systems

Measure first, then decide. `scripts/measure-site.js` returns h1/h2/body/nav as "family | px | weight | lh |
tracking | transform", header height, buttons, section padding, uppercase small-label count and transitions.
Run it on 6-12 reference sites for YOUR direction (headless: `EVAL=scripts/measure-site.js SHOTS=0 node
scripts/chrome-shot.mjs <url> <out> 1440,390`; or paste it into claude-in-chrome's javascript_tool) and tabulate.

## Decision rules

1. **One family carries the page** on every measured premium site (11/11 below). A second face is a deliberate
   voice (a display serif for a cinematic page, a mono for the tool's own output), never decoration.
2. **Mono is for code, data, paths and terminal output only.** Mono body copy and mono labels everywhere are a
   templaty tell (ember). Uppercase tracked micro-labels: at most one per section, ideally none.
3. **Sentence case** for headings, buttons and nav.
4. **Tracking follows size**: about -0.022em at >= 32px for neutral grotesks; display serifs need less (-0.01em)
   and kerning QA ("W eather" gap at 120px in halcyon). Body -0.011em at 17px for Inter-like faces, 0 for most others.
5. **Line height**: display 1.0-1.08, but check descender/ascender collisions at 1440 AND 390 (meridian's h1 at
   .92 collided "y" into "i"). h2 1.1, body 1.5-1.6.
6. **Scale**: h1 64-80 desktop / 40-48 phone; h2 44-56 / 30-34; body 17-19; small 13-14. Section padding
   clamp(88px, 10vw, 144px). Header 64. Primary button 44 tall, radius matched to the style (8 neutral, pill tactile, 0 Swiss).
7. **Self-host** a latin woff2 subset: `scripts/get-font.sh <fontsource-id> fonts` (refuses non-open licences,
   prints @font-face). Preload the one face used above the fold. Verify it rendered: chrome-shot reports
   CSS.getPlatformFontsForNode per selector; "(system)" on h1 means your font did not load.
8. **Banned as "ChatGPT fonts"** for new concepts (Angel): Inter (anhermon.dev owns it), Geist, Bricolage Grotesque,
   Space Grotesk, Poppins, DM Sans, Plus Jakarta Sans. Also rejected as a direction: condensed display serif +
   uppercase mono eyebrows + italic accent word (gallery/reject-anhermon-03364e9-serif-mono), Bricolage condensed at
   -0.045em (v3).
9. Faces already owned in Angel's portfolio (do not reuse in a new concept): Schibsted Grotesk + IBM Plex Mono
   (meridian), Martian Mono + Commit Mono (ember), Fraunces + Figtree (pebble), Bodoni Moda + Instrument Sans +
   Sometype Mono (halcyon), Big Shoulders + Azeret Mono + Archivo (tracer).

## Measured references (2026-10-01, from the retype probe)

| site | display font (licence) | h1 px d/m | weight | tracking em | body px/lh | mono use | header px | primary button h/radius | section pad d/m | motion |
|---|---|---|---|---|---|---|---|---|---|---|
| apple.com/macbook-pro (dark) | SF Pro Display/Text webfont (proprietary, Apple-platform only) | 80 / 48 | 600 | -0.015 / -0.003 | 17/1.47 (21 intro) | none | 44 globalnav | 36 r8 / pill 980 | 144 / 112 | 0.32s cubic-bezier(.4,0,.6,1) |
| apple.com/iphone-air | SF Pro | 48 / 34 | 500-600 | -0.003 | 17/1.47 | none | 44 | 28 pill | 160 / 96 | 0.32s |
| stripe.com | Söhne (Klim, proprietary) | 56 / 34 | 300 | -0.025 / -0.01 | 16-18 w300 | none | 64-76 | 40-48 r4 | n/a | 0.3s cubic-bezier(.25,1,.5,1) |
| linear.app (dark) | Inter Variable (OFL) | 64-72 / 38 | 510 | -0.022 | 15/1.6 -0.011 | Berkeley Mono only in code/product UI | 72 / 64 | 32 pill | 128 / - | 0.1-0.16s |
| vercel.com (dark) | Geist (OFL) | 64 / 48 | 400 | -0.06 (trend-tight) | 14-24 | Geist Mono labels | 64 | 32-40 r6/pill | n/a | 0.1-0.15s |
| notion.com | NotionInter (Inter derivative) | 96 / 42 | 600 | -0.048 (trend-tight) | 20/1.4 desktop, 16/1.5 phone | none | 64 | 36-38 r8 | 96 / 32 | 0.2s |
| figma.com | figmaSans (proprietary) | 56-88 / 36 | 400 | -0.022 | 16-30 | figmaMono minor | 78 / 72 | 46 r8 | 80 / 40 | 0.15-0.18s ease-out |
| framer.com (dark) | GT Walsheim (proprietary) + Inter body | 54 / 36 | 500 | -0.04 | 18/1.35 Inter | code only | 64 | 30 r8 | 100-120 / 60 | - |
| github.com (dark) | Mona Sans (OFL); repo UI = system stack | 64 / 40 | 425-440 | -0.035 / 0 | 18/1.5 | Mona Sans Mono / ui-monospace in code | 72 / 64 | 32-48 r6 | - | 0.2s ease |
| gov.uk | GDS Transport (proprietary) | 64 / 40 | 700 | 0 | 19/1.32 | none | - | 38 r0 | 60 | none |
| airbnb.com | Cereal (proprietary) | 28 (app UI) | 700 | 0 | 14 | none | 96 | pill | - | 0.2-0.3s cubic-bezier(.2,0,0,1) |

## What anhermon v4 chose from them

| token | measured references | v4 chosen |
|---|---|---|
| family | 1 sans for everything on all 11 (SF Pro, Söhne, Inter, Geist, NotionInter, figmaSans, Mona Sans, GDS Transport) | Inter variable, opsz 14-32 (Display cut auto at large sizes) + wght; OFL; 40KB woff2 subset |
| mono | only in code/product UI (Linear Berkeley Mono, GitHub Monaspace->ui-monospace) | ui-monospace stack, only for span names, paths, code, log levels, run ids |
| h1 desktop/phone | Apple 80/48, Linear 64-72/38, GitHub 64/40, Stripe 56/34, Figma 56/36, gov.uk 64/40 | 72 / 40 (clamp 40px, 5.2vw, 72px) |
| h1 weight | Apple 600, Linear 510, GitHub 425-440, gov.uk 700, Stripe 300 | 600 |
| h1 tracking | neutral group -0.015..-0.022 (Apple, Linear, Figma); Inter curve -0.022 at >=32px | -0.022em |
| h1 line-height | 1.0-1.08 (Apple 1.05, Linear 1.0-1.1, GitHub 1.08) | 1.04 |
| h2 | Apple 56/32 w600, Linear 48/24 w510, Notion 54/32 | 48 / 32, w560, -0.022em, lh 1.1 |
| h3 / card title | Linear 20 w590 -0.012, Apple 21-28 w600, GitHub 20-22 w600 | plates 36/28 w560; cards 20 w600 -0.017em |
| body | Apple 17/1.47, GitHub 18/1.5, Linear 15/1.6, gov.uk 19/1.32 | 17/1.55, -0.011em (Inter curve at 17 = -0.013) |
| lede | Apple intro 21, Notion 20 | 21 / 18 |
| small/UI | 13-14px (all) | 13-14px, w500 |
| measure | Apple 980 container / text cols 372-630; Linear 505-540 p | container 1200; text <= 58-60ch (~600px) |
| header | Linear 72/64, Vercel 64, Notion 64, Figma 78/72, GitHub 72/64 | 64, sticky, blurred bg after 8px scroll, 3 section links + 1 CTA |
| primary button | Notion 36-38 r8, Figma 46 r8, Stripe 40-48 r4, GitHub 32-48 r6, Apple 36 r8 | 44 r8 (header CTA 36 r8), 15/500 |
| section padding | Apple 144/112, Linear 128, Framer 100-120/60, Figma 80/40 | clamp(88px, 10vw, 144px) |
