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
            )
        transcript = stt_result.text
        print(transcript, flush=True)  # Debug: Print transcript to console

        # C. Process Vision Metrics
        metrics = json.loads(vision_metrics)

        # D. The LLM Review (The real magic)
        prompt = f"""
        You are a Senior Tech Recruiter evaluating a mock interview.

        Transcript: {transcript}
        Posture Score: {metrics['postureGoodPct']}%
        Eye Contact Score: {metrics['eyeGoodPct']}%

        Please evaluate the candidate and return your response in this exact format:

        SCORE: X/10
        STRENGTHS: (1-2 sentences)
        IMPROVEMENTS: (1-2 sentences)
        OVERALL: (1 sentence summary)
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
    