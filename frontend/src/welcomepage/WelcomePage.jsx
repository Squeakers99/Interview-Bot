import "./WelcomePage.css";
import { useState } from "react";
import App from "../App";
import CountdownPage from "../countdown/CountdownPage";

export default function WelcomePage() {
    const [started, setStarted] = useState(false);
    const [countdownDone, setCountdownDone] = useState(false);
    const [selectedCategory, setSelectedCategory] = useState("all");
    const [selectedDifficulty, setSelectedDifficulty] = useState("all");

    if (started && !countdownDone) {
        return <CountdownPage start={3} onComplete={() => setCountdownDone(true)} />;
    }

    if (started && countdownDone) {
        return <App promptCategory={selectedCategory} promptDifficulty={selectedDifficulty} />;
    }

    return (
        <div className="welcome-container">
            <div className="body-container">

                <h1 className="welcome-title0">
                    Take a Practice Interview to be Prepared for the Real One with 
                    Unemployment No Longer!
                </h1>
            
                <p className="welcome-title1">
                    You will answer 1 question typically seen in an interview. 
                </p>

                <p className="welcome-title2">
                    We will analyze your posture and eye contact and give you feedback on
                    how you should present yourself in an interview.
                </p>

                <p className="welcome-title3">
                     You will be given 30 seconds to think and 90 seconds to respond to the question. 
                </p>

                <p className="welcome-title4">
                    After you answer the question, click the "End Interview" button. 
                </p>
                
                <p className="welcome-title5">
                    You will be given a score and tips on how to improve your answers and presentation.
                </p>
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
                        <option value="all">All</option>
                        <option value="behaviour">Behaviour</option>
                        <option value="situation">Situation</option>
                        <option value="technical">Technical</option>
                        <option value="general">Other / General</option>
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
                        <option value="all">Default Difficulty Level</option>
                        <option value="easy">Easy</option>
                        <option value="medium">Medium</option>
                        <option value="hard">Hard</option>
                    </select>
                </div>

                <button className="start-button" onClick={() => setStarted(true)}>
                    Start Interview
                </button>
            
        </div>
    );
}
