import json
from pathlib import Path
from typing import Any, Dict

from fastapi import APIRouter

router = APIRouter(prefix="/results", tags=["results"])

def load_interview_timelines() -> Dict[str, Any]:
    timelines_path = Path(__file__).resolve().parents[2] / "uploads" / "Interview-Timelines.json"
    if not timelines_path.exists():
        return {"posture_timeline": [], "eye_timeline": []}
    try:
        interview_timelines = json.loads(timelines_path.read_text(encoding="utf-8"))
        return interview_timelines
    except Exception:
        return {"posture_timeline": [], "eye_timeline": [], "parse_error": True}


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