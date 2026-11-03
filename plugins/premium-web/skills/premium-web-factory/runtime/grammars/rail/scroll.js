// Pure math is shared by the rail controller and its offline tests.
export const clamp = (v, lo = 0, hi = 1) => Math.max(lo, Math.min(hi, v));
export const FRAME_MS = 1000 / 60, MAX_DT_MS = 64, SETTLE_PX = 0.1;
export const MOTION = { velocityGain: 0.045, skewDeg: 5, stretch: 0.07, shiftPx: 3, scale: 0.045, wipePct: 5, contourShift: 90 };
export const travelFor = (trackWidth, viewportWidth) => Math.max(0, trackWidth - viewportWidth);
export const progressFor = (top, travel, ratio) => travel > 0 ? clamp(-top / (travel * ratio)) : 0;
export const damp = (value, target, damping, dt) => value + (target - value) * (1 - Math.pow(1 - damping, clamp(dt, 0, MAX_DT_MS) / FRAME_MS));
export const horizontal = (width, breakpoint, reduced, fits) => width > breakpoint && !reduced && fits;
