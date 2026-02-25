import json
from typing import Any, Dict, Tuple

from app.services.results_store import store_latest_audio, store_latest_timelines

def parse_vision_metrics(raw: str) -> Dict[str, Any]:
    if not raw:
        return {}
    try:
        return json.loads(raw)
    except Exception:
        return {"parse_error": True, "raw": raw}


def parse_json_field(raw: str) -> Dict[str, Any]:
    if not raw:
        return {}
    try:
        return json.loads(raw)
    except Exception:
        return {"parse_error": True, "raw": raw}

async def read_upload_bytes(upload_file) -> Tuple[int, str, str, bytes]:
    """
    Returns (byte_count, filename, content_type, raw_bytes)
    """
    data = await upload_file.read()
    return (len(data), upload_file.filename, upload_file.content_type or "", data)


def save_upload_bytes(raw_bytes: bytes, original_filename: str) -> str:
    """
    Store uploaded audio bytes in backend memory and return a logical handle.
    """
    metadata: Dict[str, Any] = {
        "filename": original_filename or "",
        "byte_count": len(raw_bytes),
        "raw_bytes": raw_bytes,
    }
    store_latest_audio(metadata)
    # Return a logical (non-filesystem) identifier to keep the API shape.
    return "in_memory:Interview-Audio"


def save_json_payload(payload: Dict[str, Any], output_name: str) -> str:
    """
    Store an arbitrary JSON payload in backend memory and return a logical handle.
    """
    # For now we treat "results.json" as the canonical source for interview timelines.
    # Avoid overwriting timeline state for other logical JSON outputs.
    if output_name == "results.json":
        # Store timelines separately so they can be fetched without the full results object.
        store_latest_timelines(payload)

    return f"in_memory:{output_name}"
