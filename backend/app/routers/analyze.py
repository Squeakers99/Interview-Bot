import json
import os
from fastapi import APIRouter, UploadFile, File, Form

from app.services.analysis_service import (
    parse_json_field,
    parse_vision_metrics,
    read_upload_bytes,
    save_json_payload,
    save_upload_bytes,
)
router = APIRouter()
UPLOAD_DIR = "uploads"

@router.post("/analyze")
async def analyze(
    prompt_id: str = Form(""),
    prompt_text: str = Form(""),
    prompt_type: str = Form(""),
    prompt_difficulty: str = Form(""),
    vision_metrics: str = Form("{}"),
    interview_summary: str = Form("{}"),
    interview_timelines: str = Form("{}"),
    audio: UploadFile = File(...),
):
    """
    MVP endpoint:
    - receives audio + prompt + vision metrics
    - returns confirmation + parsed vision json
    Next step: transcription + scoring.
    """
    vision = parse_vision_metrics(vision_metrics)
    summary = parse_json_field(interview_summary)
    timelines = parse_json_field(interview_timelines)
    audio_size, filename, content_type, audio_bytes = await read_upload_bytes(audio)
    saved_path = save_upload_bytes(audio_bytes, filename)
    timelines_saved_path = save_json_payload(timelines, "results.json")

    # Terminal log for quick debugging during development.
    print("[/analyze] received audio upload", flush=True)
    print(f"filename={filename} content_type={content_type} bytes={audio_size}", flush=True)
    print(f"saved_to={saved_path}", flush=True)
    print(f"timelines_saved_to={timelines_saved_path}", flush=True)
    print(f"audio_preview_hex={audio_bytes[:24].hex()}", flush=True)
    print(f"interview_summary={summary}", flush=True)

    interview_analysis = None
    try:
        # Lazy import so missing optional deps (e.g. openai) do not break router startup.
        from app.services.Converter import analyze_interview
        interview_analysis = await analyze_interview(
            audio_bytes, 
            vision_metrics,
            prompt_id=prompt_id,
            prompt_text=prompt_text,
            prompt_difficulty=summary.get("difficulty", ""),
            prompt_type=summary.get("type", ""),
            )
        
        combined_results = {
            "interview_timelines": timelines,
            "interview_summary": summary,
            "transcription_analysis": interview_analysis.get("transcript"),
            "vision_summary": interview_analysis.get("vision_summary"),
            "voice_analysis": interview_analysis.get("voice_analysis"),
            "llm_review": interview_analysis.get("llm_review"),
        }
        
        results_path = os.path.join(UPLOAD_DIR, "results.json")
        with open(results_path, "w") as f:
            json.dump(combined_results, f, indent=2)
        print(f"[/analyze] results saved to {results_path}", flush=True)


    except Exception as exc:
        print(f"Error during interview analysis: {exc}", flush=True)
        interview_analysis = {
            "error": "analysis_unavailable",
            "detail": str(exc),
        }

    return {
        "ok": True,
        "prompt_id": prompt_id,
        "prompt_text": prompt_text,
        "prompt_type": prompt_type,
        "prompt_difficulty": prompt_difficulty,
        "audio": {
            "filename": filename,
            "content_type": content_type,
            "bytes": audio_size,
            "saved_to": saved_path,
        },
        "interview_summary": summary,
        "interview_timelines": timelines,
        "interview_timelines_saved_to": timelines_saved_path,
        "vision_metrics": vision,
        "interview_analysis": interview_analysis,
        "message": "Received audio + metrics. Next step: transcription + scoring.",
    }
