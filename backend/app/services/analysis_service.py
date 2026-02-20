import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Tuple
from uuid import uuid4

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
    """
    backend_root = Path(__file__).resolve().parents[2]
    upload_dir = backend_root / "uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)

    safe_name = Path(original_filename or "audio.webm").name
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique = uuid4().hex[:8]
    output_path = upload_dir / f"{timestamp}_{unique}_{safe_name}"
    output_path.write_bytes(raw_bytes)
    return str(output_path)
