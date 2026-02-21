import { useState } from "react";
import VisionTracker from "./components/VisionTracker";

export default function App() {
  const [started, setStarted] = useState(false);
  const [starting, setStarting] = useState(false);
  const [startError, setStartError] = useState("");
  const [cameraStream, setCameraStream] = useState(null);

  async function startInterview() {
    setStartError("");
    setStarting(true);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
      setCameraStream(stream);
      setStarted(true);
    } catch (error) {
      setStartError("Camera/mic access is required to start.");
      console.error("[startInterview] camera precheck failed", error);
    } finally {
      setStarting(false);
    }
  }

  async function handleAnalysisResult() {
    const apiBase = (import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000").replace(/\/$/, "");
    try {
      const [eyeRes, postureRes] = await Promise.all([
        fetch(`${apiBase}/results/eye_timeline`),
        fetch(`${apiBase}/results/posture_timeline`),
      ]);

      const eyeData = await eyeRes.json();
      const postureData = await postureRes.json();

      console.log("[debug] eye_timeline", eyeData);
      console.log("[debug] posture_timeline", postureData);
    } catch (error) {
      console.error("[debug] failed to fetch timelines", error);
    }
  }

  if (!started) {
    return (
      <div className="app-shell" style={{ padding: 24 }}>
        <h1>Interview Bot</h1>
        <p>Click start when you're ready. We'll verify camera/mic first.</p>
        <button onClick={startInterview} disabled={starting}>
          {starting ? "Loading Camera..." : "Start Interview"}
        </button>
        {startError ? <p style={{ color: "#c62828", marginTop: 10 }}>{startError}</p> : null}
      </div>
    );
  }

  return (
    <div className="app-shell">
      <VisionTracker
        enabled={true}
        autoStartCamera={true}
        drawLandmarks={true}
        initialStream={cameraStream}
        onAnalysisResult={handleAnalysisResult}
        onEnd={() => {
          setStarted(false);
          setCameraStream(null);
        }}
      />
    </div>
  );
}
