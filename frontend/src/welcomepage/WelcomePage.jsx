import "./WelcomePage.css";
import { useEffect, useRef, useState } from "react";
import App from "../App";

const CATEGORY_OPTIONS = [
  { value: "all", label: "Any Type" },
  { value: "behaviour", label: "Behavioural" },
  { value: "situation", label: "Situational" },
  { value: "technical", label: "Technical" },
  { value: "general", label: "General" },
];

const DIFFICULTY_OPTIONS = [
  { value: "all", label: "Any Difficulty" },
  { value: "1", label: "Easy" },
  { value: "2", label: "Medium" },
  { value: "3", label: "Hard" },
  { value: "4", label: "Expert" },
  { value: "5", label: "Master" },
];

function CustomDropdown({ id, label, value, options, isOpen, onToggle, onSelect }) {
  const selectedLabel = options.find((option) => option.value === value)?.label || options[0].label;

  return (
    <>
      <label className="welcome-filter-label" htmlFor={id}>
        {label}
      </label>
      <div className="welcome-dropdown">
        <button
          id={id}
          type="button"
          className="welcome-filter-select welcome-filter-select--custom"
          onClick={onToggle}
          aria-haspopup="listbox"
          aria-expanded={isOpen}
        >
          <span>{selectedLabel}</span>
          <span className={`welcome-dropdown-arrow ${isOpen ? "is-open" : ""}`}>▼</span>
        </button>

        {isOpen ? (
          <ul className="welcome-dropdown-menu" role="listbox" aria-labelledby={id}>
            {options.map((option) => (
              <li key={option.value}>
                <button
                  type="button"
                  className={`welcome-dropdown-option ${value === option.value ? "is-selected" : ""}`}
                  onClick={() => onSelect(option.value)}
                >
                  {option.label}
                </button>
              </li>
            ))}
          </ul>
        ) : null}
      </div>
    </>
  );
}

export default function WelcomePage() {
  const [started, setStarted] = useState(false);
  const [selectedCategory, setSelectedCategory] = useState("all");
  const [selectedDifficulty, setSelectedDifficulty] = useState("all");
  const [jobAdTitle, setJobAdTitle] = useState("");
  const [jobAdText, setJobAdText] = useState("");
  const [openDropdown, setOpenDropdown] = useState(null);
  const filtersRef = useRef(null);

  function handleReturnToMainPage() {
    setStarted(false);
  }

  useEffect(() => {
    function handleOutsideClick(event) {
      if (!filtersRef.current?.contains(event.target)) {
        setOpenDropdown(null);
      }
    }

    function handleEscape(event) {
      if (event.key === "Escape") {
        setOpenDropdown(null);
      }
    }

    document.addEventListener("mousedown", handleOutsideClick);
    document.addEventListener("keydown", handleEscape);

    return () => {
      document.removeEventListener("mousedown", handleOutsideClick);
      document.removeEventListener("keydown", handleEscape);
    };
  }, []);

  if (started) {
    return (
      <App
        promptCategory={selectedCategory}
        promptDifficulty={selectedDifficulty}
        jobAdTitle={jobAdTitle}
        jobAdText={jobAdText}
        onReturnHome={handleReturnToMainPage}
      />
    );
  }

  return (
    <div className="welcome-container">
      <div className="welcome-card">
        <h1 className="welcome-title">Practice Interview with Unemployment No Longer</h1>

        <p className="welcome-subtitle">
          Answer one interview question and receive feedback on delivery and presentation.
        </p>

        <div className="welcome-points">
          <p className="welcome-point">30 seconds to think, 90 seconds to respond.</p>
          <p className="welcome-point">We track posture and eye contact during your answer.</p>
          <p className="welcome-point">Input your job ad, select a question type and difficulty, and we will generate a prompt specific to you.</p>
          <p className="welcome-point">
            Click <b>End Interview</b> when you finish speaking and we will process your response.
          </p>
        </div>
      </div>

      <div className="welcome-panels" ref={filtersRef}>
        <div className="welcome-filters welcome-filters--jobad">
          <h3 className="welcome-panel-title">Job Ad Input (optional)</h3>

          <label className="welcome-filter-label" htmlFor="job-ad-title">
            Job Ad Title
          </label>
          <input
            id="job-ad-title"
            type="text"
            className="welcome-filter-select welcome-text-input"
            placeholder="Senior Software Engineer"
            value={jobAdTitle}
            onChange={(event) => setJobAdTitle(event.target.value)}
            autoComplete="off"
          />

          <label className="welcome-filter-label" htmlFor="job-ad-text">
            Paste Job Ad
          </label>
          <textarea
            id="job-ad-text"
            className="welcome-filter-select welcome-text-input welcome-textarea"
            placeholder="Paste the job description here..."
            value={jobAdText}
            onChange={(event) => setJobAdText(event.target.value)}
            rows={5}
          />
        </div>

        <div className="welcome-filters welcome-filters--options">
          <h3 className="welcome-panel-title">Interview Options</h3>

          <CustomDropdown
            id="question-category"
            label="Question Type"
            value={selectedCategory}
            options={CATEGORY_OPTIONS}
            isOpen={openDropdown === "category"}
            onToggle={() => setOpenDropdown((current) => (current === "category" ? null : "category"))}
            onSelect={(value) => {
              setSelectedCategory(value);
              setOpenDropdown(null);
            }}
          />

          <CustomDropdown
            id="question-difficulty"
            label="Difficulty"
            value={selectedDifficulty}
            options={DIFFICULTY_OPTIONS}
            isOpen={openDropdown === "difficulty"}
            onToggle={() => setOpenDropdown((current) => (current === "difficulty" ? null : "difficulty"))}
            onSelect={(value) => {
              setSelectedDifficulty(value);
              setOpenDropdown(null);
            }}
          />
        </div>
      </div>

      <button className="start-button" onClick={() => setStarted(true)}>
        Start Interview
      </button>
    </div>
  );
}
