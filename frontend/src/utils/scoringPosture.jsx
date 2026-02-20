import { POSTURE_THRESH, POSTURE_WEIGHTS } from "../config/scoringConfig";
import { clamp01, dist2, mid, penaltyBetween, penaltyBetweenMin } from "./math";

/**
 * Landmarks (Pose):
 *  11 left shoulder, 12 right shoulder
 *  7  left ear,      8  right ear
 *  0  nose
 *
 * Metrics:
 *  tilt = |yL - yR| / shoulderWidth                     (lower is better)
 *  headForward = |noseZ - shoulderMidZ| / shoulderWidth (lower is better)
 *  neckRatio = (shoulderMidY - earMidY) / shoulderWidth (higher is better)
 *
 * Note: y grows downward in normalized coords
 * so shoulderMidY - earMidY is positive when ears are above shoulders.
 */
export function computePostureScore(poseLandmarks) {
  if (!poseLandmarks) return null;

  const nose = poseLandmarks[0];
  const lShoulder = poseLandmarks[11];
  const rShoulder = poseLandmarks[12];

  const lEar = poseLandmarks[7];
  const rEar = poseLandmarks[8];

  if (!nose || !lShoulder || !rShoulder) return null;

  const shoulderMid = mid(lShoulder, rShoulder);

  const shoulderWidth = dist2(lShoulder, rShoulder);
  if (!shoulderWidth || shoulderWidth < 1e-6) return null;

  // NEW: horizontal head alignment
const headOffset = Math.abs(nose.x - shoulderMid.x) / shoulderWidth;
  
  // 1) Shoulder tilt
  const tilt = Math.abs(lShoulder.y - rShoulder.y) / shoulderWidth;

  // 3) Neck ratio (ear-to-shoulder vertical distance)
  // If ears aren't detected well, fall back to nose as a rough proxy
  const earMid =
    lEar && rEar ? mid(lEar, rEar) : null;

  const headTop = earMid ?? nose;
  const neckRatio = (shoulderMid.y - headTop.y) / shoulderWidth;

  // Penalties
  const tiltPenalty = penaltyBetween(
    tilt,
    POSTURE_THRESH.tiltGoodMax,
    POSTURE_THRESH.tiltBadMax
  );

  const headPenalty = penaltyBetween(
    headOffset,
    POSTURE_THRESH.headForwardGoodMax,
    POSTURE_THRESH.headForwardBadMax
  );

  // higher neckRatio is better
  const neckPenalty = penaltyBetweenMin(
    neckRatio,
    POSTURE_THRESH.neckGoodMin,
    POSTURE_THRESH.neckBadMin
  );

  const wTilt = POSTURE_WEIGHTS.tilt;
  const wHead = POSTURE_WEIGHTS.head;
  const wNeck = POSTURE_WEIGHTS.neck;

  const weightedPenalty = clamp01(
    wTilt * tiltPenalty + wHead * headPenalty + wNeck * neckPenalty
  );

  const score = Math.round(100 * (1 - weightedPenalty));

  return {
    score,
    metrics: {
      tilt,
      headOffset,
      neckRatio,
      penalties: { tiltPenalty, headPenalty, neckPenalty },
    },
  };
}