import "./WelcomePage.css";
import { useState } from "react";
import App from "../App";
import CountdownPage from "../countdown/CountdownPage";

export default function WelcomePage() {
    const [started, setStarted] = useState(false);
    const [countdownDone, setCountdownDone] = useState(false);
    const [selectedCategory, setSelectedCategory] = useState("all");
    const [selectedDifficulty, setSelectedDifficulty] = useState("1");

    if (started && !countdownDone) {
        return <CountdownPage start={3} onComplete={() => setCountdownDone(true)} />;
    }

    if (started && countdownDone) {
        return <App promptCategory={selectedCategory} promptDifficulty={selectedDifficulty} />;
    }

    return (
        <div className="welcome-container">
            <div className="welcome-card">
                <h1 className="welcome-title">
                    Practice Interview with Unemployment No Longer
                </h1>

                <p className="welcome-subtitle">
                    Answer one interview question and receive feedback on delivery and presentation.
                </p>

                <div className="welcome-points">
                    <p className="welcome-point">30 seconds to think, 90 seconds to respond.</p>
                    <p className="welcome-point">We track posture and eye contact during your answer.</p>
                    <p className="welcome-point">Click <b>End Interview</b> when you finish speaking.</p>
                </div>
            </div>

            <div className="welcome-filters">
                <label className="welcome-filter-label" htmlFor="question-category">
                    Question Type
                </label>
                <select
                    id="question-category"
                    className="welcome-filter-select"
                    value={selectedCategory}
                    onChange={(event) => setSelectedCategory(event.target.value)}
                >
                    <option value="all">Any Type</option>
                    <option value="behaviour">Behavioural</option>
                    <option value="situation">Situational</option>
                    <option value="technical">Technical</option>
                    <option value="general">General</option>
                </select>

                <label className="welcome-filter-label" htmlFor="question-difficulty">
                    Difficulty
                </label>
                <select
                    id="question-difficulty"
                    className="welcome-filter-select"
                    value={selectedDifficulty}
                    onChange={(event) => setSelectedDifficulty(event.target.value)}
                >
                    <option value="1">Easy</option>
                    <option value="2">Medium</option>
                    <option value="3">Hard</option>
                    <option value="4">Expert</option>
                    <option value="5">Master</option>
                </select>
            </div>

            <button className="start-button" onClick={() => setStarted(true)}>
                Start Interview
            </button>

        </div>
    );
}
