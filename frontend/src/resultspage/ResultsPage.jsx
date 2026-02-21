import { useEffect,useMemo, useState } from "react";
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

        const eyePoints = Array.isArray(eyeJson) ? eyeJson : (eyeJson.eye_timeline || []);
        const posturePoints = Array.isArray(postureJson) ? postureJson : (postureJson.posture_timeline || []);

        setEyeHistory(eyePoints);
        setPostureHistory(posturePoints);
      } catch (e) {
        setError("Failed to load results.");
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  
function normalizeXY(arr) {
    return (arr || [])
      .map((p, i) => {
        const isPair = Array.isArray(p);
        let timeSec = Number(isPair ? p[0] : (p?.x ?? p?.timestamp ?? i));
        let score = Number(isPair ? p[1] : (p?.y ?? p?.score ?? p?.percentage ?? 0));

        // if x is milliseconds, convert to seconds (common)
        if (Number.isFinite(timeSec) && timeSec > 1000) timeSec = timeSec / 1000;

        // if y is 0..1, convert to 0..100
        if (Number.isFinite(score) && score <= 1) score = score * 100;

        // clamp score to 0..100
        score = Math.max(0, Math.min(100, score));

        return { timeSec, score };
      })
      .sort((a, b) => a.timeSec - b.timeSec);
  }

  const eyeData = useMemo(() => normalizeXY(eyeHistory), [eyeHistory]);
  const postureData = useMemo(() => normalizeXY(postureHistory), [postureHistory]);

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
                  <XAxis 
                  dataKey="timeSec" 
                  type = "number"
                  domain={[0, "dataMax"]}
                  tickFormatter={(t)=> `${t}`}
                  />
                  <YAxis domain={[0,100]} />
                  <Tooltip />
                  <Line type="monotone" dataKey="score" dot={false} />
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
                  <XAxis 
                  dataKey="timeSec"
                  type = "number"
                  domain ={[0, "dataMax"]} 
                  tickFormatter={(t)=> `${t}`}
                  />
                  <YAxis domain={[0,100]} />
                  <Tooltip />
                  <Line type="monotone" dataKey="score" dot={false} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
        </>
      ) : null}
     

      <button className="New-Interview" onClick={onRestart}>Start New Interview</button>
    </div>
  );
}
