import json
import random
from pathlib import Path
from typing import Any


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
        "easy": "easy",
        "medium": "medium",
        "hard": "hard",
    }
    return aliases.get(raw, "all")


def list_prompts(prompt_type: str = "all", difficulty: str = "all") -> List[Dict[str, str]]:
    normalized_type = normalize_prompt_type(prompt_type)
    normalized_difficulty = normalize_difficulty(difficulty)

    return [
        prompt
        for prompt in PROMPTS
        if (normalized_type == "all" or prompt["type"] == normalized_type)
        and (
            normalized_difficulty == "all"
            or prompt["difficulty"] == normalized_difficulty
        )
    ]


def get_random_prompt(prompt_type: str = "all", difficulty: str = "all") -> Dict[str, str]:
    filtered = list_prompts(prompt_type=prompt_type, difficulty=difficulty)
    if not filtered:
        raise ValueError("No prompts available for the selected filters.")
    return random.choice(filtered)
