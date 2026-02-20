import json
from typing import Any, Dict, Tuple

def parse_vision_metrics(raw: str) -> Dict[str, Any]:
    if not raw:
        return {}
    try:
        return json.loads(raw)
    except Exception:
        return {"parse_error": True, "raw": raw}

async def read_upload_bytes(upload_file) -> Tuple[int, str, str]:
    """
    Returns (byte_count, filename, content_type)
    """
    data = await upload_file.read()
    return (len(data), upload_file.filename, upload_file.content_type or "")
