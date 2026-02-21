import os
import json
import whisper
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
# Whisper (Local)
whisper_model = whisper.load_model("base")
# LLM (API via Groq)
llm_client = OpenAI(
    api_key=os.getenv("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1"
)

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

async def analyze_interview(
    audio_data: UploadFile = File(...), 
    vision_metrics: str = Form(...)
):
    # Unique filename prevents user overlap
    temp_filename = f"{uuid.uuid4()}.webm"
    file_path = os.path.join(UPLOAD_DIR, temp_filename)

    try:
        # A. Save audio bytes
        with open(file_path, "wb") as f:
            f.write(await audio_data.read())

        # B. Transcription
        stt_result = whisper_model.transcribe(file_path)
        transcript = stt_result["text"]
        print(transcript, flush=True)  # Debug: Print transcript to console
        '''
        # C. Process Vision Metrics
        metrics = json.loads(vision_metrics)

        # D. The LLM Review (The real magic)
        prompt = f"""
        Role: Senior Tech Recruiter
        Transcript: {transcript}
        Posture Score: {metrics['postureGoodPct']}%
        Eye Contact Score: {metrics['eyeGoodPct']}%
        
        Provide a concise 3-sentence review and a score out of 10.
        """
        
        llm_response = llm_client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[{"role": "user", "content": prompt}]
        )
        '''
        return {
            "transcript": transcript,
            "vision_summary": metrics,
            "llm_review": llm_response.choices[0].message.content,
            logger.info(f"LLM Review Result: {llm_response.choices[0].message.content}"):
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
    