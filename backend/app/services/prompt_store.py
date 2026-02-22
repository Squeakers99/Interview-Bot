import json
import random
from pathlib import Path
from typing import Any, Optional


PROMPTS_DIR = Path(__file__).resolve().parents[2] / "prompts"
_PROMPTS_CACHE: list[dict[str, Any]] | None = None


def _coerce_prompt_list(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]

    if isinstance(payload, dict):
        nested = payload.get("prompts")
        if isinstance(nested, list):
            return [item for item in nested if isinstance(item, dict)]
        return [payload]

    return []


def _read_prompt_file(path: Path) -> list[dict[str, Any]]:
    raw = path.read_text(encoding="utf-8").strip()
    if not raw:
        return []

    payload = json.loads(raw)
    prompts = _coerce_prompt_list(payload)

    file_type = normalize_prompt_type(path.stem)
    normalized: list[dict[str, Any]] = []
    for index, prompt in enumerate(prompts, start=1):
        row = dict(prompt)
        row_type = normalize_prompt_type(str(row.get("type", "")))
        row["type"] = row_type if row_type != "all" else file_type
        row.setdefault("id", f"{path.stem}_{index:03d}")
        normalized.append(row)

    return normalized


def _load_prompts() -> list[dict[str, Any]]:
    global _PROMPTS_CACHE
    if _PROMPTS_CACHE is not None:
        return _PROMPTS_CACHE

    if not PROMPTS_DIR.exists():
        raise ValueError(f"Prompts directory not found: {PROMPTS_DIR}")

    prompt_files = sorted(PROMPTS_DIR.glob("*.json"))
    if not prompt_files:
        raise ValueError(f"No prompt JSON files found in: {PROMPTS_DIR}")

    prompts: list[dict[str, Any]] = []
    for path in prompt_files:
        try:
            prompts.extend(_read_prompt_file(path))
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON in prompt file: {path}") from exc

    if not prompts:
        raise ValueError(
            "Prompt files did not contain any valid prompt objects. "
            f"Directory checked: {PROMPTS_DIR}"
        )

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
        "2": "medium",
        "medium": "medium",
        "3": "hard",
        "hard": "hard",
        "4": "expert",
        "expert": "expert",
        "5": "master",
        "master": "master",
        "easy": "easy",
    }
    return aliases.get(raw, "all")


def _difficulty_bucket(value: Any) -> str:
    if isinstance(value, str):
        normalized = normalize_difficulty(value)
        if normalized != "all":
            return normalized

    try:
        score = int(value)
    except (TypeError, ValueError):
        return "all"

    if score == 1:
        return "easy"
    if score == 2:
        return "medium"
    if score == 3:
        return "hard"
    if score == 4:
        return "expert"
    if score == 5:
        return "master"
    return "all"


def list_prompts(prompt_type: str = "all", difficulty: str = "all") -> list[dict[str, Any]]:
    normalized_type = normalize_prompt_type(prompt_type)
    normalized_difficulty = normalize_difficulty(difficulty)
    prompts = _load_prompts()

    def prompt_matches_type(prompt: dict[str, Any]) -> bool:
        if normalized_type == "all":
            return True
        row_type = normalize_prompt_type(str(prompt.get("type", "")))
        return row_type == normalized_type

    return [
        prompt
        for prompt in prompts
        if prompt_matches_type(prompt)
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
