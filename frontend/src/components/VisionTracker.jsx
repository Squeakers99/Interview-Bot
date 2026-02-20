import { useEffect, useRef, useState } from "react";
import {
  FilesetResolver,
  PoseLandmarker,
  FaceLandmarker,
  DrawingUtils,
} from "@mediapipe/tasks-vision";

import {
  VIDEO_W,
  VIDEO_H,
  TARGET_FPS,
  SMOOTHING_ALPHA,
  GOOD_SCORE_THRESHOLD,
  WASM_BASE,
  POSE_MODEL_URL,
  FACE_MODEL_URL,
} from "../config/scoringConfig";

import { ema } from "../utils/math";
import { computePostureScore } from "../utils/scoringPosture";
import { computeEyeContactScore } from "../utils/scoringEye";

/**
 * VisionTracker:
 * - loads MediaPipe models once
 * - starts/stops camera
 * - runs vision loop only when enabled=true
 * - throttles FPS, smooths scores, aggregates % good-time
 */
export default function VisionTracker({
  enabled = true,          // parent can pause tracking
  autoStartCamera = false, // optional convenience
  drawLandmarks = true,    // disable if too slow
  onUpdate,                // receives metrics object each frame
}) {
  const videoRef = useRef(null);
  const canvasRef = useRef(null);

  const poseRef = useRef(null);
  const faceRef = useRef(null);
  const drawingRef = useRef(null);

  const rafRef = useRef(null);
  const lastFrameTimeRef = useRef(0);

  const aggRef = useRef({
    frames: 0,
    postureGoodFrames: 0,
    eyeGoodFrames: 0,
  });

  const [modelsReady, setModelsReady] = useState(false);
  const [cameraOn, setCameraOn] = useState(false);
  const [status, setStatus] = useState("Loading models...");

  const [postureScoreUI, setPostureScoreUI] = useState(null);
  const [eyeScoreUI, setEyeScoreUI] = useState(null);

  // Load models once
  useEffect(() => {
    let cancelled = false;

    async function loadModels() {
      try {
        setStatus("Loading MediaPipe WASM...");
        const vision = await FilesetResolver.forVisionTasks(WASM_BASE);

        setStatus("Loading Pose model...");
        const pose = await PoseLandmarker.createFromOptions(vision, {
          baseOptions: { modelAssetPath: POSE_MODEL_URL },
          runningMode: "VIDEO",
          numPoses: 1,
        });

        setStatus("Loading Face model...");
        const face = await FaceLandmarker.createFromOptions(vision, {
          baseOptions: { modelAssetPath: FACE_MODEL_URL },
          runningMode: "VIDEO",
          numFaces: 1,
          outputFacialTransformationMatrixes: true,
          outputFaceBlendshapes: false,
        });

        if (cancelled) return;

        poseRef.current = pose;
        faceRef.current = face;
        setModelsReady(true);
        setStatus("Models loaded.");
      } catch (e) {
        setStatus(`Model load failed: ${String(e)}`);
      }
    }

    loadModels();

    return () => {
      cancelled = true;
      stopLoop();
      stopCamera();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Auto-start camera if requested
  useEffect(() => {
    if (!modelsReady) return;
    if (!autoStartCamera) return;
    if (!cameraOn) startCamera();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [modelsReady, autoStartCamera]);

  // Start/stop loop based on enabled
  useEffect(() => {
    if (!modelsReady || !cameraOn) return;

    if (enabled) {
      setStatus("Camera on. Tracking enabled.");
      startLoop();
    } else {
      setStatus("Camera on. Tracking paused.");
      stopLoop();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [enabled, modelsReady, cameraOn]);

  async function startCamera() {
    try {
      setStatus("Requesting camera...");
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { width: VIDEO_W, height: VIDEO_H },
        audio: false,
      });

      videoRef.current.srcObject = stream;
      await videoRef.current.play();

      const ctx = canvasRef.current.getContext("2d");
      drawingRef.current = new DrawingUtils(ctx);

      resetAggregates();

      setCameraOn(true);
      setStatus(enabled ? "Camera on. Tracking enabled." : "Camera on. Tracking paused.");
    } catch (e) {
      setStatus(`Camera error: ${String(e)}`);
    }
  }

  function stopCamera() {
    const stream = videoRef.current?.srcObject;
    stream?.getTracks?.().forEach((t) => t.stop());
    if (videoRef.current) videoRef.current.srcObject = null;

    setCameraOn(false);
  }

  function resetAggregates() {
    aggRef.current = { frames: 0, postureGoodFrames: 0, eyeGoodFrames: 0 };
    setPostureScoreUI(null);
    setEyeScoreUI(null);
    lastFrameTimeRef.current = 0;
  }

  function startLoop() {
    if (rafRef.current) return;
    rafRef.current = requestAnimationFrame(loop);
  }

  function stopLoop() {
    if (rafRef.current) cancelAnimationFrame(rafRef.current);
    rafRef.current = null;
  }

  function loop(t) {
    // FPS throttle
    const minDelta = 1000 / TARGET_FPS;
    if (t - lastFrameTimeRef.current < minDelta) {
      rafRef.current = requestAnimationFrame(loop);
      return;
    }
    lastFrameTimeRef.current = t;

    const video = videoRef.current;
    const canvas = canvasRef.current;
    const pose = poseRef.current;
    const face = faceRef.current;

    if (!video || !canvas || !pose || !face) {
      rafRef.current = requestAnimationFrame(loop);
      return;
    }

    const now = performance.now();
    const poseRes = pose.detectForVideo(video, now);
    const faceRes = face.detectForVideo(video, now);

    // Draw base video frame
    const ctx = canvas.getContext("2d");
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

    let posture = null;
    if (poseRes?.landmarks?.length) posture = computePostureScore(poseRes.landmarks[0]);

    let eye = null;
    if (faceRes?.faceLandmarks?.length) {
      const matrix = faceRes.facialTransformationMatrixes?.[0] || null;
      eye = computeEyeContactScore(faceRes.faceLandmarks[0], matrix);
    }

    // Aggregates
    aggRef.current.frames += 1;

    if (posture?.score != null) {
      setPostureScoreUI((prev) => Math.round(ema(prev, posture.score, SMOOTHING_ALPHA)));
      if (posture.score >= GOOD_SCORE_THRESHOLD) aggRef.current.postureGoodFrames += 1;
    }

    if (eye?.score != null) {
      setEyeScoreUI((prev) => Math.round(ema(prev, eye.score, SMOOTHING_ALPHA)));
      if (eye.score >= GOOD_SCORE_THRESHOLD) aggRef.current.eyeGoodFrames += 1;
    }

    const frames = aggRef.current.frames || 1;
    const postureGoodPct = Math.round((100 * aggRef.current.postureGoodFrames) / frames);
    const eyeGoodPct = Math.round((100 * aggRef.current.eyeGoodFrames) / frames);

    // Emit metrics
    onUpdate?.({
      postureScore: posture?.score ?? null,
      eyeScore: eye?.score ?? null,
      postureGoodPct,
      eyeGoodPct,
      postureMetrics: posture?.metrics ?? null,
      eyeMetrics: eye?.metrics ?? null,
    });

    // Optional landmark drawing
    if (drawLandmarks && drawingRef.current) {
      if (poseRes?.landmarks?.length) drawingRef.current.drawLandmarks(poseRes.landmarks[0], { radius: 2 });
      if (faceRes?.faceLandmarks?.length) drawingRef.current.drawLandmarks(faceRes.faceLandmarks[0], { radius: 0.6 });
    }

    rafRef.current = requestAnimationFrame(loop);
  }

  return (
    <div style={{ marginBottom: 16 }}>
      <div style={{ display: "flex", gap: 10, marginBottom: 10, flexWrap: "wrap" }}>
        {!cameraOn ? (
          <button onClick={startCamera} disabled={!modelsReady} style={btnPrimary}>
            Start Camera
          </button>
        ) : (
          <button
            onClick={() => {
              stopLoop();
              stopCamera();
              setStatus("Camera stopped.");
            }}
            style={btnDanger}
          >
            Stop Camera
          </button>
        )}

        <div style={{ color: "#666", alignSelf: "center" }}>Status: {status}</div>

        <div style={{ color: "#444", alignSelf: "center" }}>
          <b>Live:</b> Posture {postureScoreUI ?? "--"} · Eye {eyeScoreUI ?? "--"}
        </div>
      </div>

      <div style={{ position: "relative", width: VIDEO_W, height: VIDEO_H }}>
        <video ref={videoRef} style={{ display: "none" }} playsInline />
        <canvas
          ref={canvasRef}
          width={VIDEO_W}
          height={VIDEO_H}
          style={{ border: "1px solid #ddd", borderRadius: 12 }}
        />
      </div>

      <div style={{ marginTop: 8, fontSize: 12, color: "#666" }}>
        Tracking is <b>{enabled ? "ON" : "PAUSED"}</b>. FPS target: {TARGET_FPS}.
      </div>
    </div>
  );
}

const btnBase = {
  padding: "10px 14px",
  borderRadius: 10,
  border: "1px solid #ddd",
  cursor: "pointer",
  fontWeight: 700,
};

const btnPrimary = { ...btnBase, background: "#111", color: "white", borderColor: "#111" };
const btnDanger = { ...btnBase, background: "#fff", borderColor: "#e0a0a0", color: "#9a1b1b" };