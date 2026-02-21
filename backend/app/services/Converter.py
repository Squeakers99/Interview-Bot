import os
import json
import uuid
import logging
import librosa
import numpy as np
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI
from dotenv import load_dotenv

logger = logging.getLogger("uvicorn.error")

load_dotenv() # Load your Groq or OpenAI API key from .env

def analyze_voice_tone(file_path: str) -> dict:
    try:
        # Load audio file
        y, sr = librosa.load(file_path, sr=None)

        #1 pitch (F0 - fundamental frequency)
        f0, voiced_flag, _ = librosa.pyin(y, fmin=librosa.note_to_hz('C2'), fmax=librosa.note_to_hz('C7'))
        voiced_f0 = f0[voiced_flag]

        avg_pitch = float(np.mean(voiced_f0)) if len(voiced_f0) > 0 else 0.0
        pitch_variability = float(np.std(voiced_f0)) if len(voiced_f0) > 0 else 0.0

        duration = librosa.get_duration(y=y, sr=sr)
        zcr = librosa.feature.zero_crossing_rate(y)
        avg_zcr = float(np.mean(zcr))

        speaking_rate = avg_zcr * sr / 2 

        rms = librosa.feature.rms(y=y)
        avg_energy = float(np.mean(rms))
        energy_variation = float(np.std(rms))

        if avg_pitch < 100:
            pitch_feedback = "Very low pitch - may sound flat or monotone."
        elif avg_pitch < 165:
            pitch_feedback = "Low-normal pitch - can sound calm but may lack energy."
        elif avg_pitch < 255:
            pitch_feedback = "Normal pitch - generally good for professional settings."
        else:
            pitch_feedback = "High pitch - may sound nervous or overly excited."

        #Monotone feedback
        if pitch_variability < 20:
            monotone_feedback = "Monotone delivery - consider varying your pitch more to sound more engaging."
        elif pitch_variability < 50:
            monotone_feedback = "Some pitch variation - good, but adding more could enhance engagement."
        else:
            monotone_feedback = "Good pitch variability - your voice likely sounds dynamic and engaging."

        # speaking rate 
        if speaking_rate < 2.5:
            rate_feedback = "Speaking rate is slow - may come across as hesitant or lacking confidence."
        elif speaking_rate > 5.5:
            rate_feedback = "Speaking rate is fast - slow down so the interviewer can better understand your responses."
        else:
            rate_feedback = "Speaking rate is moderate - easy to follow and understand."

        return {
            "avg_pitch_hz": round(avg_pitch, 2),
            "pitch_variation": round(pitch_variability, 2),
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



app = FastAPI()

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
    vision_metrics: str
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

        --- INTERVIEW DATA ---
        Transcript: {transcript}
        Posture Score: {metrics['postureGoodPct']}%
        Eye Contact Score: {metrics['eyeGoodPct']}%

        --- VOICE TONE DATA ---
        Average Pitch: {voice_analysis.get('avg_pitch_hz')} Hz — {voice_analysis.get('pitch_feedback')}
        Tone Variation: {voice_analysis.get('tone_feedback')}
        Speaking Rate: {voice_analysis.get('speaking_rate')} — {voice_analysis.get('rate_feedback')}

        --- SCORING RUBRIC (100 points total) ---
        Score each category honestly. A 7/10 overall is a GOOD interview. Reserve 9-10 for exceptional candidates.

        1. COMMUNICATION CLARITY (25 pts)
        - Are answers clear, concise, and well-structured?
        - Is vocabulary professional?
        - Are filler words (um, uh, like) avoided?

        2. CONTENT & SUBSTANCE (25 pts)
        - Are answers specific and detailed?
        - Does the candidate use examples or stories?
        - Do they demonstrate knowledge of the field?

        3. PROFESSIONALISM (20 pts)
        - Is the tone confident but not arrogant?
        - Is the introduction strong and polished?
        - Is the language appropriate for a professional setting?

        4. BODY LANGUAGE (15 pts) — use posture ({metrics['postureGoodPct']}%) and eye contact ({metrics['eyeGoodPct']}%) scores
        - Posture above 80% = full marks for posture
        - Eye contact above 80% = full marks for eye contact

        5. VOCAL DELIVERY (15 pts)
        - Pitch: {voice_analysis.get('avg_pitch_hz')} Hz — {voice_analysis.get('pitch_feedback')}
        - Tone variation: {voice_analysis.get('tone_feedback')}
        - Speaking rate: {voice_analysis.get('rate_feedback')}
        - Is the voice confident, varied, and appropriately paced?

        --- RESPONSE FORMAT (follow this exactly) ---

        CATEGORY SCORES:
        - Communication Clarity: X/25
        - Content & Substance: X/25  
        - Professionalism: X/20
        - Body Language: X/15
        - Engagement & Energy: X/15

        TOTAL SCORE: X/100 (X/10)

        WHAT YOU ARE DOING WELL (be specific, reference exact moments from the transcript):
        - [Strength 1]
        - [Strength 2]

        WHAT YOU MUST IMPROVE (be direct and actionable, not vague):
        - [Improvement 1 with specific example from transcript]
        - [Improvement 2 with specific example from transcript]

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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)
    