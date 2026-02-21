import json
from pathlib import Path
from typing import Any, Dict, Tuple

def parse_vision_metrics(raw: str) -> Dict[str, Any]:
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
    Persists uploaded audio bytes to backend/uploads and returns absolute path.
    File name is always Interview-Audio.<ext>.
    """
    backend_root = Path(__file__).resolve().parents[2]
    upload_dir = backend_root / "uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)

    suffix = Path(original_filename or "").suffix.lower() or ".webm"
    output_path = upload_dir / f"Interview-Audio{suffix}"
    output_path.write_bytes(raw_bytes)
    return str(output_path)
