import os
import json
import uuid
import logging
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI
from dotenv import load_dotenv

print("DEBUG: Analysis started...", flush=True)

logger = logging.getLogger("uvicorn.error")

load_dotenv() # Load your Groq or OpenAI API key from .env

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
                promtpt="Transcribe this interview audio clearly and accurately. Focus on capturing the candidate's words verbatim, including filler words and hesitations, as these are important for analysis."
            )
        transcript = stt_result.text
        print(transcript, flush=True)  # Debug: Print transcript to console

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

        5. ENGAGEMENT & ENERGY (15 pts)
        - Does the candidate seem enthusiastic and engaged?
        - Do they ask thoughtful questions?
        - Is there a natural conversational flow?

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
    