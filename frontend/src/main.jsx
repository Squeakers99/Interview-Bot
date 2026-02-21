import { StrictMode, Suspense, lazy } from "react";
import { createRoot } from "react-dom/client";
import "./index.css";
import Preloader from "./preloader/preloader";

const WelcomePage = lazy(() => import("./welcomepage/WelcomePage"));

createRoot(document.getElementById("root")).render(
  <StrictMode>
    <Suspense fallback={<Preloader />}>
      <WelcomePage />
    </Suspense>
  </StrictMode>
);
