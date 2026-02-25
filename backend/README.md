# Backend (UNL)

This backend is a FastAPI service for the **Unemployment No Longer** interview coach. It powers:

- Prompt retrieval and filtering.
- Prompt generation from pasted/linked job ads.
- Interview payload ingestion (audio + vision metrics + metadata).
- Transcription and AI feedback generation.
- Results retrieval APIs for frontend rendering.
- PDF report generation.

---

## Stack

- FastAPI
- Uvicorn
- OpenAI-compatible client pointed at Groq endpoint
- Librosa, NumPy, pydub (voice analysis)
- ReportLab, Matplotlib (report output)
- httpx (web/content fetch)

---

## Directory layout

```text
backend/
├── app/
│   ├── main.py                # FastAPI app + router registration
│   ├── routers/
│   │   ├── health.py
│   │   ├── prompts.py
│   │   ├── analyze.py
│   │   └── results_fetch.py
│   └── services/
│       ├── prompt_store.py
│       ├── job_ad_prompt_service.py
│       ├── analysis_service.py
│       └── Converter.py
├── prompts/                   # Prompt dataset used by prompt store
└── requirements.txt
```

---

## Environment variables

Create `backend/.env` with your OpenAI API key:

```bash
OPENAI_API_KEY=your_key_here
```

You can also use `OPEN_AI_API_KEY`. The backend uses OpenAI for Whisper transcription and for chat (interview analysis and job-ad prompt generation). Optional: `OPENAI_MODEL` (default `gpt-4o-mini`) for the chat model.

For **voice tone analysis** (pitch, speaking rate), ffmpeg must be available. If it’s installed but not on PATH (e.g. on Windows), set `FFMPEG_PATH` (and optionally `FFPROBE_PATH`) in `.env` to the full path to the executable(s), e.g. `FFMPEG_PATH=C:\ffmpeg\bin\ffmpeg.exe`.

---

## Setup

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

API base URL: `http://127.0.0.1:8000`
Swagger docs: `http://127.0.0.1:8000/docs`

---

## Core endpoints

### Health
- `GET /`
- `GET /health`

### Prompts
- `GET /prompt/all?type=...&difficulty=...`
- `GET /prompt/random?type=...&difficulty=...`
- `POST /prompt/from-job-ad`

### Analysis
- `POST /analyze`
  - multipart form payload including audio and interview metadata.

### Results
- `GET /results/timelines`
- `GET /results/posture_timeline`
- `GET /results/eye_timeline`
- `GET /results/llm_review`
- `GET /results/full`
- `GET /results/interview/pdf`

---

## Data flow summary

1. Frontend submits interview payload to `/analyze`.
2. Backend stores uploaded audio + timelines.
3. `Converter.py` performs:
   - transcription,
   - voice tone/speaking analysis,
   - LLM interview review and scoring.
4. Combined output is saved to `uploads/results.json`.
5. Frontend fetches result/timeline endpoints and renders final dashboard.
6. Optional PDF report is generated from stored results.

---

## Notes

- If scraping a job ad URL is blocked by anti-bot protection, prompt generation can fall back to a Playwright-based fetch path.
- `uploads/results.json` is the shared artifact used by `/results/*` routes.
- Ensure `ffmpeg` is available in your environment for robust audio conversion paths used by `pydub`.
