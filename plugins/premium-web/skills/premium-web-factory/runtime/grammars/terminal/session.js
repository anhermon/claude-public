export const TYPE_MS = 35, GLITCH_MS = 260, CLOCK_MS = 1000, CHAPTER_MID = .55;
export const SESSION_STATE = { typing:'TYPING', complete:'COMPLETE' };
export const characterCount = (elapsed, length) => Math.min(length, Math.max(0, Math.floor(elapsed / TYPE_MS)));
export const sessionIndex = (tops, height) => tops.reduce((active, top, i) => top < height * CHAPTER_MID ? i : active, 0);
