# Headless GPU verification

A WebGL page that passes its assertions can still be a black rectangle. Capture, then look.

## Contents
- Flags
- The loop
- Frame-time method
- Failure modes

## Flags

| Platform | Chrome args | Notes |
|---|---|---|
| macOS | `--use-angle=metal --ignore-gpu-blocklist` | verified with system Chrome through Playwright, 2026-11 |
| Linux | `--use-angle=swiftshader --enable-unsafe-swiftshader` or a real GPU with `--use-gl=egl` | NOT verified here; software GL is 5-20x slower, so frame times mean nothing |
| Windows | `--use-angle=d3d11 --ignore-gpu-blocklist` | NOT verified here |

Use the system Chrome (`executablePath`), not Playwright's bundled headless shell, whose GPU path is often disabled. Override
with `GPU_ARGS="..." node selftest.mjs`.

## The loop

1. Serve the folder over HTTP (`python3 -m http.server`); ES modules do not load from `file://`.
2. For each scroll state, set `scrollTo`, wait about 2 s (the progress is damped), screenshot.
3. Hide the copy (`.copy { visibility: hidden }`) for one set of frames so the canvas alone is judged and cannot look different only because text moved.
4. Assert the frames are not flat (PNG size) and differ per state, then OPEN them. State what is visible: shape, lighting side, colour, edge clipping, overlap with copy.
5. Repeat at 390 x 844 with `deviceScaleFactor 3`: check DPR cap, cloud above the copy, no horizontal overflow.
6. Run the fallback paths: `?nogl`, `?rm`, `?slow`, and a forced context loss (`WEBGL_lose_context`).

## Frame-time method

`stage.stats()` keeps a ring of the last 900 frame times (rAF deltas). Reset, sweep the scroll for 3.5 s, read p50 and p99.
Headless runs at the display rate (16.7 ms), so only a miss (p99 over two frames) is informative. For GPU-inclusive cost use a
shader field with `measure: true` (adds `gl.finish()`, distorts rAF, test only). CPU throttling (`Emulation.setCPUThrottlingRate`) is a lab
proxy for a phone, not a measurement of one: never claim a real-device frame rate from it.

## Failure modes

| Symptom | Cause | Fix |
|---|---|---|
| Blank canvas, no errors | headless without GPU flags; or page background covering a negative z-index stage | flags; background on `html` only |
| Everything one flat colour | shader compile error swallowed | `fx-canvas` throws readable errors with line context; read the console |
| Frames identical across states | progress not reaching the scene | check `stage.ctx.progress` and the scroll element |
| Passes locally, black in CI | software GL has no float textures / extensions | design for WebGL2 baseline; test the poster path in CI |
