import { useState } from "react";
import VisionTracker from "./components/VisionTracker";

export default function App() {
  const [started, setStarted] = useState(false);

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
        <p>Click start when you’re ready. We’ll ask for camera permission.</p>
        <button onClick={() => setStarted(true)}>Start Interview</button>
      </div>
    );
  }

  return (
    <div className="app-shell">
      <VisionTracker
        enabled={true}
        autoStartCamera={true}
        drawLandmarks={true}
        onAnalysisResult={handleAnalysisResult}
        onEnd={() => setStarted(false)} // add this prop if you want End Interview to go back
      />
    </div>
  );
}