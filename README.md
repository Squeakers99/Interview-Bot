# Unemployment No Longer (UNL)

UNL is an AI-powered mock interview coach designed to help students and early-career candidates practice interview responses and receive actionable feedback on both **what they say** and **how they present themselves**.

This project combines a React + Vite frontend with a FastAPI backend to deliver:
- Prompt generation from either a built-in prompt bank or pasted job descriptions.
- Real-time posture and eye-contact tracking during interview responses.
- Audio transcription + speaking style analysis.
- LLM-generated interview feedback and scoring.
- A final results dashboard and downloadable report.

> Demo video: https://youtu.be/a-7Rl7wk_L0

---

## Inspiration

UNL began as a response to a common frustration in today’s job market: candidates often never hear back or receive meaningful interview feedback. UNL aims to close that gap by simulating interview conditions and returning practical coaching that users can apply immediately.

---

## What the platform does

1. User enters interview preferences (question type + difficulty) and can optionally paste a job ad.
2. System generates an interview prompt.
3. User gets a **thinking window**, then a **timed response window**.
4. Frontend tracks posture and eye contact while recording audio.
5. Backend analyzes:
   - transcript quality and content,
   - vocal delivery characteristics,
   - posture/eye timeline data.
6. Results are displayed in a structured dashboard with strengths, improvement areas, and a next-step action plan.

---

## Tech Stack

### Frontend
- React 19 + Vite
- MediaPipe Tasks Vision
- Recharts
- CSS

### Backend
- FastAPI + Uvicorn
- Groq/OpenAI-compatible SDK (for LLM + transcription)
- Librosa + NumPy + pydub (audio processing)
- ReportLab + Matplotlib (PDF/report chart generation)

### Tooling
- JavaScript / Python
- Git + GitHub

---

## Project Structure

```text
Interview-Bot/
├── backend/     # FastAPI API, prompt services, analysis pipeline
├── frontend/    # React app, interview flow, MediaPipe tracking, results UI
└── README.md    # Project overview (this file)
```

For folder-specific setup and architecture, see:
- [`frontend/README.md`](frontend/README.md)
- [`backend/README.md`](backend/README.md)

---

## Quick Start (Local)

### 1) Backend
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Backend default: `http://127.0.0.1:8000`

### 2) Frontend
```bash
cd frontend
npm install
npm run dev
```

Frontend default: `http://127.0.0.1:5173`

### 3) Use the app
- Open frontend URL.
- Select interview settings.
- Start interview and answer question.
- Review generated feedback on the results page.

---

## Challenges faced

- Keeping frontend and backend communication stable throughout the interview lifecycle.
- Uploading and processing recorded audio reliably.
- Tuning prompts so model output remained structured and useful.
- Iterating on CSS/UI to keep the experience clean and intuitive.
- Maintaining a consistent JSON response format across services.

---

## Accomplishments

- Built a fully functional end-to-end prototype under tight time constraints.
- Integrated live vision analysis, audio transcription, and AI feedback in one workflow.
- Produced a practical coaching tool that users can repeatedly train with.

---

## What we learned

- Better collaboration workflows with Git/GitHub.
- Practical audio ingestion and analysis for product use-cases.
- How to integrate LLM-driven feedback into a full-stack app.

---

## What’s next

Planned improvements include:
- More polished production UX.
- Accessibility enhancements (such as text-to-speech support).
- Historical tracking of interview sessions and progress over time.
- Stronger deployment/ops readiness for public usage.
