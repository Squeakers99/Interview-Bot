import { useEffect, useMemo, useState } from "react";
import "./ResultsPage.css";
import TimelineChart from "./components/TimelineChart";
import { normalizeXY } from "./utils/normalizeXY";

function averageScore(points) {
  if (!points.length) return 0;
  const total = points.reduce((sum, point) => sum + point.score, 0);
  return Math.round(total / points.length);
}

function sessionLength(points) {
  if (!points.length) return 0;
  return Math.max(0, Math.round(points[points.length - 1].timeSec));
}

function formatMMSS(totalSeconds) {
  const seconds = Math.max(0, Number(totalSeconds) || 0);
  const mm = String(Math.floor(seconds / 60)).padStart(2, "0");
  const ss = String(seconds % 60).padStart(2, "0");
  return `${mm}:${ss}`;
}

function decodeEscapedNewlines(value) {
  if (typeof value !== "string") return value;
  return value.replace(/\\n/g, "\n").replace(/\r\n/g, "\n");
}

function toReadableReview(value, indent = 0) {
  const pad = " ".repeat(indent);

  if (value == null) return `${pad}No LLM review available yet.`;
  if (typeof value === "string") return `${pad}${decodeEscapedNewlines(value)}`;
  if (typeof value === "number" || typeof value === "boolean") return `${pad}${String(value)}`;

  if (Array.isArray(value)) {
    if (!value.length) return `${pad}[]`;
    return value
      .map((item) => {
        if (typeof item === "string" || typeof item === "number" || typeof item === "boolean") {
          return `${pad}- ${decodeEscapedNewlines(String(item))}`;
        }
        return `${pad}-\n${toReadableReview(item, indent + 2)}`;
      })
      .join("\n");
  }

  if (typeof value === "object") {
    const entries = Object.entries(value);
    if (!entries.length) return `${pad}{}`;
    return entries
      .map(([key, val]) => {
        if (typeof val === "string" || typeof val === "number" || typeof val === "boolean") {
          return `${pad}${key}: ${decodeEscapedNewlines(String(val))}`;
        }
        return `${pad}${key}:\n${toReadableReview(val, indent + 2)}`;
      })
      .join("\n");
  }

  return `${pad}${String(value)}`;
}

export default function ResultsPage({ onRestart }) {
  const [eyeHistory, setEyeHistory] = useState([]);
  const [postureHistory, setPostureHistory] = useState([]);
  const [llmReview, setLlmReview] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function load() {
      const apiBase = (import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000").replace(/\/$/, "");
      try {
        const [eyeRes, postureRes, llmRes] = await Promise.all([
          fetch(`${apiBase}/results/eye_timeline`),
          fetch(`${apiBase}/results/posture_timeline`),
          fetch(`${apiBase}/results/llm_review`),
        ]);

        const eyeJson = await eyeRes.json();
        const postureJson = await postureRes.json();
        const llmJson = await llmRes.json();

        const eyePoints = Array.isArray(eyeJson) ? eyeJson : eyeJson.eye_timeline || [];
        const posturePoints = Array.isArray(postureJson) ? postureJson : postureJson.posture_timeline || [];

        setEyeHistory(eyePoints);
        setPostureHistory(posturePoints);
        setLlmReview(llmJson?.llm_review ?? null);
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
  const eyeAverage = useMemo(() => averageScore(eyeData), [eyeData]);
  const postureAverage = useMemo(() => averageScore(postureData), [postureData]);
  const totalDuration = useMemo(
    () => Math.max(sessionLength(eyeData), sessionLength(postureData)),
    [eyeData, postureData]
  );
  const llmReviewText = useMemo(() => toReadableReview(llmReview), [llmReview]);

  return (
    <main className="results-page">
      <section className="results-shell">
        <header className="results-header">
          <h1 className="results-title">Interview Results</h1>
          <p className="results-subtitle">Session summary and timeline breakdown.</p>
        </header>

        {loading ? (
          <section className="results-status-card">
            <h2>Loading results</h2>
            <p>Fetching eye and posture timelines from backend...</p>
          </section>
        ) : null}

        {error ? (
          <section className="results-status-card results-status-card--error">
            <h2>Could not load results</h2>
            <p>{error}</p>
          </section>
        ) : null}

        {!loading && !error ? (
          <>
            <section className="results-metrics">
              <article className="metric-card">
                <p className="metric-card__label">Eye Contact Avg</p>
                <p className="metric-card__value">{eyeAverage}%</p>
              </article>
              <article className="metric-card">
                <p className="metric-card__label">Posture Avg</p>
                <p className="metric-card__value">{postureAverage}%</p>
              </article>
              <article className="metric-card">
                <p className="metric-card__label">Session Length</p>
                <p className="metric-card__value">{formatMMSS(totalDuration)}</p>
              </article>
              <article className="metric-card">
                <p className="metric-card__label">Timeline Samples</p>
                <p className="metric-card__value">{Math.max(eyeData.length, postureData.length)}</p>
              </article>
            </section>

            <section className="results-charts">
              <TimelineChart title="Eye Timeline" data={eyeData} />
              <TimelineChart title="Posture Timeline" data={postureData} />
              <section className="graph-card llm-review-card">
                <h2 className="graph-title">LLM Review</h2>
                <div className="llm-review-content">
                  <pre className="llm-review-pre">{llmReviewText}</pre>
                </div>
              </section>
            </section>
          </>
        ) : null}

        <div className="results-actions">
          <button className="results-button" onClick={onRestart}>
            Start New Interview
          </button>
        </div>
      </section>
    </main>
  );
}
