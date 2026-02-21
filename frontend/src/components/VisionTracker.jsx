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
import "./VisionTracker.css";
import AnalyzingPage from "../analyzing/AnalyzingPage";

const INTERVIEW_TIMINGS = {
  thinkingSeconds: 30,
  responseSeconds: 90,
};

function formatElapsedSeconds(msSinceStart) {
  const seconds = Math.max(0, msSinceStart) / 1000;
  return Number(seconds.toFixed(2));
}

function secondsToMMSS(totalSeconds) {
  const safeSeconds = Math.max(0, totalSeconds || 0);
  const minutes = Math.floor(safeSeconds / 60);
  const seconds = safeSeconds % 60;
  return `${String(minutes).padStart(2, "0")}:${String(seconds).padStart(2, "0")}`;
}

export default function VisionTracker({
  enabled = true,
  autoStartCamera = true,
  drawLandmarks = true,
  initialStream = null,
  prompt = null,
  onUpdate,
  onAnalysisResult,
  onEnd, // ✅ NEW: lets parent return to entry page
}) {
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const streamRef = useRef(null);

  const poseRef = useRef(null);
  const faceRef = useRef(null);
  const drawingRef = useRef(null);
  const recorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const latestMetricsRef = useRef({});
  const postureTimelineRef = useRef([]);
  const eyeTimelineRef = useRef([]);
  const timelineStartMsRef = useRef(0);

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
  const [phase, setPhase] = useState(autoStartCamera ? "thinking" : "idle");
  const [timeLeft, setTimeLeft] = useState(INTERVIEW_TIMINGS.thinkingSeconds);

  // These are used in uploadAudio summary; must exist (not just setters)
  const [postureScoreUI, setPostureScoreUI] = useState(null);
  const [eyeScoreUI, setEyeScoreUI] = useState(null);

  // Avoid stale phase inside requestAnimationFrame loop
  const phaseRef = useRef("idle");
  useEffect(() => {
    phaseRef.current = phase;
  }, [phase]);

  // ------------------ Load Models ------------------
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

    if (enabled) loadModels();

    return () => {
      cancelled = true;
      stopLoop();
      stopCamera();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [enabled]);

  // ------------------ Auto Start Camera ------------------
  useEffect(() => {
    if (!enabled) return;
    if (!modelsReady) return;
    if (!autoStartCamera) return;
    if (cameraOn) return;
    if (initialStream) {
      startCamera(initialStream);
      return;
    }
    startCamera();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [enabled, modelsReady, autoStartCamera, cameraOn, initialStream]);

  // ------------------ Preview Loop Control ------------------
  useEffect(() => {
    if (!enabled) return;
    if (!modelsReady || !cameraOn) return;

    // Preview should run during THINKING + RESPONSE
    const shouldPreview = phase === "thinking" || phase === "response";

    if (shouldPreview) {
      setStatus(
        phase === "response"
          ? "Camera on. Tracking enabled."
          : "Thinking time running. Preview enabled."
      );
      startLoop();
    } else {
      setStatus("Camera on. Preview paused.");
      stopLoop();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [enabled, modelsReady, cameraOn, phase]);

  // ------------------ Countdown Timer ------------------
  useEffect(() => {
    if (!enabled) return;
    if (!cameraOn) return;
    if (phase !== "thinking" && phase !== "response") return;
    if (timeLeft <= 0) return;

    const timer = setTimeout(() => {
      setTimeLeft((prev) => prev - 1);
    }, 1000);

    return () => clearTimeout(timer);
  }, [enabled, cameraOn, phase, timeLeft]);

  // ------------------ Phase Transitions ------------------
  useEffect(() => {
    if (!enabled) return;
    if (!cameraOn) return;
    if (timeLeft > 0) return;

    if (phase === "thinking") {
      setPhase("response");
      setTimeLeft(INTERVIEW_TIMINGS.responseSeconds);
      setStatus("Response time started.");
      timelineStartMsRef.current = performance.now();
      if (streamRef.current) startAudioRecording(streamRef.current);
      return;
    }

    if (phase === "response") {
      endInterviewAndUpload();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [enabled, cameraOn, phase, timeLeft]);

  // ------------------ Camera ------------------
  async function startCamera(preloadedStream = null) {
    try {
      setPhase("thinking");
      setTimeLeft(INTERVIEW_TIMINGS.thinkingSeconds);
      let stream = preloadedStream;
      if (!stream) {
        setStatus("Requesting camera...");
        stream = await navigator.mediaDevices.getUserMedia({
          video: { width: VIDEO_W, height: VIDEO_H },
          audio: true,
        });
      } else {
        setStatus("Starting camera...");
      }

      streamRef.current = stream;
      if (videoRef.current) videoRef.current.srcObject = stream;

      // Wait for video to have data before playing/drawing
      await new Promise((resolve) => {
        const v = videoRef.current;
        if (!v) return resolve();
        if (v.readyState >= 2) return resolve();
        v.onloadeddata = () => resolve();
      });

      await videoRef.current.play();

      const ctx = canvasRef.current.getContext("2d");
      drawingRef.current = new DrawingUtils(ctx);

      resetAggregates();
      setPhase("thinking");
      setTimeLeft(INTERVIEW_TIMINGS.thinkingSeconds);

      setCameraOn(true);
      setStatus("Thinking time started.");
    } catch (e) {
      setStatus(`Camera error: ${String(e)}`);
    }
  }

  function stopCamera() {
    const stream = streamRef.current || videoRef.current?.srcObject;
    stream?.getTracks?.().forEach((t) => t.stop());
    streamRef.current = null;
    if (videoRef.current) videoRef.current.srcObject = null;
    setCameraOn(false);
  }

  // ------------------ End / Upload ------------------
  async function endInterviewAndUpload() {
    setPhase("finishing");
    stopLoop();
    try {
      await stopAudioRecording(true);
      setStatus("Response time ended. Audio uploaded.");
    } catch (e) {
      setStatus(`Auto-stop error: ${String(e)}`);
    } finally {
      stopCamera();
      setPhase("done");
      setTimeLeft(0);
      onEnd?.(); // ✅ NEW: go back to entry
    }
  }

  async function endInterviewByUser() {
    setPhase("finishing");
    stopLoop();
    try {
      if (recorderRef.current) {
        await stopAudioRecording(true);
        setStatus("Interview ended and audio uploaded.");
      } else {
        setStatus("Interview ended.");
      }
    } catch (e) {
      setStatus(`Stop/upload error: ${String(e)}`);
    } finally {
      stopCamera();
      setPhase("idle");
      setTimeLeft(INTERVIEW_TIMINGS.thinkingSeconds);
      onEnd?.(); // ✅ NEW: go back to entry
    }
  }

  function resetAggregates() {
    aggRef.current = { frames: 0, postureGoodFrames: 0, eyeGoodFrames: 0 };
    setPostureScoreUI(null);
    setEyeScoreUI(null);
    lastFrameTimeRef.current = 0;
    postureTimelineRef.current = [];
    eyeTimelineRef.current = [];
    timelineStartMsRef.current = 0;
  }

  function startLoop() {
    if (rafRef.current) return;
    rafRef.current = requestAnimationFrame(loop);
  }

  function stopLoop() {
    if (rafRef.current) cancelAnimationFrame(rafRef.current);
    rafRef.current = null;
  }

  // ------------------ Audio ------------------
  function startAudioRecording(stream) {
    if (!window.MediaRecorder) {
      setStatus("MediaRecorder not supported in this browser.");
      return;
    }
    try {
      audioChunksRef.current = [];
      const audioTracks = stream.getAudioTracks();
      if (!audioTracks.length) {
        setStatus("No microphone track found.");
        return;
      }
      const audioOnlyStream = new MediaStream(audioTracks);
      let options;
      if (MediaRecorder.isTypeSupported("audio/webm;codecs=opus")) {
        options = { mimeType: "audio/webm;codecs=opus" };
      }
      const recorder = options
        ? new MediaRecorder(audioOnlyStream, options)
        : new MediaRecorder(audioOnlyStream);

      recorderRef.current = recorder;
      recorder.ondataavailable = (event) => {
        if (event.data && event.data.size > 0) audioChunksRef.current.push(event.data);
      };
      recorder.start(250);
    } catch (e) {
      setStatus(`Audio record error: ${String(e)}`);
    }
  }

  async function stopAudioRecording(uploadAfterStop) {
    const recorder = recorderRef.current;
    if (!recorder) return;

    if (recorder.state !== "inactive") {
      await new Promise((resolve, reject) => {
        const onStop = () => resolve();
        const onError = (event) => reject(event?.error || new Error("Recorder error"));
        recorder.addEventListener("stop", onStop, { once: true });
        recorder.addEventListener("error", onError, { once: true });
        recorder.stop();
      });
    }

    const type = recorder.mimeType || "audio/webm";
    const blob = new Blob(audioChunksRef.current, { type });
    recorderRef.current = null;
    audioChunksRef.current = [];
    if (uploadAfterStop) await uploadAudio(blob);
  }

  async function uploadAudio(audioBlob) {
    setStatus("Uploading audio for analysis...");
    const formData = new FormData();
    const ext = audioBlob.type.includes("ogg") ? "ogg" : "webm";
    const filename = `interview-audio.${ext}`;

    const interviewSummary = {
      postureScore: latestMetricsRef.current?.postureScore ?? postureScoreUI ?? null,
      eyeScore: latestMetricsRef.current?.eyeScore ?? eyeScoreUI ?? null,
    };
    const interviewTimelines = {
      posture_timeline: postureTimelineRef.current,
      eye_timeline: eyeTimelineRef.current,
    };

    formData.append("audio", audioBlob, filename);
    formData.append("prompt_id", prompt?.id || "");
    formData.append("prompt_text", prompt?.text || "");
    formData.append("prompt_type", prompt?.type || "");
    formData.append("prompt_difficulty", prompt?.difficulty || "");
    formData.append("vision_metrics", JSON.stringify(latestMetricsRef.current || {}));
    formData.append("interview_summary", JSON.stringify(interviewSummary));
    formData.append("interview_timelines", JSON.stringify(interviewTimelines));

    const apiBase = (import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000").replace(/\/$/, "");
    const response = await fetch(`${apiBase}/analyze`, { method: "POST", body: formData });
    if (!response.ok) throw new Error(`Analyze failed with status ${response.status}`);
    const data = await response.json();
    onAnalysisResult?.(data);
    setStatus(`Uploaded ${filename} (${audioBlob.size} bytes).`);
  }

  // ------------------ Render Loop ------------------
  function loop(t) {
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
    const currentPhase = phaseRef.current;

    // Always draw the live camera feed (works during THINKING too)
    const ctx = canvas.getContext("2d");
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

    // THINKING: preview only (no detection/scoring)
    if (currentPhase !== "response") {
      rafRef.current = requestAnimationFrame(loop);
      return;
    }

    // RESPONSE: detection + scoring
    const poseRes = pose.detectForVideo(video, now);
    const faceRes = face.detectForVideo(video, now);

    let posture = null;
    if (poseRes?.landmarks?.length) posture = computePostureScore(poseRes.landmarks[0]);

    let eye = null;
    if (faceRes?.faceLandmarks?.length) {
      const matrix = faceRes.facialTransformationMatrixes?.[0] || null;
      eye = computeEyeContactScore(faceRes.faceLandmarks[0], matrix);
    }

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

    const elapsedMs = now - (timelineStartMsRef.current || now);
    const timestamp = formatElapsedSeconds(elapsedMs);

    postureTimelineRef.current.push({ timestamp, percentage: postureGoodPct });
    eyeTimelineRef.current.push({ timestamp, percentage: eyeGoodPct });

    onUpdate?.({
      postureScore: posture?.score ?? null,
      eyeScore: eye?.score ?? null,
      postureGoodPct,
      eyeGoodPct,
      postureMetrics: posture?.metrics ?? null,
      eyeMetrics: eye?.metrics ?? null,
    });

    latestMetricsRef.current = {
      postureScore: posture?.score ?? null,
      eyeScore: eye?.score ?? null,
      postureGoodPct,
      eyeGoodPct,
      postureMetrics: posture?.metrics ?? null,
      eyeMetrics: eye?.metrics ?? null,
    };

    if (drawLandmarks && drawingRef.current) {
      if (poseRes?.landmarks?.length) {
        drawingRef.current.drawLandmarks(poseRes.landmarks[0], { radius: 2 });
      }
      if (faceRes?.faceLandmarks?.length) {
        drawingRef.current.drawLandmarks(faceRes.faceLandmarks[0], { radius: 0.6 });
      }
    }

    rafRef.current = requestAnimationFrame(loop);
  }

  if (!enabled) return null;
  if (phase === "finishing") return <AnalyzingPage />;

  return (
    <div className="vision-tracker">
      <div className="vision-tracker__frame">
        {/* IMPORTANT: muted helps autoplay reliability */}
        <video ref={videoRef} muted className="vision-tracker__video-hidden" playsInline />
        <canvas ref={canvasRef} width={VIDEO_W} height={VIDEO_H} className="vision-tracker__canvas" />

        <div className="vision-tracker__center-overlay">
          <button
            onClick={endInterviewByUser}
            className="vision-btn vision-btn--danger vision-btn--end"
            disabled={!cameraOn || phase !== "response"}
          >
            End Interview
          </button>
        </div>

        <div className="vision-tracker__timer-overlay">
          <div className="vision-tracker__timer-badge">{secondsToMMSS(timeLeft)}</div>
        </div>

        <div className="vision-tracker__phase-overlay">
          <div className="vision-tracker__phase-badge">Phase: {phase.toUpperCase()}</div>
        </div>

        {/* Optional debug: show status */}
        {/* <div style={{ position: "absolute", bottom: 10, left: 10, fontSize: 12, opacity: 0.8 }}>{status}</div> */}
      </div>
    </div>
  );
}
