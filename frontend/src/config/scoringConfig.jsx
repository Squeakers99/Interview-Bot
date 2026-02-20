export const VIDEO_W = 640;
export const VIDEO_H = 480;

// Throttle vision processing (saves CPU)
export const TARGET_FPS = 20; // 15–30 is reasonable
export const SMOOTHING_ALPHA = 0.15;

// What score counts as “good” for % tracking
export const GOOD_SCORE_THRESHOLD = 75;

// -----------------------------
// Model loading
// -----------------------------
export const WASM_BASE = "https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@latest/wasm";

export const POSE_MODEL_URL = "https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/1/pose_landmarker_lite.task";

export const FACE_MODEL_URL = "https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task";

// -----------------------------
// Posture scoring thresholds
// -----------------------------
export const POSTURE_THRESH = {
  // tilt = |yL - yR| / shoulderWidth
  tiltGoodMax: 0.06,
  tiltBadMax: 0.14,

  // headForward = |noseZ - shoulderMidZ| / shoulderWidth
  headForwardGoodMax: 0.08,
  headForwardBadMax: 0.20,

  // neckRatio = (shoulderMidY - earMidY) / shoulderWidth
  // bigger is better (more "neck length" / less slouch)
  neckGoodMin: 0.22,
  neckBadMin: 0.12,
};

export const POSTURE_WEIGHTS = {
  tilt: 0.30,
  head: 0.40,
  neck: 0.30,
};

// -----------------------------
// Eye-contact scoring thresholds
// -----------------------------
export const EYE_THRESH = {
  // yaw in degrees (from nose offset) - HORIZONTAL (x coord)
  yawGoodMax: 12,
  yawBadMax: 25,

  // pitch in degrees (from nose offset) - VERTICAL (y coord)
  pitchGoodMax: 18,
  pitchBadMax: 35,

  // distance from screen center (0.5,0.5)
  centerGoodMax: 0.22,
  centerBadMax: 0.40,
};

export const EYE_WEIGHTS = {
  yaw: 0.45,
  pitch: 0.35,
  center: 0.20,
};
