export const MOTION = { damping:.13, shift:18, scrollShift:12, scale:.035, settle:.02, frameMs:1000 / 60, maxDt:64, midpoint:.5, depthBase:.55, depthStep:.15 };
export const clamp = (value, min = -1, max = 1) => Math.min(max, Math.max(min, value));
export const damp = (value, target, dt) => value + (target - value) * (1 - (1 - MOTION.damping) ** (Math.min(dt, MOTION.maxDt) / MOTION.frameMs));
export const wordOffset = (pointer, progress, index, vertical = 0) => {
  const depth = Math.min(1, MOTION.depthBase + index * MOTION.depthStep);
  return { x:clamp(pointer) * MOTION.shift * depth, y:clamp(progress) * MOTION.scrollShift * (index % 2 ? -1 : 1) + clamp(vertical) * MOTION.scrollShift * depth };
};
