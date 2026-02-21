from fastapi import APIRouter, UploadFile, File, Form

from app.services.analysis_service import parse_vision_metrics, read_upload_bytes, save_upload_bytes
from app.services.Converter import analyze_interview

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
    audio_size, filename, content_type, audio_bytes = await read_upload_bytes(audio)
    saved_path = save_upload_bytes(audio_bytes, filename)

    # Terminal log for quick debugging during development.
    print("[/analyze] received audio upload", flush=True)
    print(f"filename={filename} content_type={content_type} bytes={audio_size}", flush=True)
    print(f"saved_to={saved_path}", flush=True)
    print(f"audio_preview_hex={audio_bytes[:24].hex()}", flush=True)

    # Call the analyze_interview function from Converter.py
    interview_analysis = await analyze_interview(audio_bytes, vision_metrics)


    return {
        "ok": True,
        "prompt_id": prompt_id,
        "prompt_text": prompt_text,
        "audio": {
            "filename": filename,
            "content_type": content_type,
            "bytes": audio_size,
            "saved_to": saved_path,
        },
        "vision_metrics": vision,
        "message": "Received audio + metrics. Next step: transcription + scoring.",
    }
