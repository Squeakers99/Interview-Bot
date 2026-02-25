import io
import json
import logging
import os
import subprocess
import shutil

import librosa
import numpy as np
from openai import OpenAI
from dotenv import load_dotenv

logger = logging.getLogger("uvicorn.error")

load_dotenv()  # Load your OpenAI API key from .env


def _resolve_ffmpeg() -> str | None:
    """
    Resolve path to an ffmpeg executable.
    Priority:
    - FFMPEG_PATH env var (full path)
    - PATH lookup
    - `imageio_ffmpeg` bundled binary (pip install imageio-ffmpeg)
    """
    ffmpeg_env = os.getenv("FFMPEG_PATH", "").strip()
    if ffmpeg_env and os.path.isfile(ffmpeg_env):
        return ffmpeg_env

    converter_path = shutil.which("ffmpeg") or shutil.which("avconv")
    if converter_path:
        return converter_path

    try:
        import imageio_ffmpeg  # type: ignore

        candidate = imageio_ffmpeg.get_ffmpeg_exe()
        if candidate and os.path.isfile(candidate):
            return candidate
    except Exception:
        return None

    return None


def _webm_to_wav_bytes_via_ffmpeg(ffmpeg_path: str, webm_bytes: bytes) -> bytes:
    """
    Convert WebM/Opus bytes to WAV bytes using ffmpeg via stdin/stdout pipes.
    Avoids pydub/ffprobe and does not touch the filesystem.
    """
    if not webm_bytes:
        raise ValueError("Empty audio upload (0 bytes).")

    proc = subprocess.run(
        [
            ffmpeg_path,
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            "pipe:0",
            "-ac",
            "1",
            "-ar",
            "16000",
            "-f",
            "wav",
            "pipe:1",
        ],
        input=webm_bytes,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if proc.returncode != 0 or not proc.stdout:
        stderr = (proc.stderr or b"").decode("utf-8", errors="replace")[:800]
        raise RuntimeError(f"ffmpeg conversion failed (code={proc.returncode}). {stderr}")
    return proc.stdout


def analyze_voice_tone_from_bytes(webm_bytes: bytes) -> dict:
    """
    Analyze voice tone directly from in-memory WebM audio bytes.
    No filesystem I/O is performed.
    """
    ffmpeg_path = _resolve_ffmpeg()
    if not ffmpeg_path:
        msg = (
            "ffmpeg not found. Either add ffmpeg to PATH, set FFMPEG_PATH to the full path "
            "to ffmpeg.exe, or install `imageio-ffmpeg` so the backend can use a bundled ffmpeg."
        )
        logger.warning(msg)
        return {"error": "ffmpeg_not_available", "detail": msg}

    try:
        wav_bytes = _webm_to_wav_bytes_via_ffmpeg(ffmpeg_path, webm_bytes)
        wav_buffer = io.BytesIO(wav_bytes)

        # Now load the clean wav from memory
        y, sr = librosa.load(wav_buffer, sr=16000)

        # Remove silence before analysis — silence skews pitch readings
        intervals = librosa.effects.split(y, top_db=30)
        y_voiced = np.concatenate([y[start:end] for start, end in intervals])

        if len(y_voiced) < sr * 0.5:  # Less than 0.5 seconds of speech
            return {"error": "Not enough speech detected"}

        # 1. Pitch Analysis — use y_voiced only (no silence)
        f0, voiced_flag, _ = librosa.pyin(
            y_voiced,
            fmin=librosa.note_to_hz('C2'),
            fmax=librosa.note_to_hz('C7'),
            frame_length=2048,
        )
        voiced_f0 = f0[voiced_flag & ~np.isnan(f0)]

        avg_pitch = float(np.mean(voiced_f0)) if len(voiced_f0) > 0 else 0.0
        pitch_variability = float(np.std(voiced_f0)) if len(voiced_f0) > 0 else 0.0

        # Normalize pitch variability as % of mean for fairer comparison
        pitch_variability_pct = (pitch_variability / avg_pitch * 100) if avg_pitch > 0 else 0

        # 2. Speaking Rate — use onset detection (much more accurate than ZCR)
        onset_frames = librosa.onset.onset_detect(y=y_voiced, sr=sr, units='time')
        duration_voiced = len(y_voiced) / sr
        speaking_rate = len(onset_frames) / duration_voiced if duration_voiced > 0 else 0

        # 3. Energy
        rms = librosa.feature.rms(y=y_voiced)
        avg_energy = float(np.mean(rms))
        energy_variation = float(np.std(rms))

        # 4. Pitch feedback — use gender-neutral ranges
        if avg_pitch < 85:
            pitch_feedback = "Very low pitch — may sound flat or disengaged."
        elif avg_pitch < 180:
            pitch_feedback = "Low-normal pitch — sounds calm and authoritative."
        elif avg_pitch < 300:
            pitch_feedback = "Normal pitch range — good for conversation."
        else:
            pitch_feedback = "High pitch — may sound nervous or anxious."

        # 5. Monotone feedback — use % variability for accuracy
        if pitch_variability_pct < 10:
            monotone_feedback = "Very monotone — your pitch barely changes, which can disengage interviewers. Practice varying your tone when emphasizing key points."
        elif pitch_variability_pct < 25:
            monotone_feedback = "Slightly monotone — some variation present but adding more expressiveness would help keep the interviewer engaged."
        elif pitch_variability_pct < 60:
            monotone_feedback = "Good pitch variation — your voice sounds natural and engaging."
        else:
            monotone_feedback = "High pitch variation — make sure your tone stays controlled and professional."

        # 6. Speaking rate feedback — onsets per second
        if speaking_rate < 2.0:
            rate_feedback = "Speaking too slowly — try to pick up the pace to sound more confident."
        elif speaking_rate > 6.0:
            rate_feedback = "Speaking too fast — slow down so the interviewer can follow you."
        else:
            rate_feedback = "Good speaking rate — easy to follow."

        return {
            "avg_pitch_hz": round(avg_pitch, 2),
            "pitch_variation": round(pitch_variability, 2),
            "pitch_variation_pct": round(pitch_variability_pct, 2),
            "speaking_rate": round(speaking_rate, 2),
            "avg_energy": round(avg_energy, 4),
            "energy_variation": round(energy_variation, 4),
            "pitch_feedback": pitch_feedback,
            "tone_feedback": monotone_feedback,
            "rate_feedback": rate_feedback,
        }
    except Exception as e:
        logger.error(f"Error analyzing voice tone: {e}")
        return {"error": str(e)}

print("DEBUG: Analysis started...", flush=True)


# 2. Setup OpenAI client (Whisper + chat use OpenAI API directly)
_openai_api_key = os.getenv("OPENAI_API_KEY") or os.getenv("OPEN_AI_API_KEY")
llm_client = OpenAI(api_key=_openai_api_key) if _openai_api_key else None
OPENAI_WHISPER_MODEL = "whisper-1"
OPENAI_CHAT_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

async def analyze_interview(
    audio_bytes: bytes, 
    vision_metrics: str,
    prompt_id: str = "",
    prompt_text: str = "",
    prompt_type: str = "",
    prompt_difficulty: str = "",
    prompt_good_signals: str = "",
    prompt_red_flags: str = "",
):
    if not llm_client:
        return {
            "error": "analysis_unavailable",
            "detail": "Missing OPENAI_API_KEY or OPEN_AI_API_KEY.",
        }
    try:
        # A. Transcribe audio via OpenAI Whisper API (no Groq)
        audio_file = io.BytesIO(audio_bytes)
        # Some OpenAI-compatible clients expect a name attribute on the file-like object.
        audio_file.name = "interview.webm"  # type: ignore[attr-defined]

        stt_result = llm_client.audio.transcriptions.create(
            file=audio_file,
            model=OPENAI_WHISPER_MODEL,
            prompt=(
                "Transcribe this interview audio clearly and accurately. "
                "Focus on capturing the candidate's words verbatim, including "
                "filler words and hesitations, as these are important for analysis."
            ),
        )
        transcript = stt_result.text

        # B. Voice analysis from in-memory bytes
        voice_analysis = analyze_voice_tone_from_bytes(audio_bytes)
        print("\n===== VOICE TONE ANALYSIS =====", flush=True)
        print(f"Avg Pitch: {voice_analysis.get('avg_pitch_hz')} Hz — {voice_analysis.get('pitch_feedback')}", flush=True)
        print(f"Tone: {voice_analysis.get('tone_feedback')}", flush=True)
        print(f"Speaking Rate: {voice_analysis.get('speaking_rate')} — {voice_analysis.get('rate_feedback')}", flush=True)
        print("================================\n", flush=True)

        # C. Process Vision Metrics
        metrics = json.loads(vision_metrics)

        # D. The LLM Review (The real magic)
        prompt = f"""
        You are a Senior Tech Recruiter with 15 years of experience evaluating candidates.
        Evaluate this mock interview and provide detailed, realistic feedback.

        --- INTERVIEW QUESTION ---
        Question Asked: {prompt_text if prompt_text else "General interview question"}
        Question Type: {prompt_type if prompt_type else "General"}
        Difficulty Level: {prompt_difficulty if prompt_difficulty else "Unknown"}

        --- WHAT A GOOD ANSWER LOOKS LIKE ---
        {"For a BEHAVIOURAL question: The candidate should use the STAR method (Situation, Task, Action, Result). Penalize vague answers with no real example." if prompt_type.lower() == "behavioural" else ""}
        {"For a SITUATIONAL question: The candidate should walk through their thought process clearly, explain what they would do and why." if prompt_type.lower() == "situational" else ""}
        {"For a TECHNICAL question: The candidate should demonstrate knowledge, use correct terminology, and explain their reasoning step by step." if prompt_type.lower() == "technical" else ""}
        {"For a GENERAL question: The candidate should give a clear, confident, and professional answer." if prompt_type.lower() in ("general", "other", "") else ""}
        {"Hard difficulty requires depth, specifics, and structured responses. Penalize surface-level answers harshly." if prompt_difficulty.lower() in ("hard", "expert") else ""}
        {"Medium difficulty expects some structure and relevant examples." if prompt_difficulty.lower() == "medium" else ""}
        {"Easy difficulty just needs a clear and confident response." if prompt_difficulty.lower() == "easy" else ""}

        --- POSITIVE SIGNALS TO LOOK FOR ---
        These are things the candidate SHOULD say or demonstrate. If you detect any of these in the transcript, highlight them as strengths:
        {prompt_good_signals if prompt_good_signals else "No specific signals provided."}
           
        --- RED FLAGS TO WATCH FOR ---
        These are things the candidate should NEVER say or do for this question. If you detect any of these in the transcript, call them out directly and firmly in the improvements section:
        {prompt_red_flags if prompt_red_flags else "No specific red flags provided."}
        
        --- INTERVIEW DATA ---
        Transcript: {transcript}
        Posture Score: {metrics['postureGoodPct']}%
        Eye Contact Score: {metrics['eyeGoodPct']}%

        --- VOICE TONE DATA ---
        Average Pitch: {voice_analysis.get('avg_pitch_hz')} Hz — {voice_analysis.get('pitch_feedback')}
        Tone Variation: {voice_analysis.get('tone_feedback')}
        Speaking Rate: {voice_analysis.get('speaking_rate')} — {voice_analysis.get('rate_feedback')}

        --- SCORING RUBRIC (100 points total) ---
        Score each category honestly based on the question type and difficulty.
        A 7/10 overall is a GOOD interview. Reserve 9-10 for exceptional candidates.

        1. COMMUNICATION CLARITY (25 pts)
        - Are answers clear, concise, and well-structured?
        - Is vocabulary professional?
        - Are filler words (um, uh, like) avoided?

        2. CONTENT & SUBSTANCE (25 pts)
        - Did the candidate actually answer the question that was asked?
        - Are answers specific and detailed enough for the difficulty level?
        - Does the candidate use examples or STAR method where appropriate?

        3. PROFESSIONALISM (20 pts)
        - Is the tone confident but not arrogant?
        - Is the language appropriate for a professional setting?

        4. BODY LANGUAGE (15 pts)
        - Posture above 80% = full marks for posture
        - Eye contact above 80% = full marks for eye contact

        5. VOCAL DELIVERY (15 pts)
        - Pitch: {voice_analysis.get('avg_pitch_hz')} Hz — {voice_analysis.get('pitch_feedback')}
        - Tone variation: {voice_analysis.get('tone_feedback')}
        - Speaking rate: {voice_analysis.get('rate_feedback')}

        --- RESPONSE FORMAT (follow this exactly) ---

        QUESTION: {prompt_text}
        TYPE: {prompt_type}
        DIFFICULTY: {prompt_difficulty}

        CATEGORY SCORES:
        - Communication Clarity: X/25
        - Content & Substance: X/25
        - Professionalism: X/20
        - Body Language: X/15
        - Vocal Delivery: X/15

        TOTAL SCORE: X/100 (X/10)

        WHAT YOU ARE DOING WELL (be specific, reference exact moments from the transcript):
        - [Strength 1]
        - [Strength 2]

        WHAT YOU MUST IMPROVE (be direct and actionable, reference exact moments from the transcript):
        - [Improvement 1 with specific example]
        - [Improvement 2 with specific example]

        HABITS TO KEEP:
        - [Specific positive behavior to continue]

        ACTION PLAN FOR NEXT INTERVIEW:
        - [1-2 concrete things to practice before next interview]
        """
        
        llm_response = llm_client.chat.completions.create(
            model=OPENAI_CHAT_MODEL,
            messages=[{"role": "user", "content": prompt}]
        )
        review = llm_response.choices[0].message.content
        print("\n===== INTERVIEW ANALYSIS =====", flush=True)
        print(f"TRANSCRIPT: {transcript}", flush=True)
        print(f"\nLLM REVIEW:\n{review}", flush=True)
        print("==============================\n", flush=True)
        
        #------- LLM SEPERATION -------#
        question = prompt_text
        type_ = prompt_type
        difficulty = prompt_difficulty
        
        clarity_score = review.split("Communication Clarity: ")[1].split("/25")[0].strip()
        content_score = review.split("Content & Substance: ")[1].split("/25")[0].strip()
        professionalism_score = review.split("Professionalism: ")[1].split("/20")[0].strip()
        body_language_score = review.split("Body Language: ")[1].split("/15")[0].strip()
        vocal_delivery_score = review.split("Vocal Delivery: ")[1].split("/15")[0].strip()
        total_score = review.split("TOTAL SCORE: ")[1].split("/100")[0].strip()
        
        doing_well = review.split("WHAT YOU ARE DOING WELL")[1].split("WHAT YOU MUST IMPROVE")[0].strip()
        must_improve = review.split("WHAT YOU MUST IMPROVE")[1].split("HABITS TO KEEP")[0].strip()
        habits_to_keep = review.split("HABITS TO KEEP")[1].split("ACTION PLAN FOR NEXT INTERVIEW")[0].strip()
        action_plan = review.split("ACTION PLAN FOR NEXT INTERVIEW")[1].strip()
        
        return {
            "transcript": transcript,
            "vision_summary": metrics,
            "voice_analysis": voice_analysis,
            "llm_review": review,
            "question": question,
            "type": type_,
            "difficulty": difficulty,
            "clarity_score": clarity_score,
            "content_score": content_score,
            "professionalism_score": professionalism_score,
            "body_language_score": body_language_score,
            "vocal_delivery_score": vocal_delivery_score,
            "total_score": total_score,
            "doing_well": doing_well,
            "must_improve": must_improve,
            "habits_to_keep": habits_to_keep,
            "action_plan": action_plan
        }

    except Exception as e:
        logger.error(f"Error during analysis: {e}")
        return {
            "error": "analysis_unavailable",
            "detail": str(e),
        }
