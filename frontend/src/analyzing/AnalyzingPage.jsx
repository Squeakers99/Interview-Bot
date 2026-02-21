import "./AnalyzingPage.css";

export default function AnalyzingPage() {
  return (
    <div className="analyzing-page">
      <div className="analyzing-card">
        <div className="analyzing-spinner" aria-hidden="true" />
        <h1 className="analyzing-title">Analyzing Your Results...</h1>
        <p className="analyzing-subtitle">Please wait while we process your interview.</p>
      </div>
    </div>
  );
}
