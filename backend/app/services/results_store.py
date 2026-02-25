from __future__ import annotations

from typing import Any, Dict, Optional


# In-memory storage for the most recent analysis session.
_LATEST_RESULTS: Optional[Dict[str, Any]] = None
_LATEST_AUDIO: Optional[Dict[str, Any]] = None
_LATEST_TIMELINES: Optional[Dict[str, Any]] = None


def store_latest_results(payload: Dict[str, Any]) -> None:
    """
    Store the most recent full interview analysis payload in memory.
    """
    global _LATEST_RESULTS
    _LATEST_RESULTS = dict(payload)


def load_latest_results() -> Dict[str, Any]:
    """
    Return the most recent full interview analysis payload, or an empty dict.
    """
    return dict(_LATEST_RESULTS) if isinstance(_LATEST_RESULTS, dict) else {}


def store_latest_audio(metadata: Dict[str, Any]) -> None:
    """
    Store metadata (and optionally raw bytes) for the most recent uploaded audio.
    """
    global _LATEST_AUDIO
    _LATEST_AUDIO = dict(metadata)


def load_latest_audio() -> Optional[Dict[str, Any]]:
    """
    Return metadata for the most recent uploaded audio, or None.
    """
    return dict(_LATEST_AUDIO) if isinstance(_LATEST_AUDIO, dict) else None


def store_latest_timelines(timelines: Dict[str, Any]) -> None:
    """
    Store the most recent interview timelines (posture/eye).
    """
    global _LATEST_TIMELINES
    _LATEST_TIMELINES = dict(timelines)


def load_latest_timelines() -> Dict[str, Any]:
    """
    Return the most recent interview timelines.
    Falls back to timelines nested inside the latest results payload.
    """
    if isinstance(_LATEST_TIMELINES, dict):
        return dict(_LATEST_TIMELINES)

    results = load_latest_results()
    nested = results.get("interview_timelines")
    return dict(nested) if isinstance(nested, dict) else {}

