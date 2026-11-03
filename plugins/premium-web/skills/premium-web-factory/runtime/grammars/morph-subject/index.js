import { createSubject as originalSubject } from './index-base.js';
const STATIC_TIME = 0, STATIC_POINTER = { x: 0, y: 0, moved: false };
export async function createSubject(piece, env) {
  const subject = await originalSubject(piece, env), mode = piece.scroll?.mode;
  if (mode === 'static' || mode === 'orbit') {
    const update = subject.scene.update;
    subject.scene.update = (ctx) => update({ ...ctx, time: STATIC_TIME, pointer: STATIC_POINTER, reduced: true });
    subject.setDrive = () => {};
  }
  return subject;
}
