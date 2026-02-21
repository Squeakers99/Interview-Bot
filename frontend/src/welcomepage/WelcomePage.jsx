import "./WelcomePage.css";
import { useState,useEffect } from "react";
import App from "../App";

export default function WelcomePage() {
    const [started, setStarted] = useState(false);
    const [step, setStep] = useState(0);

    useEffect(() => {
        const timer1 = setTimeout(() => setStep(1), 5000);
        const timer2 = setTimeout(() => setStep(2), 11000);
        const timer3 = setTimeout(() => setStep(3), 17000);
        const timer4 = setTimeout(() => setStep(4), 23000);
        const timer5 = setTimeout(() => setStep(5), 30000);


        return () => {
            clearTimeout(timer1);
            clearTimeout(timer2);
            clearTimeout(timer3);
            clearTimeout(timer4);
            clearTimeout(timer5);
        };
    }, []);

    if (started) {
        return <App />;
    }

    return (
        <div className="welcome-container">
            
            {step === 0 && (
                <h1 className="welcome-title">
                    Take a Practice Interview to be Prepared for the Real One with 
                    Unemployment No Longer!
                </h1>
            )}
            
            {step === 1 && (
                <p className="welcome-title">
                    You will answer 1 question typically seen in an interviews. 
                </p>
            )}

            {step === 2 && (
            <p className="welcome-title">
                We will analyze your posture and eye contact and give you feedback on
                how you should present yourself in an interview.
            </p>
        )}

            {step === 3 && (
                <p className="welcome-title">
                    You will be given 30 seconds to think and 90 seconds to respond to the question. 
                </p>
            )}

            {step === 4 && (
            <p className="welcome-title">
                After you answer the question, click the "End Interview" button. 
            </p>
        )}
            
            {step === 5 && (
            <p className="welcome-title">
                You will be given a score and tips on how to improve your answers and presentation.
            </p>
            )}

            <button className="start-button" onClick={() => setStarted(true)}>
                Start Interview
            </button>

        </div>
    );
}
