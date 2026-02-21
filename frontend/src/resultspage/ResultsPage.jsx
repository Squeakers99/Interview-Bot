import { useEffect, useMemo, useState } from "react";
import "./ResultsPage.css";
import TimelineChart from "./components/TimelineChart";
import { normalizeXY } from "./utils/normalizeXY";

export default function ResultsPage({ onRestart }) {
  const [eyeHistory, setEyeHistory] = useState([]);
  const [postureHistory, setPostureHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function load() {
      const apiBase = (import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000").replace(/\/$/, "");
      try {
        const [eyeRes, postureRes] = await Promise.all([
          fetch(`${apiBase}/results/eye_timeline`),
          fetch(`${apiBase}/results/posture_timeline`),
        ]);

        const eyeJson = await eyeRes.json();
        const postureJson = await postureRes.json();

        const eyePoints = Array.isArray(eyeJson) ? eyeJson : eyeJson.eye_timeline || [];
        const posturePoints = Array.isArray(postureJson) ? postureJson : postureJson.posture_timeline || [];

        setEyeHistory(eyePoints);
        setPostureHistory(posturePoints);
      } catch {
        setError("Failed to load results.");
      } finally {
        setLoading(false);
      }
    }

    load();
  }, []);

  const eyeData = useMemo(() => normalizeXY(eyeHistory), [eyeHistory]);
  const postureData = useMemo(() => normalizeXY(postureHistory), [postureHistory]);

  return (
    <div className="results-container">
      <header className="results-header">
        <h1 className="results-title">Interview Results</h1>
        <p className="results-subtitle">
          Your interview ended. Timeline data has been collected and stored.
        </p>
      </header>

      {loading ? <p>Loading results...</p> : null}
      {error ? <p>{error}</p> : null}

      {!loading && !error ? (
        <div className="results-charts">
          <TimelineChart title="Eye Timeline" data={eyeData} />
          <TimelineChart title="Posture Timeline" data={postureData} />
        </div>
      ) : null}

      <button className="results-button" onClick={onRestart}>
        Start New Interview
      </button>
    </div>
  );
}
