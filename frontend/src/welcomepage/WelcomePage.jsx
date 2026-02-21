import "./WelcomePage.css";
import { useState } from "react";
import App from "../App";
import CountdownPage from "../countdown/CountdownPage";

export default function WelcomePage() {
    const [started, setStarted] = useState(false);
    const [countdownDone, setCountdownDone] = useState(false);

    if (started && !countdownDone) {
        return <CountdownPage start={3} onComplete={() => setCountdownDone(true)} />;
    }

    if (started && countdownDone) {
        return <App />;
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

                <button className="start-button" onClick={() => setStarted(true)}>
                    Start Interview
                </button>
            
        </div>
    );
}
