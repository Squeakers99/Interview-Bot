import json
import logging
import os
import re
from typing import Any

from dotenv import load_dotenv
from openai import OpenAI

from app.services.prompt_store import normalize_difficulty, normalize_prompt_type

load_dotenv()
logger = logging.getLogger("uvicorn.error")

GROQ_BASE_URL = os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")


def _groq_client() -> OpenAI:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("Missing GROQ_API_KEY for Groq prompt generation.")
    return OpenAI(api_key=api_key, base_url=GROQ_BASE_URL)


def _extract_json_object(raw_text: str) -> dict[str, Any]:
    text = (raw_text or "").strip()
    if not text:
        raise ValueError("Empty Groq response while generating job-ad prompt.")

    try:
        parsed = json.loads(text)
        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        pass

    fenced_match = re.search(r"```(?:json)?\s*(\{.*\})\s*```", text, flags=re.DOTALL | re.IGNORECASE)
    if fenced_match:
        parsed = json.loads(fenced_match.group(1))
        if isinstance(parsed, dict):
            return parsed

    first = text.find("{")
    last = text.rfind("}")
    if first != -1 and last != -1 and last > first:
        parsed = json.loads(text[first : last + 1])
        if isinstance(parsed, dict):
            return parsed

    preview = text[:500].replace("\n", " ")
    raise ValueError(f"Could not parse JSON object from Groq response. Preview: {preview}")


def _coerce_string_list(value: Any, fallback: list[str]) -> list[str]:
    if not isinstance(value, list):
        return fallback
    cleaned = [str(item).strip() for item in value if str(item).strip()]
    return cleaned[:5] or fallback


def generate_prompt_from_job_ad_with_groq(
    *,
    job_url: str,
    job_title: str,
    job_text: str,
    prompt_type: str = "all",
    difficulty: str = "all",
) -> dict[str, Any]:
    normalized_type = normalize_prompt_type(prompt_type)
    normalized_difficulty = normalize_difficulty(difficulty)

    system_prompt = (
        "You generate one high-quality interview practice question from a job advertisement. "
        "Return strict JSON only, no markdown. Keep the question realistic and role-specific."
    )

    user_prompt = f"""
Generate one interview prompt from this job ad.

Requirements:
- Use the job ad details heavily (responsibilities, skills, seniority).
- If prompt_type is not "all", use it exactly.
- If difficulty is not "all", use it exactly.
- If prompt_type is "all", infer one of: technical, behavioral, situational, general.
- If difficulty is "all", infer one of: easy, medium, hard, expert, master.
- Return ONLY one valid JSON object (no markdown, no comments, no extra text).
- JSON schema:
  {{
    "id": "custom_prompt",
    "type": "technical|behavioral|situational|general",
    "text": "interview question",
    "difficulty": "easy|medium|hard|expert|master",
    "good_signals": ["...", "..."],
    "red_flags": ["...", "..."]
  }}
- `good_signals` and `red_flags` should each contain 2-5 concise strings.

User-selected filters:
- prompt_type: {normalized_type}
- difficulty: {normalized_difficulty}

Job Ad URL:
{job_url}

Job Ad Title:
{job_title}

Job Ad Text (truncated):
{job_text[:10000]}
""".strip()

    client = _groq_client()
    model_candidates: list[str] = []
    if GROQ_MODEL.strip():
        model_candidates.append(GROQ_MODEL.strip())
    for env_name in ("GROQ_MODEL_FALLBACKS",):
        for candidate in [part.strip() for part in os.getenv(env_name, "").split(",") if part.strip()]:
            if candidate not in model_candidates:
                model_candidates.append(candidate)
    for candidate in ("llama-3.3-70b-versatile", "llama-3.1-70b-versatile", "mixtral-8x7b-32768"):
        if candidate not in model_candidates:
            model_candidates.append(candidate)

    content = ""
    chosen_model = ""
    last_error: Exception | None = None
    for model_name in model_candidates:
        try:
            response = client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.4,
                response_format={"type": "json_object"},
            )
            content = response.choices[0].message.content if response.choices else ""
            chosen_model = model_name
            break
        except Exception as exc:
            last_error = exc
            logger.warning("Groq request failed for model '%s': %s", model_name, exc)
            try:
                response = client.chat.completions.create(
                    model=model_name,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    temperature=0.4,
                )
                content = response.choices[0].message.content if response.choices else ""
                chosen_model = model_name
                break
            except Exception as exc2:
                last_error = exc2
                logger.warning("Groq retry without response_format failed for model '%s': %s", model_name, exc2)

    if not chosen_model:
        raise ValueError(f"All Groq model attempts failed. Last error: {last_error}")

    payload = _extract_json_object(content or "")

    result_type = normalize_prompt_type(str(payload.get("type", normalized_type)))
    if normalized_type != "all":
        result_type = normalized_type
    if result_type == "all":
        result_type = "technical"

    result_difficulty = normalize_difficulty(str(payload.get("difficulty", normalized_difficulty)))
    if normalized_difficulty != "all":
        result_difficulty = normalized_difficulty
    if result_difficulty == "all":
        result_difficulty = "medium"

    question_text = str(payload.get("text", "")).strip()
    if not question_text:
        raise ValueError("Groq response did not include prompt text.")
    
    print(
        "Generated prompt from Groq:",
        {
            "model": chosen_model,
            "type": result_type,
            "difficulty": result_difficulty,
            "text": question_text,
            "good_signals": _coerce_string_list(payload.get("good_signals"), []),
            "red_flags": _coerce_string_list(payload.get("red_flags"), []),
            "job_ad_url": job_url,
            "job_ad_title": job_title,
        },
        flush=True,
    )
    
    return {
        "id": f"jobad_groq_{abs(hash((job_url, job_title, question_text))) % 10_000_000}",
        "type": result_type,
        "difficulty": result_difficulty,
        "text": question_text,
        "good_signals": _coerce_string_list(
            payload.get("good_signals"),
            [
                "References responsibilities and requirements from the job ad",
                "Explains tradeoffs and decisions clearly",
            ],
        ),
        "red_flags": _coerce_string_list(
            payload.get("red_flags"),
            [
                "Generic answer not tied to the posted role",
                "No clear rationale or prioritization",
            ],
        ),
        "source": "groq_job_ad",
        "job_ad_url": job_url,
        "job_ad_title": job_title,
        "groq_model": chosen_model,
    }
