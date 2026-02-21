import { useEffect, useState } from "react";

export default function preloader() {
  const [dots, setDots] = useState(".");

  useEffect(() => {
    const id = setInterval(() => {
      setDots((prev) => (prev.length >= 3 ? "." : `${prev}.`));
    }, 300);
    return () => clearInterval(id);
  }, []);

  return (
    <div
      style={{
        minHeight: "100vh",
        width: "100vw",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        textAlign: "center",
        background:
          "linear-gradient(to right, #202656, #4e73df, #7790ba, rgb(133, 132, 132), #7790ba, #4e73df, #202656)",
        backgroundSize: "500% 500%",
        animation: "preloaderGradient 20s ease infinite",
        color: "white",
        fontFamily: "'Times New Roman', Times, serif",
      }}
    >
      <style>
        {`@keyframes preloaderGradient {
            0% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
            100% { background-position: 0% 50%; }
          }`}
      </style>

      <h1 style={{ marginBottom: 12, fontSize: "2rem" }}>Loading Interview Bot{dots}</h1>
      <p style={{ fontSize: "1.05rem", opacity: 0.95 }}>Preparing your welcome experience...</p>
    </div>
  );
}
