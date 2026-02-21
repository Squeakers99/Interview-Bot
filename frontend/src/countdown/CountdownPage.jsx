import { useEffect, useState } from "react";
import "./CountdownPage.css";

export default function CountdownPage({ start = 3, onComplete }) {
  const [count, setCount] = useState(start);

  useEffect(() => {
    if (count <= 0) {
      const doneTimer = setTimeout(() => {
        if (typeof onComplete === "function") {
          onComplete();
        }
      }, 350);
      return () => clearTimeout(doneTimer);
    }

    const tickTimer = setTimeout(() => {
      setCount((prev) => prev - 1);
    }, 1000);

    return () => clearTimeout(tickTimer);
  }, [count, onComplete]);

  return (
    <div className="countdown-page">
      <div className="countdown-label">Starting Interview In</div>
      <div className="countdown-number" key={count}>
        {count}
      </div>
    </div>
  );
}
