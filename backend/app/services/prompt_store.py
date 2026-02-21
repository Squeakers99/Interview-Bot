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


def list_prompts() -> list[dict[str, Any]]:
    return _load_prompts()


def get_random_prompt() -> dict[str, Any]:
    return random.choice(_load_prompts())
