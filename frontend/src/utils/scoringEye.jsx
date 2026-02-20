import { EYE_THRESH, EYE_WEIGHTS } from "../config/scoringConfig";
import { clamp01, dist2, mid, penaltyBetween, rad2deg } from "./math";

/**
 * Compute yaw/pitch from MediaPipe face transformation matrix (best),
 * fallback to landmark-geometry estimation (okay).
 *
 * The transformation matrix is 4x4. We use its "forward" axis to estimate head direction.
 */
function headPoseFromMatrix(matrix) {
  // matrix may be { data: Float32Array(16) } or { data: { data: [...] } } depending on build
  const arr =
    matrix?.data?.length === 16
      ? matrix.data
      : matrix?.data?.data?.length === 16
      ? matrix.data.data
      : Array.isArray(matrix) && matrix.length === 16
      ? matrix
      : null;

  if (!arr) return null;

  // MediaPipe matrices are typically column-major.
  // Forward (z axis) is third column: indices 8,9,10
  const fx1 = arr[8],
    fy1 = arr[9],
    fz1 = arr[10];

  // Row-major alternative forward vector guess (third row): indices 2,6,10
  const fx2 = arr[2],
    fy2 = arr[6],
    fz2 = arr[10];

  function computeYawPitch(fx, fy, fz) {
    const yaw = Math.atan2(fx, fz);
    const pitch = Math.atan2(-fy, Math.sqrt(fx * fx + fz * fz));
    return { yawDeg: Math.abs(rad2deg(yaw)), pitchDeg: Math.abs(rad2deg(pitch)) };
  }

  const a = computeYawPitch(fx1, fy1, fz1);
  const b = computeYawPitch(fx2, fy2, fz2);

  // Heuristic: pick the one with smaller total rotation (usually correct)
  const scoreA = a.yawDeg + a.pitchDeg;
  const scoreB = b.yawDeg + b.pitchDeg;

  return scoreA <= scoreB ? a : b;
}

function fallbackPoseFromLandmarks(faceLandmarks) {
  // Your original “nose vs eyes” approximation
  const leftEyeOuter = faceLandmarks[33];
  const rightEyeOuter = faceLandmarks[263];
  const noseTip = faceLandmarks[1];

  const eyeMid = mid(leftEyeOuter, rightEyeOuter);
  const eyeDist = dist2(leftEyeOuter, rightEyeOuter);
  if (!eyeDist || eyeDist < 1e-6) return null;

  const nx = (noseTip.x - eyeMid.x) / eyeDist;
  const ny = (noseTip.y - eyeMid.y) / eyeDist;

  const yawDeg = Math.abs(rad2deg(Math.atan(nx)));
  const pitchDeg = Math.abs(rad2deg(Math.atan(ny)));

  return { yawDeg, pitchDeg };
}

export function computeEyeContactScore(faceLandmarks, faceMatrix = null) {
  if (!faceLandmarks) return null;

  // 1) head pose angles (yaw/pitch)
  const pose = headPoseFromMatrix(faceMatrix) || fallbackPoseFromLandmarks(faceLandmarks);
  if (!pose) return null;

  const { yawDeg, pitchDeg } = pose;

  // 2) center on screen
  const noseTip = faceLandmarks[1];
  const centerDist = Math.sqrt((noseTip.x - 0.5) ** 2 + (noseTip.y - 0.5) ** 2);

  // penalties
  const yawPenalty = penaltyBetween(yawDeg, EYE_THRESH.yawGoodMax, EYE_THRESH.yawBadMax);
  const pitchPenalty = penaltyBetween(pitchDeg, EYE_THRESH.pitchGoodMax, EYE_THRESH.pitchBadMax);
  const centerPenalty = penaltyBetween(centerDist, EYE_THRESH.centerGoodMax, EYE_THRESH.centerBadMax);

  const weightedPenalty = clamp01(
    EYE_WEIGHTS.yaw * yawPenalty +
      EYE_WEIGHTS.pitch * pitchPenalty +
      EYE_WEIGHTS.center * centerPenalty
  );

  const score = Math.round(100 * (1 - weightedPenalty));

  return {
    score,
    metrics: {
      yawDeg,
      pitchDeg,
      centerDist,
      penalties: { yawPenalty, pitchPenalty, centerPenalty },
      usedMatrix: Boolean(headPoseFromMatrix(faceMatrix)),
    },
  };
}