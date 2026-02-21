import { useEffect, useState } from "react";
import "./ResultsPage.css";
import {
    LineChart,
    Line,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer
} from "recharts";


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

  function normalizeTimeline(arr){
    return (arr || []).map((item, index) => {
      // If backend returns just numbers: [0.1, 0.3, 0.9]
      if (typeof item === "number") {
        return { time: index, value: item };
      }

      // If backend returns objects: [{time: ..., value: ...}, ...]
      if (item && typeof item === "object") {
        const time =
          item.time ?? item.t ?? item.ts ?? item.x ?? item.frame ?? item.seconds ?? index;

        const value =
          item.value ?? item.score ?? item.y ?? item.prob ?? item.confidence ?? item.val ?? 0;

        return { time, value: Number(value) };
      }

      return { time: index, value: 0 };
    });  
  }

  const eyeData = useMemo(() => normalizeTimeline(eyeHistory), [eyeHistory]);
  const postureData = useMemo(() => normalizeTimeline(postureHistory), [postureHistory]);

  return (
    <div className="results-container">
      <h1 className="results-title">Interview Results</h1>
      <p className="results-subtitle">Your interview ended. Timeline data has been collected and stored.</p>

      {loading ? <p>Loading results...</p> : null}
      {error ? <p>{error}</p> : null}

      {!loading && !error ? (
        <>
          <div className="graph-card">
            <h2 className="graph-title">Eye Timeline</h2>
            <div className="graph-wrap">
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={eyeData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="time" />
                  <YAxis />
                  <Tooltip />
                  <Line type="monotone" dataKey="value" dot={false} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="graph-card">
            <h2 className="graph-title">Posture Timeline</h2>
            <div className="graph-wrap">
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={postureData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="time" />
                  <YAxis />
                  <Tooltip />
                  <Line type="monotone" dataKey="value" dot={false} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
        </>
      ) : null}
     

      <button onClick={onRestart}>Start New Interview</button>
    </div>
  );
}
