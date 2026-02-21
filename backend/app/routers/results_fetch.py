import json
from pathlib import Path
from typing import Any, Dict

from fastapi import APIRouter

router = APIRouter(prefix="/results", tags=["results"])

def load_results_payload() -> Dict[str, Any]:
    results_path = Path(__file__).resolve().parents[2] / "uploads" / "results.json"
    if not results_path.exists():
        return {}
    try:
        payload = json.loads(results_path.read_text(encoding="utf-8"))
        return payload if isinstance(payload, dict) else {}
    except Exception:
        return {}

def load_interview_timelines() -> Dict[str, Any]:
    payload = load_results_payload()
    if not payload:
        return {"posture_timeline": [], "eye_timeline": []}

    # New shape in results.json:
    # { "interview_timelines": { "posture_timeline": [...], "eye_timeline": [...] }, ... }
    nested = payload.get("interview_timelines")
    if isinstance(nested, dict):
        return nested

    # Backward compatibility for older files where timelines were top-level.
    return payload


def to_pairs(timeline: Any):
    if not isinstance(timeline, list):
        return []
    pairs = []
    for item in timeline:
        if isinstance(item, dict):
            pairs.append([item.get("timestamp"), item.get("percentage")])
    return pairs


@router.get("/timelines")
def get_timelines():
    interview_timelines = load_interview_timelines()
    posture_pairs = to_pairs(interview_timelines.get("posture_timeline", []))
    eye_pairs = to_pairs(interview_timelines.get("eye_timeline", []))
    return {
        "ok": True,
        "interview_timelines": {
            "posture_timeline": posture_pairs,
            "eye_timeline": eye_pairs,
        },
    }

@router.get("/posture_timeline")
def get_posture_timeline():
    interview_timelines = load_interview_timelines()
    posture_timeline = to_pairs(interview_timelines.get("posture_timeline", []))
    return {"ok": True, "posture_timeline": posture_timeline}

@router.get("/eye_timeline")
def get_eye_timeline():
    interview_timelines = load_interview_timelines()
    eye_timeline = to_pairs(interview_timelines.get("eye_timeline", []))
    return {"ok": True, "eye_timeline": eye_timeline}


@router.get("/llm_review")
def get_llm_review():
    payload = load_results_payload()
    return {"ok": True, "llm_review": payload.get("llm_review")}
