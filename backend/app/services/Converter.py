import os
import json
import uuid
import logging
import librosa
import numpy as np
from pydub import AudioSegment
from fastapi import FastAPI
from openai import OpenAI
from dotenv import load_dotenv

logger = logging.getLogger("uvicorn.error")

load_dotenv() # Load your Groq or OpenAI API key from .env

def analyze_voice_tone(file_path: str) -> dict:
    wav_path = file_path.replace(".webm", ".wav")
    try:
        # Convert .webm to .wav first for much better librosa accuracy
        audio = AudioSegment.from_file(file_path, format="webm")
        audio = audio.set_channels(1).set_frame_rate(16000)  # mono, 16kHz is ideal for voice
        audio.export(wav_path, format="wav")

        # Now load the clean wav
        y, sr = librosa.load(wav_path, sr=16000)

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
    finally:
        if os.path.exists(wav_path):
            os.remove(wav_path)  

print("DEBUG: Analysis started...", flush=True)


# 2. Setup AI Models
# LLM (API via Groq)
llm_client = OpenAI(
    api_key=os.getenv("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1"
)

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

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
    # Unique filename prevents user overlap
    temp_filename = f"{uuid.uuid4()}.webm"
    file_path = os.path.join(UPLOAD_DIR, temp_filename)

    try:
        # A. Save audio bytes
        with open(file_path, "wb") as f:
            f.write(audio_bytes)

        with open(file_path, "rb") as audio_file:
            stt_result = llm_client.audio.transcriptions.create(
                file=audio_file,
                model="whisper-large-v3",
                prompt="Transcribe this interview audio clearly and accurately. Focus on capturing the candidate's words verbatim, including filler words and hesitations, as these are important for analysis."
            )
        transcript = stt_result.text

        voice_analysis = analyze_voice_tone(file_path)
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
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}]
        )
        review = llm_response.choices[0].message.content
        print("\n===== INTERVIEW ANALYSIS =====", flush=True)
        print(f"TRANSCRIPT: {transcript}", flush=True)
        print(f"\nLLM REVIEW:\n{review}", flush=True)
        print("==============================\n", flush=True)


        return {
            "transcript": transcript,
            "vision_summary": metrics,
            "voice_analysis": voice_analysis,
            "llm_review": review,
            
        }

    except Exception as e:
        logger.error(f"Error during analysis: {e}")
        return {"error": str(e)}, 500
    finally:
        # E. Cleanup: Always delete even if code fails
        if os.path.exists(file_path):
            os.remove(file_path)
    