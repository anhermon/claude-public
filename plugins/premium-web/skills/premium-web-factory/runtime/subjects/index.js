// Subject factory: kind -> stage scene + the public API. Kinds are loaded on demand (the generator copies only the used one).
import { createCore } from './core.js';

const HIDDEN_AT = 0.97;   // hideV above this: the scene is not drawn at all (a zero-scale additive point cloud would still glow)

export async function createSubject(piece, { mobile }) {
  const kind = piece.subject.kind;
  if (kind === 'custom-module') {
    const mod = await import(/* @vite-ignore */ new URL(`../../../${piece.subject.module}`, import.meta.url).href);
    return mod.createSubject(piece, { mobile });
  }
  const mod = await import(`./${kind}.js`);
  const N = kind === 'point-cloud' ? mod.pointCount(piece, mobile) : piece.subject.items;
  const core = createCore({ piece, mobile, N });
  const scene = mod.create(core, piece), update = scene.update;
  scene.update = (c) => { update(c); scene.root.visible = core.st.hideV < HIDDEN_AT; };
  return { ...core.api, scene };
}
