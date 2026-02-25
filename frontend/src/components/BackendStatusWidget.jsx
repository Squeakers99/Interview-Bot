import { useEffect, useState } from "react";
import "./BackendStatusWidget.css";

export default function BackendStatusWidget({ apiBase }) {
  const [status, setStatus] = useState("checking");

  useEffect(() => {
    let isMounted = true;

    const checkBackend = async () => {
      try {
        const response = await fetch(`${apiBase}/health`, { cache: "no-store" });
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`);
        }
        const payload = await response.json();
        if (!isMounted) return;
        const backendState =
          String(payload?.status || "").toLowerCase() === "healthy" ? "online" : "degraded";
        setStatus(backendState);
      } catch (error) {
        if (!isMounted) return;
        setStatus("offline");
      }
    };

    checkBackend();
    const intervalId = window.setInterval(checkBackend, 5000);

    return () => {
      isMounted = false;
      window.clearInterval(intervalId);
    };
  }, [apiBase]);

  return (
    <div className={`backend-status-widget backend-status-widget--${status}`} role="status" aria-live="polite">
      <span className="backend-status-widget__dot" aria-hidden="true" />
      <span className="backend-status-widget__label">
        {status === "online" ? "Backend Running" : "Backend Down"}
      </span>
    </div>
  );
}
