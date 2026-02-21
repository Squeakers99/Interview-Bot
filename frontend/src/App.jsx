import { useState } from "react";
import VisionTracker from "./components/VisionTracker";
import ResultsPage from "./resultspage/ResultsPage";

export default function App() {
  const [view, setView] = useState("interview");

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

  if (view === "results") {
    return (
      <div className="app-shell">
        <ResultsPage onRestart={() => setView("interview")} />
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
        onEnd={() => setView("results")}
      />
    </div>
  );
}
