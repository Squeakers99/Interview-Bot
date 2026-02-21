import "./WelcomePage.css";
import { useState } from "react";
import App from "../App";

export default function WelcomePage() {
    const [started, setStarted] = useState(false);

    if (started) {
        return <App />;
    }

    return (
        <div className="welcome-container">
            <h1 className="welcome-title">
                Take a Practice Interview to be Prepared for the Real One with UNL!
            </h1>

            <p className="welcome-subtitle">
                The purpose of this is to answer 3 questions that are typically seen
                in interviews and get tips on how to improve on your answers. Also it
                will analyze your posture and eye contact to help you improve on
                how you should present yourself in an interview.

            </p>

            <button className="start-button" onClick={() => setStarted(true)}>
                Start Interview
            </button>
        </div>
    );
}
