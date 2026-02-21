import "./ResultsPage.css";
import { useState } from "react";
import App from "../App";

export default function resultspage() {
    const [started, setStarted] = useState(false);

    if (started) {
        return <App />;
    }

    return (
        <div className="results-container">
            <h1 className="results-title">
                Results of Your Practice Interview
            </h1>
            <p className="results-subtitle">
                Interview prompt:
                <br />
                Your response:
                <br />
                AI response:
            </p>

            <button className="results-button" onClick={() => setStarted(true)}>
                Try-Again
            </button>
        </div>
    );
}
