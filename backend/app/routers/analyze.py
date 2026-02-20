from fastapi import APIRouter, UploadFile, File, Form

from app.services.analysis_service import parse_vision_metrics, read_upload_bytes

router = APIRouter()

@router.post("/analyze")
async def analyze(
    prompt_id: str = Form(""),
    prompt_text: str = Form(""),
    vision_metrics: str = Form("{}"),
    audio: UploadFile = File(...),
):
    """
    MVP endpoint:
    - receives audio + prompt + vision metrics
    - returns confirmation + parsed vision json
    Next step: transcription + scoring.
    """
    vision = parse_vision_metrics(vision_metrics)
    audio_size, filename, content_type = await read_upload_bytes(audio)

    return {
        "ok": True,
        "prompt_id": prompt_id,
        "prompt_text": prompt_text,
        "audio": {
            "filename": filename,
            "content_type": content_type,
            "bytes": audio_size,
        },
        "vision_metrics": vision,
        "message": "Received audio + metrics. Next step: transcription + scoring.",
    }
