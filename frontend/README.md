# Frontend (UNL)

This frontend is a React + Vite application for the **Unemployment No Longer** interview coach. It handles the full client-side flow:

- Welcome/setup screen (job ad input + filters)
- Prompt loading
- Countdown and interview timing phases
- Real-time posture + eye tracking with MediaPipe
- Audio capture and upload
- Results visualization and summary display

---

## Features

- **Interview setup UI**
  - Optional job ad title + pasted description.
  - Question type and difficulty selection.
- **Prompt generation path**
  - Fetch random prompt, or generate from job ad via backend.
- **Timed interview phases**
  - Thinking phase: 30 seconds.
  - Response phase: 90 seconds.
- **Vision tracking overlay**
  - Pose + face landmarks (MediaPipe Tasks).
  - Smoothed posture/eye scoring over time.
- **Results page**
  - Session summary cards.
  - Timeline charts.
  - Structured feedback sections.

---

## Tech Stack

- React 19
- Vite
- MediaPipe Tasks Vision (`@mediapipe/tasks-vision`)
- Recharts
- Plain CSS

---

## Environment Variables

Create a `.env` file in `frontend/` if needed:

```bash
VITE_API_BASE_URL=http://127.0.0.1:8000
```

If omitted, the app defaults to `http://127.0.0.1:8000`.

---

## Getting Started

```bash
cd frontend
npm install
npm run dev
```

App runs on: `http://127.0.0.1:5173`

### Other scripts

```bash
npm run build
npm run preview
npm run lint
```

---

## High-Level Flow

1. `main.jsx` lazy-loads `WelcomePage`.
2. `WelcomePage` captures job ad + interview preferences.
3. `App.jsx` requests prompt data from backend.
4. `CountdownPage` starts the interview loop.
5. `VisionTracker`:
   - runs MediaPipe detection,
   - computes posture/eye scores,
   - records microphone audio,
   - uploads interview payload to backend.
6. `AnalyzingPage` displays processing state.
7. `ResultsPage` renders analysis data and timelines.

---

## Backend API expectations

The frontend expects the backend to expose endpoints such as:

- `GET /prompt/random`
- `POST /prompt/from-job-ad`
- `POST /analyze`
- `GET /results/posture_timeline`
- `GET /results/eye_timeline`
- `GET /results/full`
- `GET /results/interview/pdf`

---

## Notes for developers

- Camera and microphone permissions are required.
- MediaPipe model URLs and scoring constants are configured in:
  - `src/config/scoringConfig.jsx`
- Results normalization and chart formatting live under:
  - `src/resultspage/`
