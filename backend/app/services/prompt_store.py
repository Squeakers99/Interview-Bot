import json
import random
from pathlib import Path
from typing import Any, Optional


PROMPTS_FILE = Path(__file__).resolve().parents[2] / "prompts.json"
_PROMPTS_CACHE: list[dict[str, Any]] | None = None


def _load_prompts() -> list[dict[str, Any]]:
    global _PROMPTS_CACHE
    if _PROMPTS_CACHE is not None:
        return _PROMPTS_CACHE

    with PROMPTS_FILE.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, list):
        raise ValueError("prompts.json must contain a JSON array.")

    prompts = [item for item in data if isinstance(item, dict)]
    if not prompts:
        raise ValueError("prompts.json does not contain any valid prompt objects.")

    _PROMPTS_CACHE = prompts
    return _PROMPTS_CACHE


def normalize_prompt_type(prompt_type: Optional[str]) -> str:
    raw = (prompt_type or "").strip().lower()
    aliases = {
        "all": "all",
        "any": "all",
        "default": "all",
        "behavior": "behavioral",
        "behaviour": "behavioral",
        "behavioral": "behavioral",
        "situation": "situational",
        "situational": "situational",
        "technical": "technical",
        "tech": "technical",
        "background": "general",
        "general": "general",
        "other": "general",
    }
    return aliases.get(raw, "all")


def normalize_difficulty(difficulty: Optional[str]) -> str:
    raw = (difficulty or "").strip().lower()
    aliases = {
        "all": "all",
        "any": "all",
        "default": "all",
        "1": "easy",
        "2": "easy",
        "easy": "easy",
        "3": "medium",
        "medium": "medium",
        "4": "hard",
        "5": "hard",
        "hard": "hard",
    }
    return aliases.get(raw, "all")


def _difficulty_bucket(value: Any) -> str:
    try:
        score = int(value)
    except (TypeError, ValueError):
        return "all"

    if score <= 2:
        return "easy"
    if score == 3:
        return "medium"
    return "hard"


def list_prompts(prompt_type: str = "all", difficulty: str = "all") -> list[dict[str, Any]]:
    normalized_type = normalize_prompt_type(prompt_type)
    normalized_difficulty = normalize_difficulty(difficulty)
    prompts = _load_prompts()

    return [
        prompt
        for prompt in prompts
        if (normalized_type == "all" or str(prompt.get("type", "")).lower() == normalized_type)
        and (
            normalized_difficulty == "all"
            or _difficulty_bucket(prompt.get("difficulty")) == normalized_difficulty
        )
    ]


def get_random_prompt(prompt_type: str = "all", difficulty: str = "all") -> dict[str, Any]:
    filtered = list_prompts(prompt_type=prompt_type, difficulty=difficulty)
    if not filtered:
        raise ValueError("No prompts available for the selected filters.")
    return random.choice(filtered)
