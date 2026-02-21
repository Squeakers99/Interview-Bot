import { useEffect, useState } from "react";
import "./ResultsPage.css";

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
        setEyeHistory(eyeJson.eye_timeline || []);
        setPostureHistory(postureJson.posture_timeline || []);
      } catch (e) {
        setError("Failed to load results.");
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  return (
    <div className="results-container">
      <h1 className="results-title">Interview Results</h1>
      <p className="results-subtitle">Your interview ended. Timeline data has been collected and stored.</p>

      {loading ? <p>Loading results...</p> : null}
      {error ? <p>{error}</p> : null}

      {!loading && !error ? (
        <>
          <p className="Eye-timeline">Eye timeline points: {eyeHistory.length}</p>
          <p className="Posture-timeline">Posture timeline points: {postureHistory.length}</p>
        </>
      ) : null}

      <button className="New-Interview" onClick={onRestart}>Start New Interview</button>
    </div>
  );
}
