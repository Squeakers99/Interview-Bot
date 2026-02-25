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

OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")


def _openai_client() -> OpenAI:
    api_key = os.getenv("OPENAI_API_KEY") or os.getenv("OPEN_AI_API_KEY")
    if not api_key:
        raise ValueError("Missing OPENAI_API_KEY or OPEN_AI_API_KEY for prompt generation.")
    return OpenAI(api_key=api_key)


def _extract_json_object(raw_text: str) -> dict[str, Any]:
    text = (raw_text or "").strip()
    if not text:
        raise ValueError("Empty OpenAI response while generating job-ad prompt.")

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


def generate_prompt_from_job_ad_with_openai(
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
- Note the difficulty scale is easy < medium < hard < expert < master. Master difficulty is peak difficulty, and should be treated as such.
- Always return a question, even if the job ad is sparse. Do not say "I can't generate a question". Use your best judgment to create a relevant question.

User-selected filters:
- prompt_type: {normalized_type}
- difficulty: {normalized_difficulty}

Job Ad Title:
{job_title}

Job Ad Text (truncated):
{job_text[:10000]}
""".strip()

    client = _openai_client()
    model_candidates: list[str] = []
    if OPENAI_MODEL.strip():
        model_candidates.append(OPENAI_MODEL.strip())
    for env_name in ("OPENAI_MODEL_FALLBACKS",):
        for candidate in [part.strip() for part in os.getenv(env_name, "").split(",") if part.strip()]:
            if candidate not in model_candidates:
                model_candidates.append(candidate)
    for candidate in ("gpt-4o-mini", "gpt-4o", "gpt-4-turbo"):
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
            logger.warning("OpenAI request failed for model '%s': %s", model_name, exc)
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
                logger.warning("OpenAI retry without response_format failed for model '%s': %s", model_name, exc2)

    if not chosen_model:
        raise ValueError(f"All OpenAI model attempts failed. Last error: {last_error}")

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
        raise ValueError("OpenAI response did not include prompt text.")
    
    print(
        "Generated prompt from OpenAI:",
        {
            "model": chosen_model,
            "type": result_type,
            "difficulty": result_difficulty,
            "text": question_text,
            "good_signals": _coerce_string_list(payload.get("good_signals"), []),
            "red_flags": _coerce_string_list(payload.get("red_flags"), []),
            "job_ad_title": job_title,
        },
        flush=True,
    )
    
    return {
        "id": f"jobad_openai_{abs(hash((job_url, job_title, question_text))) % 10_000_000}",
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
        "source": "openai_job_ad",
        "job_ad_url": job_url,
        "job_ad_title": job_title,
        "openai_model": chosen_model,
    }
