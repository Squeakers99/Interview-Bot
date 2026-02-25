import io
import json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from fastapi import APIRouter, UploadFile, File, Form
from fastapi.responses import Response
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable, Image as RLImage
from reportlab.lib.units import inch
from reportlab.lib.utils import ImageReader

from app.services.analysis_service import (
    parse_json_field,
    parse_vision_metrics,
    read_upload_bytes,
    save_json_payload,
    save_upload_bytes,
)
from app.services.results_store import store_latest_results, load_latest_results, load_latest_timelines
router = APIRouter()


def _as_list(value):
    return value if isinstance(value, list) else []

def _as_dict(value):
    return value if isinstance(value, dict) else {}


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
    resolved_prompt_type = prompt_type or summary.get("type", "")
    resolved_prompt_difficulty = prompt_difficulty or summary.get("difficulty", "")
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
            prompt_difficulty=resolved_prompt_difficulty,
            prompt_type=resolved_prompt_type,
            prompt_good_signals=good_signals,
            prompt_red_flags=red_flags,
            )
        
        analysis_payload = _as_dict(interview_analysis)

        combined_results = {
            "prompt_id": prompt_id,
            "prompt_text": prompt_text,
            "prompt_type": resolved_prompt_type,
            "prompt_difficulty": resolved_prompt_difficulty,
            "interview_timelines": timelines,
            "interview_summary": summary,
            "interview_feedback": feedback,
            "good_signals": good_signals,
            "red_flags": red_flags,
            "transcription_analysis": analysis_payload.get("transcript"),
            "vision_summary": analysis_payload.get("vision_summary"),
            "voice_analysis": analysis_payload.get("voice_analysis"),
            "llm_review": analysis_payload.get("llm_review"),
            # Persist the full Converter.py parsed output so downstream jobs can use all fields.
            "interview_analysis": analysis_payload,
            "converter_parsed": {
                "question": analysis_payload.get("question"),
                "type": analysis_payload.get("type") or resolved_prompt_type,
                "difficulty": analysis_payload.get("difficulty") or resolved_prompt_difficulty,
                "clarity_score": analysis_payload.get("clarity_score"),
                "content_score": analysis_payload.get("content_score"),
                "professionalism_score": analysis_payload.get("professionalism_score"),
                "body_language_score": analysis_payload.get("body_language_score"),
                "vocal_delivery_score": analysis_payload.get("vocal_delivery_score"),
                "total_score": analysis_payload.get("total_score"),
                "doing_well": analysis_payload.get("doing_well"),
                "must_improve": analysis_payload.get("must_improve"),
                "habits_to_keep": analysis_payload.get("habits_to_keep"),
                "action_plan": analysis_payload.get("action_plan"),
            },
        }
        # Persist the full combined results payload in backend memory.
        store_latest_results(combined_results)
        print("[/analyze] results stored in memory", flush=True)


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
        "prompt_type": resolved_prompt_type,
        "prompt_difficulty": resolved_prompt_difficulty,
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

def generate_timeline_chart(data: list, title: str, color: str):
    """
    Generate a timeline chart and return a tuple of (ImageReader, buffer).
    The caller is responsible for keeping a reference to the buffer alive
    until after the PDF has been built to avoid premature garbage collection.
    """
    if not data:
        return None, None

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

    buf = io.BytesIO()
    fig.savefig(buf, format="PNG", dpi=150, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return ImageReader(buf), buf


@router.get("/results/interview/pdf")
async def download_interview_pdf():
    try:
        data = load_latest_results()
        if not data:
            return {"error": "No results found. Run an analysis first."}

        print(f"[PDF] data keys: {list(data.keys())}", flush=True)
        timelines = load_latest_timelines()
        eye_timeline = timelines.get("eye_timeline", [])
        posture_timeline = timelines.get("posture_timeline", [])

        print(f"[PDF] eye_timeline points: {len(eye_timeline)}", flush=True)
        print(f"[PDF] posture_timeline points: {len(posture_timeline)}", flush=True)

        pdf_buffer = io.BytesIO()
        doc = SimpleDocTemplate(pdf_buffer, pagesize=letter, topMargin=0.75*inch, bottomMargin=0.75*inch)
        styles = getSampleStyleSheet()
        story = []
        # Keep references to image buffers to prevent premature garbage collection
        image_buffers = []

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

        eye_chart_image, eye_buf = generate_timeline_chart(eye_timeline, "Eye Contact Timeline", "#4f46e5")
        posture_chart_image, posture_buf = generate_timeline_chart(posture_timeline, "Posture Timeline", "#10b981")

        story.append(Paragraph("Timeline Charts", heading_style))
        if eye_chart_image:
            image_buffers.append(eye_buf)
            story.append(RLImage(eye_chart_image, width=6.5*inch, height=2.3*inch))
            story.append(Spacer(1, 8))
        if posture_chart_image:
            image_buffers.append(posture_buf)
            story.append(RLImage(posture_chart_image, width=6.5*inch, height=2.3*inch))
        story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#dddddd")))


        # Transcript
        transcript = data.get("transcription_analysis") or data.get("transcript_analysis", "")
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
        pdf_buffer.seek(0)
        pdf_bytes = pdf_buffer.getvalue()
        print(f"[PDF] PDF built successfully, size: {len(pdf_bytes)} bytes", flush=True)

        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": 'attachment; filename="interview-results.pdf"'},
        )

    except Exception as e:
        print(f"[PDF] ERROR: {e}", flush=True)
        import traceback
        traceback.print_exc()
        return {"error": str(e)}
        
