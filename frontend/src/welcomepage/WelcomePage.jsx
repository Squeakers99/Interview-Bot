import "./WelcomePage.css";
import { useEffect, useRef, useState } from "react";
import App from "../App";
import CountdownPage from "../countdown/CountdownPage";

const CATEGORY_OPTIONS = [
  { value: "all", label: "Any Type" },
  { value: "behaviour", label: "Behavioural" },
  { value: "situation", label: "Situational" },
  { value: "technical", label: "Technical" },
  { value: "general", label: "General" },
];

const DIFFICULTY_OPTIONS = [
  { value: "all", label: "All (Random)" },
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
  const [countdownDone, setCountdownDone] = useState(false);
  const [selectedCategory, setSelectedCategory] = useState("all");
  const [selectedDifficulty, setSelectedDifficulty] = useState("all");
  const [openDropdown, setOpenDropdown] = useState(null);
  const filtersRef = useRef(null);

  function handleReturnToMainPage() {
    setCountdownDone(false);
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

  if (started && !countdownDone) {
    return <CountdownPage start={3} onComplete={() => setCountdownDone(true)} />;
  }

  if (started && countdownDone) {
    return (
      <App
        promptCategory={selectedCategory}
        promptDifficulty={selectedDifficulty}
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
          <p className="welcome-point">
            Click <b>End Interview</b> when you finish speaking.
          </p>
        </div>
      </div>

      <div className="welcome-filters" ref={filtersRef}>
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

      <button className="start-button" onClick={() => setStarted(true)}>
        Start Interview
      </button>
    </div>
  );
}
