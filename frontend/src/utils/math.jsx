export function clamp01(x) {
  return Math.max(0, Math.min(1, x));
}

export function norm01(x, a, b) {
  if (a === b) return 0;
  return clamp01((x - a) / (b - a));
}

// value <= goodMax => 0 penalty; value >= badMax => 1 penalty
export function penaltyBetween(value, goodMax, badMax) {
  return norm01(value, goodMax, badMax);
}

// value >= goodMin => 0 penalty; value <= badMin => 1 penalty
export function penaltyBetweenMin(value, goodMin, badMin) {
  if (value >= goodMin) return 0;
  if (value <= badMin) return 1;
  return clamp01((goodMin - value) / (goodMin - badMin));
}

export function ema(prev, next, alpha) {
  if (prev == null) return next;
  return prev + alpha * (next - prev);
}

export function dist2(a, b) {
  const dx = a.x - b.x;
  const dy = a.y - b.y;
  return Math.sqrt(dx * dx + dy * dy);
}

export function mid(a, b) {
  return { x: (a.x + b.x) / 2, y: (a.y + b.y) / 2, z: (a.z + b.z) / 2 };
}

export function rad2deg(r) {
  return (r * 180) / Math.PI;
}
