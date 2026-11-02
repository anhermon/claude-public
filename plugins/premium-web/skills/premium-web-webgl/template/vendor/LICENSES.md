# Vendored libraries

| File | Library | Version | Licence | Why vendored |
|---|---|---|---|---|
| `three.module.min.js` | three.js | r170 | MIT (`LICENSE-three`) | No CDN at runtime; the point-morph scene and the stage use `WebGLRenderer`, `Points`, `ShaderMaterial`. |

The shader-field module (`src/fx-canvas.js`) is raw WebGL2 and needs nothing from this directory.
Upgrade by replacing the file and re-running `node selftest.mjs`; keep the pinned version in this table.
