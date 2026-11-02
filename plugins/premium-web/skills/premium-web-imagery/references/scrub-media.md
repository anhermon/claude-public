# Generated video and scroll-scrub media

Contents: decide, make the clip, encode (script), player, rules, failure modes.

Scroll-scrubbed media = the page maps scroll progress to a frame of pre-rendered footage. Use it when the thing that moves cannot be
done live (generated footage, a heavy offline render) and the motion is short and meaningful. If a shader or 3D scene can draw it
live, prefer `premium-web-webgl`: smaller, sharp at any size, no encode step.

## Decide

| Need | Choose | Why |
|---|---|---|
| Short scrub (<= ~6 s, one pinned section) | image sequence on canvas | Most predictable: decoded stills, no seeking, works on every browser. |
| Smaller payload, still scrubbing | all-intra MP4 + `video.currentTime` | One file; needs HTTP Range support and every frame a keyframe. |
| Ambient loop, no scroll coupling | normal H.264/AV1 MP4, `autoplay muted loop playsinline` | Do not use all-intra for this: 3-6x larger for no gain. |
| Long footage | do not scrub | Cut to key moments, or time-drive a short loop on entering the viewport. |

## Make the clip

- Generated video (image-to-video, first/last frame control) is a source, not a deliverable: expect 3-8 s, 720p-1080p, drifting detail. Generate from ONE accepted still so the first frame matches the poster. Where the generator supports first-and-last-frame keys, use them to get a clean loop or a clean landing frame.
- Procedural footage: render a canvas/WebGL scene deterministically by frame number (fixed time step, seeded), capture frames headlessly, then encode. No variance between runs.
- Plan the scrub for ~24 fps sequences. A viewer scrolling at human speed does not resolve more; 12-24 stills for 1.5-3 viewport heights of scroll is typical. Numbers: practice defaults.

## Encode: `template/scrub.sh in.mp4 out/ [width=1280] [fps=30] [seq_fps=24]`

| Output | ffmpeg essentials | Why |
|---|---|---|
| `scrub.mp4` | `-c:v libx264 -g 1 -bf 0 -crf 20 -pix_fmt yuv420p -movflags +faststart -an` | `-g 1` = every frame a keyframe, so a seek decodes one frame, not a GOP. No B-frames. `faststart` lets the browser start before the full download. |
| `scrub.webm` (opt-in `SCRUB_WEBM=1`) | `-c:v libvpx-vp9 -crf 32 -b:v 0 -g 1` | Smaller than MP4 for Chrome/Firefox; Safari needs the MP4. |
| `frames/f%04d.webp` or `.jpg` | libwebp `-quality 72` when the ffmpeg build has it, else mjpeg `-q:v 4` | Sequence for canvas. The script falls back to JPEG on builds without libwebp. |
| `manifest.json` | frame count, pattern, fps, size | Read by the player. |

Verified here: the script produced an all-intra MP4 (every packet flagged keyframe) and a 36-frame sequence from a 3 s clip.
Budget: sequence <= ~1 MB per second of scroll range at 960 w, MP4 <= ~6 MB total; both on mobile need a smaller width (<= 720) variant.

## Player: `template/scrub-player.js`

`init(canvas, {mode: 'sequence'|'video', base, manifest, damp: 0.1})`. Progress = scroll position inside a tall section
(`height: 300-500vh`) with a sticky stage; the displayed frame follows progress through a damped lerp (0.08-0.1, measured
from public reference sites, 2026-11; +-0.02). It draws with cover-fit, preloads first and middle frames then the rest, tolerates
missing frames (nearest loaded), exposes `canvas.dataset.frame` / `.t` for tests, and shows a static poster frame under
`prefers-reduced-motion`.

## Rules

- First frame = the poster = the LCP image (`<img>` or CSS background under the canvas); the canvas paints over it when ready.
- Scrub the camera-like, continuous motion (rotate, dolly, assemble). Time-drive everything discrete (text reveals, state changes).
- Keep DOM text OUTSIDE the canvas; scrub only pixels. Overlay chapter copy with the motion skill's reveals.
- Mobile: serve a lower resolution and fewer frames, or a static poster plus a short autoplay loop.
- Never ship the media inside a skill or plugin repository; generate into the user's project.

## Failure modes

- **Video does not seek / stays on frame 0**: the server lacks HTTP Range support (`python3 -m http.server` has none). Use `template/serve-range.mjs`, or any real static host.
- **Stutter**: the clip is not all-intra, or decoded video is competing with other work; use the sequence path.
- **Blank canvas on load**: poster frame not drawn before listeners start; the player draws the first frame before the loop.
- **Colour shift video vs poster**: limited vs full range in encode; export the poster from the same encode.
- **Huge memory with long sequences**: do not hold hundreds of 1080p frames decoded; cap at ~60 frames or use video mode.
