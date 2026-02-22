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

function toTitle(value) {
  const raw = String(value || "").trim();
  if (!raw) return "N/A";
  return raw.charAt(0).toUpperCase() + raw.slice(1).toLowerCase();
}

function splitFeedbackBlock(value) {
  if (!value) return [];
  const normalized = String(value).replace(/\\n/g, "\n");
  return normalized
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean)
    .map((line) => line.replace(/^[:\-\*]\s*/, ""))
    .map((line) => line.replace(/^:\s*/, ""))
    .filter(Boolean);
}

function scoreValue(value) {
  if (value === null || value === undefined || value === "") return "N/A";
  return String(value);
}

function totalScoreLabel(value) {
  const raw = String(value ?? "").trim();
  if (!raw) return "N/A";
  return raw.includes("/100") ? raw : `${raw}/100`;
}

function difficultyLabel(value) {
  const raw = String(value ?? "").trim();
  const map = {
    "1": "Easy",
    "2": "Medium",
    "3": "Hard",
    "4": "Expert",
    "5": "Master",
    easy: "Easy",
    medium: "Medium",
    hard: "Hard",
    expert: "Expert",
    master: "Master",
  };
  return map[raw.toLowerCase()] || toTitle(raw);
}

function fallbackParsedFromReview(llmReview) {
  const text = String(llmReview || "");
  if (!text) return {};
  const grab = (label, endToken) => {
    if (!text.includes(label)) return "";
    try {
      return text.split(label)[1].split(endToken)[0].trim();
    } catch {
      return "";
    }
  };
  return {
    clarity_score: grab("Communication Clarity: ", "/25"),
    content_score: grab("Content & Substance: ", "/25"),
    professionalism_score: grab("Professionalism: ", "/20"),
    body_language_score: grab("Body Language: ", "/15"),
    vocal_delivery_score: grab("Vocal Delivery: ", "/15"),
    total_score: grab("TOTAL SCORE: ", "(") || grab("TOTAL SCORE: ", "/100"),
  };
}

function renderList(items, emptyLabel) {
  if (!items.length) {
    return <p className="parsed-empty">{emptyLabel}</p>;
  }
  return (
    <ul className="parsed-list">
      {items.map((item, index) => (
        <li key={`${item}-${index}`}>{item}</li>
      ))}
    </ul>
  );
}

export default function ResultsPage({ onRestart }) {
  const [eyeHistory, setEyeHistory] = useState([]);
  const [postureHistory, setPostureHistory] = useState([]);
  const [fullResults, setFullResults] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function load() {
      const apiBase = (import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000").replace(/\/$/, "");
      try {
        const [eyeRes, postureRes, fullRes] = await Promise.all([
          fetch(`${apiBase}/results/eye_timeline`),
          fetch(`${apiBase}/results/posture_timeline`),
          fetch(`${apiBase}/results/full`),
        ]);

        const eyeJson = await eyeRes.json();
        const postureJson = await postureRes.json();
        const fullJson = await fullRes.json();

        const eyePoints = Array.isArray(eyeJson) ? eyeJson : eyeJson.eye_timeline || [];
        const posturePoints = Array.isArray(postureJson) ? postureJson : postureJson.posture_timeline || [];

        setEyeHistory(eyePoints);
        setPostureHistory(posturePoints);
        setFullResults(fullJson?.results || {});
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
  const converterParsed = fullResults?.converter_parsed || {};
  const parsedFallback = useMemo(
    () => fallbackParsedFromReview(fullResults?.llm_review),
    [fullResults?.llm_review]
  );
  const parsed = { ...parsedFallback, ...converterParsed };
  const doingWellItems = useMemo(() => splitFeedbackBlock(parsed.doing_well), [parsed.doing_well]);
  const mustImproveItems = useMemo(() => splitFeedbackBlock(parsed.must_improve), [parsed.must_improve]);
  const habitsItems = useMemo(() => splitFeedbackBlock(parsed.habits_to_keep), [parsed.habits_to_keep]);
  const actionPlanItems = useMemo(() => splitFeedbackBlock(parsed.action_plan), [parsed.action_plan]);

  const handleDownload = async () => { // added download section here
    const apiBase = (import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000").replace(/\/$/, "");
    const res = await fetch(`${apiBase}/results/interview/pdf`);
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "interview-results.pdf";
    a.click();
    URL.revokeObjectURL(url);  
  };

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
            </section>

            <section className="results-charts">
              <TimelineChart title="Eye Timeline" data={eyeData} />
              <TimelineChart title="Posture Timeline" data={postureData} />
              <section className="graph-card parsed-summary-card">
                <h2 className="graph-title">Interview Breakdown</h2>
                <div className="parsed-meta">
                  <p className="parsed-meta-question">
                    <strong>Question:</strong> {parsed.question || fullResults?.prompt_text || "N/A"}
                  </p>
                  <div className="parsed-meta-row">
                    <p><strong>Type:</strong> {toTitle(parsed.type || fullResults?.prompt_type || "N/A")}</p>
                    <p>
                      <strong>Difficulty:</strong>{" "}
                      {difficultyLabel(parsed.difficulty || fullResults?.prompt_difficulty || "N/A")}
                    </p>
                  </div>
                </div>
                <div className="parsed-score-grid">
                  <div className="parsed-score-item">
                    <span>Communication</span>
                    <strong>{scoreValue(parsed.clarity_score)}/25</strong>
                  </div>
                  <div className="parsed-score-item">
                    <span>Content</span>
                    <strong>{scoreValue(parsed.content_score)}/25</strong>
                  </div>
                  <div className="parsed-score-item">
                    <span>Professionalism</span>
                    <strong>{scoreValue(parsed.professionalism_score)}/20</strong>
                  </div>
                  <div className="parsed-score-item">
                    <span>Body Language</span>
                    <strong>{scoreValue(parsed.body_language_score)}/15</strong>
                  </div>
                  <div className="parsed-score-item">
                    <span>Vocal Delivery</span>
                    <strong>{scoreValue(parsed.vocal_delivery_score)}/15</strong>
                  </div>
                  <div className="parsed-score-item parsed-score-item--total">
                    <span>Total</span>
                    <strong>{totalScoreLabel(parsed.total_score)}</strong>
                  </div>
                </div>
              </section>
            </section>

            <section className="results-analysis-grid">
              <article className="analysis-card">
                <h3>What You Are Doing Well</h3>
                {renderList(doingWellItems, "No strengths captured.")}
              </article>
              <article className="analysis-card">
                <h3>What You Must Improve</h3>
                {renderList(mustImproveItems, "No improvement notes captured.")}
              </article>
              <article className="analysis-card">
                <h3>Habits To Keep</h3>
                {renderList(habitsItems, "No habits captured.")}
              </article>
              <article className="analysis-card">
                <h3>Action Plan</h3>
                {renderList(actionPlanItems, "No action plan captured.")}
              </article>
            </section>
          </>
        ) : null}

        <div className="results-actions">
          <button className="results-button" onClick={onRestart}>
            Start New Interview
          </button>

           <button className="results-button" onClick={handleDownload}>
              Download Results
           </button>

        </div>

        
      </section>
    </main>
  );
}
