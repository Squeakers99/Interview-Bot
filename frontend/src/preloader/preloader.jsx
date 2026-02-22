import Logo from "../assets/Logo.png";

export default function preloader() {
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
          }
          @keyframes preloaderPulse {
            0% { transform: scale(0.92); }
            50% { transform: scale(1.06); }
            100% { transform: scale(0.92); }
          }`}
      </style>

      <img
        src={Logo}
        alt="Interview Bot logo"
        style={{
          width: "min(220px, 42vw)",
          height: "auto",
          marginBottom: 14,
          animation: "preloaderPulse 0.9s ease-in-out infinite",
          filter: "drop-shadow(0 12px 24px rgba(0,0,0,0.28))",
        }}
      />
    </div>
  );
}
