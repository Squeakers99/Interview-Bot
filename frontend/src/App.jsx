import { useState } from "react";
import VisionTracker from "./components/VisionTracker";
import ScoreCard from "./components/ScoreCard";
import WelcomePage from "./welcomepage/WelcomePage";

export default function App() {
  const [started, setStarted] = useState(false);
  const [vision, setVision] = useState({
    postureScore: null,
    eyeScore: null,
    postureGoodPct: 0,
    eyeGoodPct: 0,
  });
  const [analysisResult, setAnalysisResult] = useState(null);

  if (!started) {
    return <WelcomePage onStart={() => setStarted(true)} />;
  }

  return (
    <div style={{ maxWidth: 1100, margin: "24px auto", fontFamily: "system-ui" }}>
      <h1 style={{ marginBottom: 6 }}>Vision Scoring (Modular)</h1>
      <p style={{ marginTop: 0, color: "#555" }}>
        MediaPipe runs in-browser. Copy these metrics to send to FastAPI later.
      </p>

      <VisionTracker
        enabled={true}
        autoStartCamera={false}
        drawLandmarks={true}
        onUpdate={setVision}
        onAnalysisResult={setAnalysisResult}
      />

      <div style={{ display: "flex", gap: 14, flexWrap: "wrap" }}>
        <div style={{ minWidth: 360, flex: 1 }}>
          <ScoreCard
            title="Posture"
            score={vision.postureScore}
            goodPct={vision.postureGoodPct}
            hint="Goal: upright, shoulders level, head not too far forward."
          />
          <ScoreCard
            title="Eye Contact"
            score={vision.eyeScore}
            goodPct={vision.eyeGoodPct}
            hint="Goal: face mostly forward and centered; don’t look away too long."
          />
        </div>

        <div style={{ minWidth: 360, flex: 1, padding: 14, border: "1px solid #ddd", borderRadius: 12 }}>
          <h3 style={{ marginTop: 0 }}>Metrics object</h3>
          <pre style={{ whiteSpace: "pre-wrap" }}>{JSON.stringify(vision, null, 2)}</pre>
        </div>

        <div style={{ minWidth: 360, flex: 1, padding: 14, border: "1px solid #ddd", borderRadius: 12 }}>
          <h3 style={{ marginTop: 0 }}>Analyze response</h3>
          <pre style={{ whiteSpace: "pre-wrap" }}>
            {analysisResult ? JSON.stringify(analysisResult, null, 2) : "No analysis yet. Stop camera to upload audio."}
          </pre>
        </div>
      </div>
    </div>
  );
}
