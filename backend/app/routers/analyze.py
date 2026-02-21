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


def _as_list(value):
    return value if isinstance(value, list) else []

def _as_dict(value):
    return value if isinstance(value, dict) else {}


def normalize_feedback_payload(raw_feedback):
    if not isinstance(raw_feedback, dict):
        return {"good_signals": [], "red_flags": []}

    good_signals = _as_list(raw_feedback.get("good_signals"))
    if not good_signals:
        good_signals = _as_list(raw_feedback.get("goodSignals"))

    red_flags = _as_list(raw_feedback.get("red_flags"))
    if not red_flags:
        red_flags = _as_list(raw_feedback.get("redFlags"))

    return {
        "good_signals": good_signals,
        "red_flags": red_flags,
    }


@router.post("/analyze")
async def analyze(
    prompt_id: str = Form(""),
    prompt_text: str = Form(""),
    prompt_type: str = Form(""),
    prompt_difficulty: str = Form(""),
    vision_metrics: str = Form("{}"),
    interview_summary: str = Form("{}"),
    interview_timelines: str = Form("{}"),
    interview_feedback: str = Form("{}"),
    audio: UploadFile = File(...)
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
    feedback = normalize_feedback_payload(parse_json_field(interview_feedback))
    good_signals = summary.get("good_signals", [])
    red_flags = summary.get("red_flags", [])
    resolved_prompt_type = prompt_type or summary.get("type", "")
    resolved_prompt_difficulty = prompt_difficulty or summary.get("difficulty", "")
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
    print(f"interview_feedback={feedback}", flush=True)

    interview_analysis = None
    try:
        # Lazy import so missing optional deps (e.g. openai) do not break router startup.
        from app.services.Converter import analyze_interview
        interview_analysis = await analyze_interview(
            audio_bytes, 
            vision_metrics,
            prompt_id=prompt_id,
            prompt_text=prompt_text,
            prompt_difficulty=resolved_prompt_difficulty,
            prompt_type=resolved_prompt_type,
            prompt_good_signals=good_signals,
            prompt_red_flags=red_flags,
            )
        
        analysis_payload = _as_dict(interview_analysis)

        combined_results = {
            "prompt_id": prompt_id,
            "prompt_text": prompt_text,
            "prompt_type": resolved_prompt_type,
            "prompt_difficulty": resolved_prompt_difficulty,
            "interview_timelines": timelines,
            "interview_summary": summary,
            "interview_feedback": feedback,
            "good_signals": good_signals,
            "red_flags": red_flags,
            "transcription_analysis": analysis_payload.get("transcript"),
            "vision_summary": analysis_payload.get("vision_summary"),
            "voice_analysis": analysis_payload.get("voice_analysis"),
            "llm_review": analysis_payload.get("llm_review"),
            # Persist the full Converter.py parsed output so downstream jobs can use all fields.
            "interview_analysis": analysis_payload,
            "converter_parsed": {
                "question": analysis_payload.get("question"),
                "type": analysis_payload.get("type") or resolved_prompt_type,
                "difficulty": analysis_payload.get("difficulty") or resolved_prompt_difficulty,
                "clarity_score": analysis_payload.get("clarity_score"),
                "content_score": analysis_payload.get("content_score"),
                "professionalism_score": analysis_payload.get("professionalism_score"),
                "body_language_score": analysis_payload.get("body_language_score"),
                "vocal_delivery_score": analysis_payload.get("vocal_delivery_score"),
                "total_score": analysis_payload.get("total_score"),
                "doing_well": analysis_payload.get("doing_well"),
                "must_improve": analysis_payload.get("must_improve"),
                "habits_to_keep": analysis_payload.get("habits_to_keep"),
                "action_plan": analysis_payload.get("action_plan"),
            },
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
        "prompt_type": resolved_prompt_type,
        "prompt_difficulty": resolved_prompt_difficulty,
        "audio": {
            "filename": filename,
            "content_type": content_type,
            "bytes": audio_size,
            "saved_to": saved_path,
        },
        "interview_summary": summary,
        "interview_timelines": timelines,
        "interview_feedback": feedback,
        "good_signals": good_signals,
        "red_flags": red_flags,
        "interview_timelines_saved_to": timelines_saved_path,
        "vision_metrics": vision,
        "interview_analysis": interview_analysis,
        "message": "Received audio + metrics. Next step: transcription + scoring.",
    }
