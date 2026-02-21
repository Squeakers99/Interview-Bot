import { useCallback, useEffect, useState } from "react";
import "./App.css";
import VisionTracker from "./components/VisionTracker";
import ResultsPage from "./resultspage/ResultsPage";
import AnalyzingPage from "./analyzing/AnalyzingPage";

const FALLBACK_PROMPT = {
  id: "fallback-prompt",
  text: "Tell me about yourself and background.",
  type: "general",
  difficulty: "easy",
  good_signals: [],
  red_flags: [],
};

function formatLabel(value) {
  const safe = String(value || "").trim().toLowerCase();
  if (!safe || safe === "all") return "All";
  return safe.charAt(0).toUpperCase() + safe.slice(1);
}

export default function App({ promptCategory = "all", promptDifficulty = "all", onReturnHome }) {
  const [view, setView] = useState("interview");
  const [prompt, setPrompt] = useState(null);
  const [promptLoading, setPromptLoading] = useState(true);
  const [promptError, setPromptError] = useState("");
  const [interviewRound, setInterviewRound] = useState(0);
  const [trackerPhase, setTrackerPhase] = useState("idle");

  const apiBase = (import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000").replace(/\/$/, "");

  const loadPrompt = useCallback(async () => {
    setPromptLoading(true);
    setPromptError("");

    try {
      const params = new URLSearchParams({
        type: promptCategory || "all",
        difficulty: promptDifficulty || "all",
      });

      const response = await fetch(`${apiBase}/prompt/random?${params.toString()}`);
      if (!response.ok) {
        throw new Error(`Prompt request failed (${response.status})`);
      }

      const payload = await response.json();
      if (!payload?.prompt?.text) {
        throw new Error("Prompt response was empty.");
      }

      setPrompt(payload.prompt);
    } catch (error) {
      setPrompt(FALLBACK_PROMPT);
      setPromptError("Could not load a filtered prompt from backend. Showing a fallback question.");
      console.error("[debug] prompt fetch failed", error);
    } finally {
      setPromptLoading(false);
    }
  }, [apiBase, promptCategory, promptDifficulty]);

  useEffect(() => {
    if (view !== "interview") return;
    loadPrompt();
  }, [view, interviewRound, loadPrompt]);

  async function handleAnalysisResult() {
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

  function handleRestart() {
    if (typeof onReturnHome === "function") {
      onReturnHome();
      return;
    }
    setTrackerPhase("idle");
    setView("interview");
    setInterviewRound((previous) => previous + 1);
  }

  if (view === "results") {
    return (
      <div className="app-shell">
        <ResultsPage onRestart={handleRestart} />
      </div>
    );
  }

  if (promptLoading) {
    return (
      <div className="app-shell">
        <div className="prompt-loading-card">
          <h2>Loading interview question...</h2>
          <p>
            Type: <strong>{formatLabel(promptCategory)}</strong> | Difficulty:{" "}
            <strong>{formatLabel(promptDifficulty)}</strong>
          </p>
        </div>
      </div>
    );
  }

  if (view === "interview" && trackerPhase === "finishing") {
    return <AnalyzingPage />;
  }

  return (
    <div className="app-shell">
      <div className="interview-layout">
        <div className="prompt-banner">
          <div className="prompt-banner__meta-row">
            <span className="prompt-chip">Type: {formatLabel(prompt?.type || promptCategory)}</span>
            <span className="prompt-chip">
              Difficulty: {formatLabel(prompt?.difficulty || promptDifficulty)}
            </span>
          </div>
          <h2 className="prompt-banner__title">Interview Question</h2>
          <p className="prompt-banner__text">{prompt?.text || FALLBACK_PROMPT.text}</p>
          {promptError ? <p className="prompt-banner__warning">{promptError}</p> : null}
        </div>

        <VisionTracker
          key={`${prompt?.id || "prompt"}-${interviewRound}`}
          enabled={true}
          autoStartCamera={true}
          drawLandmarks={true}
          onAnalysisResult={handleAnalysisResult}
          onPhaseChange={setTrackerPhase}
          onEnd={() => setView("results")}
          prompt={prompt || FALLBACK_PROMPT}
        />
      </div>
    </div>
  );
}
