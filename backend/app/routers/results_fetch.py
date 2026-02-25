from typing import Any, Dict

from fastapi import APIRouter

from app.services.results_store import load_latest_results, load_latest_timelines

router = APIRouter(prefix="/results", tags=["results"])


def load_results_payload() -> Dict[str, Any]:
    """
    Backwards-compatible helper that now reads from in-memory storage
    instead of the filesystem.
    """
    return load_latest_results()


def load_interview_timelines() -> Dict[str, Any]:
    """
    Helper that returns the most recent interview timelines from in-memory storage.
    """
    timelines = load_latest_timelines()
    if not timelines:
        return {"posture_timeline": [], "eye_timeline": []}
    return timelines


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


@router.get("/full")
def get_full_results():
    payload = load_results_payload()
    return {"ok": True, "results": payload}
