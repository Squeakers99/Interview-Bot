import os
import json
import tempfile
import matplotlib
import httpx
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from fastapi import APIRouter, UploadFile, File, Form, BackgroundTasks
from fastapi.responses import FileResponse
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable, Image as RLImage
from reportlab.lib.units import inch


from app.services.analysis_service import (
    parse_json_field,
    parse_vision_metrics,
    read_upload_bytes,
    save_json_payload,
    save_upload_bytes,
)
router = APIRouter()
UPLOAD_DIR = "uploads"


def _as_list(value):
    return value if isinstance(value, list) else []


def normalize_feedback_payload(raw_feedback):
    if not isinstance(raw_feedback, dict):
        return {"good_signals": [], "red_flags": []}

    good_signals = _as_list(raw_feedback.get("good_signals"))
    if not good_signals:
        good_signals = _as_list(raw_feedback.get("goodSignals"))

    red_flags = _as_list(raw_feedback.get("red_flags"))
    if not red_flags:
        red_flags = _as_list(raw_feedback.get("redFlags"))

    return {
        "good_signals": good_signals,
        "red_flags": red_flags,
    }


@router.post("/analyze")
async def analyze(
    prompt_id: str = Form(""),
    prompt_text: str = Form(""),
    prompt_type: str = Form(""),
    prompt_difficulty: str = Form(""),
    vision_metrics: str = Form("{}"),
    interview_summary: str = Form("{}"),
    interview_timelines: str = Form("{}"),
    interview_feedback: str = Form("{}"),
    audio: UploadFile = File(...)
):
    """
    MVP endpoint:
    - receives audio + prompt + vision metrics
    - returns confirmation + parsed vision json
    Next step: transcription + scoring.
    """
    vision = parse_vision_metrics(vision_metrics)
    summary = parse_json_field(interview_summary)
    timelines = parse_json_field(interview_timelines)
    feedback = normalize_feedback_payload(parse_json_field(interview_feedback))
    good_signals = summary.get("good_signals", [])
    red_flags = summary.get("red_flags", [])
    audio_size, filename, content_type, audio_bytes = await read_upload_bytes(audio)
    saved_path = save_upload_bytes(audio_bytes, filename)
    timelines_saved_path = save_json_payload(timelines, "results.json")

    # Terminal log for quick debugging during development.
    print("[/analyze] received audio upload", flush=True)
    print(f"filename={filename} content_type={content_type} bytes={audio_size}", flush=True)
    print(f"saved_to={saved_path}", flush=True)
    print(f"timelines_saved_to={timelines_saved_path}", flush=True)
    print(f"audio_preview_hex={audio_bytes[:24].hex()}", flush=True)
    print(f"interview_summary={summary}", flush=True)
    print(f"interview_feedback={feedback}", flush=True)

    interview_analysis = None
    try:
        # Lazy import so missing optional deps (e.g. openai) do not break router startup.
        from app.services.Converter import analyze_interview
        interview_analysis = await analyze_interview(
            audio_bytes, 
            vision_metrics,
            prompt_id=prompt_id,
            prompt_text=prompt_text,
            prompt_difficulty=summary.get("difficulty", ""),
            prompt_type=summary.get("type", ""),
            prompt_good_signals=good_signals,
            prompt_red_flags=red_flags,
            )
        
        combined_results = {
            "interview_timelines": timelines,
            "interview_summary": summary,
            "interview_feedback": feedback,
            "good_signals": good_signals,
            "red_flags": red_flags,
            "transcription_analysis": interview_analysis.get("transcript"),
            "vision_summary": interview_analysis.get("vision_summary"),
            "voice_analysis": interview_analysis.get("voice_analysis"),
            "llm_review": interview_analysis.get("llm_review"),
        }
        
        results_path = os.path.join(UPLOAD_DIR, "results.json")
        with open(results_path, "w") as f:
            json.dump(combined_results, f, indent=2)
        print(f"[/analyze] results saved to {results_path}", flush=True)


    except Exception as exc:
        print(f"Error during interview analysis: {exc}", flush=True)
        interview_analysis = {
            "error": "analysis_unavailable",
            "detail": str(exc),
        }

    return {
        "ok": True,
        "prompt_id": prompt_id,
        "prompt_text": prompt_text,
        "prompt_type": prompt_type,
        "prompt_difficulty": prompt_difficulty,
        "audio": {
            "filename": filename,
            "content_type": content_type,
            "bytes": audio_size,
            "saved_to": saved_path,
        },
        "interview_summary": summary,
        "interview_timelines": timelines,
        "interview_feedback": feedback,
        "good_signals": good_signals,
        "red_flags": red_flags,
        "interview_timelines_saved_to": timelines_saved_path,
        "vision_metrics": vision,
        "interview_analysis": interview_analysis,
        "message": "Received audio + metrics. Next step: transcription + scoring.",
    }

def generate_timeline_chart(data: list, title: str, color: str) -> str:
    if not data:
        return None

    times = []
    scores = []
    for i, point in enumerate(data):
        if isinstance(point, dict):
            times.append(point.get("timeSec", i))
            scores.append(point.get("score", 0))
        elif isinstance(point, (list, tuple)) and len(point) >= 2:
            times.append(point[0])  # index 0 = timeSec
            scores.append(point[1])  # index 1 = score
        else:
            times.append(i)
            scores.append(0)

    fig, ax = plt.subplots(figsize=(7, 2.5))
    ax.plot(times, scores, color=color, linewidth=1.5)
    ax.fill_between(times, scores, alpha=0.15, color=color)
    ax.set_title(title, fontsize=11, fontweight="bold", pad=8)
    ax.set_xlabel("Time (s)", fontsize=9)
    ax.set_ylabel("Score (%)", fontsize=9)
    ax.set_ylim(0, 105)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
    fig.savefig(tmp.name, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return tmp.name


@router.get("/results/interview/pdf")
async def download_interview_pdf(background_tasks: BackgroundTasks):
    try:
        results_path = os.path.join(UPLOAD_DIR, "results.json")
        if not os.path.exists(results_path):
            return {"error": "No results found. Run an analysis first."}

        with open(results_path, "r") as f:
            data = json.load(f)
        
        print(f"[PDF] data keys: {list(data.keys())}", flush=True)

        async with httpx.AsyncClient() as client:
            eye_res = await client.get("http://127.0.0.1:8000/results/eye_timeline")
            posture_res = await client.get("http://127.0.0.1:8000/results/posture_timeline")
            eye_json = eye_res.json()
            posture_json = posture_res.json()

        eye_timeline = eye_json if isinstance(eye_json, list) else eye_json.get("eye_timeline", [])
        posture_timeline = posture_json if isinstance(posture_json, list) else posture_json.get("posture_timeline", [])

        print(f"[PDF] eye_timeline points: {len(eye_timeline)}", flush=True)
        print(f"[PDF] posture_timeline points: {len(posture_timeline)}", flush=True)


        # Create a temp PDF file
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
        pdf_path = tmp.name
        tmp.close()

        doc = SimpleDocTemplate(pdf_path, pagesize=letter, topMargin=0.75*inch, bottomMargin=0.75*inch)
        styles = getSampleStyleSheet()
        story = []

        # Custom styles
        title_style = ParagraphStyle("Title", parent=styles["Title"], fontSize=24, textColor=colors.HexColor("#1a1a2e"), spaceAfter=6)
        heading_style = ParagraphStyle("Heading", parent=styles["Heading2"], fontSize=13, textColor=colors.HexColor("#16213e"), spaceBefore=14, spaceAfter=4)
        body_style = ParagraphStyle("Body", parent=styles["Normal"], fontSize=10, leading=16, textColor=colors.HexColor("#333333"))
        label_style = ParagraphStyle("Label", parent=styles["Normal"], fontSize=10, textColor=colors.HexColor("#666666"), spaceAfter=2)
        value_style = ParagraphStyle("Value", parent=styles["Normal"], fontSize=11, textColor=colors.HexColor("#1a1a2e"), spaceBefore=0, spaceAfter=8)
        bold_style = ParagraphStyle("Bold", parent=styles["Normal"], fontSize=10, fontName="Helvetica-Bold", textColor=colors.HexColor("#16213e"), spaceBefore=8, spaceAfter=4)
        # Header
        story.append(Paragraph("Interview Results Report", title_style))
        story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#4f46e5")))
        story.append(Spacer(1, 12))

        # Vision Scores
        vision = data.get("vision_summary", {})
        if vision:
            story.append(Paragraph("Body Language Scores", heading_style))
            story.append(Paragraph("Posture Score", label_style))
            story.append(Paragraph(f"{vision.get('postureGoodPct', 'N/A')}%", value_style))
            story.append(Paragraph("Eye Contact Score", label_style))
            story.append(Paragraph(f"{vision.get('eyeGoodPct', 'N/A')}%", value_style))
            story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#dddddd")))

        # Voice Analysis
        voice = data.get("voice_analysis", {})
        if voice and "error" not in voice:
            story.append(Paragraph("Voice Analysis", heading_style))
            story.append(Paragraph("Pitch", label_style))
            story.append(Paragraph(f"{voice.get('avg_pitch_hz', 'N/A')} Hz — {voice.get('pitch_feedback', '')}", value_style))
            story.append(Paragraph("Tone", label_style))
            story.append(Paragraph(voice.get("tone_feedback", "N/A"), value_style))
            story.append(Paragraph("Speaking Rate", label_style))
            story.append(Paragraph(f"{voice.get('speaking_rate', 'N/A')} — {voice.get('rate_feedback', '')}", value_style))
            story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#dddddd")))

        eye_chart_path = generate_timeline_chart(eye_timeline, "Eye Contact Timeline", "#4f46e5")
        posture_chart_path = generate_timeline_chart(posture_timeline, "Posture Timeline", "#10b981")

        story.append(Paragraph("Timeline Charts", heading_style))
        if eye_chart_path:
            story.append(RLImage(eye_chart_path, width=6.5*inch, height=2.3*inch))
            story.append(Spacer(1, 8))
        if posture_chart_path:
            story.append(RLImage(posture_chart_path, width=6.5*inch, height=2.3*inch))
        story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#dddddd")))


        # Transcript
        transcript = data.get("transcript_analysis", "")
        if transcript:
            story.append(Paragraph("Transcript", heading_style))
            story.append(Paragraph(transcript, body_style))
            story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#dddddd")))

        # LLM Review
        review = data.get("llm_review", "")
        if review:
            story.append(Paragraph("AI Recruiter Feedback", heading_style))
            for line in review.split("\n"):
                line = line.strip()
                if not line:
                    story.append(Spacer(1, 4))
                elif line.isupper() or line.endswith(":"):
                    story.append(Paragraph(line, ParagraphStyle("Bold", parent=styles["Normal"], fontSize=10, fontName="Helvetica-Bold", spaceBefore=8, textColor=colors.HexColor("#16213e"))))
                else:
                    story.append(Paragraph(line, body_style))

        doc.build(story)
        print(f"[PDF] PDF built successfully, size: {os.path.getsize(pdf_path)} bytes", flush=True)

        def cleanup():
            if os.path.exists(pdf_path):
                os.remove(pdf_path)

        background_tasks.add_task(cleanup)

        return FileResponse(
            pdf_path,
            media_type="application/pdf",
            filename="interview-results.pdf",
        )

    except Exception as e:
        print(f"[PDF] ERROR: {e}", flush=True)
        import traceback
        traceback.print_exc()
        return {"error": str(e)}
        
