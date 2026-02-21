import VisionTracker from "./components/VisionTracker";

export default function App() {
  return (
    <main className="app-shell">
      <VisionTracker enabled={true} autoStartCamera={true} drawLandmarks={true} />
    </main>
  );
}
