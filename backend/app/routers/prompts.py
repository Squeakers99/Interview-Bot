from fastapi import APIRouter, HTTPException, Query
from app.services.prompt_store import (
    get_random_prompt,
    list_prompts,
    normalize_difficulty,
    normalize_prompt_type,
)

router = APIRouter()

@router.get("/all")
def prompts_all(
    prompt_type: str = Query("all", alias="type"),
    difficulty: str = Query("all"),
):
    normalized_type = normalize_prompt_type(prompt_type)
    normalized_difficulty = normalize_difficulty(difficulty)
    prompts = list_prompts(prompt_type=normalized_type, difficulty=normalized_difficulty)
    return {
        "count": len(prompts),
        "filters": {
            "type": normalized_type,
            "difficulty": normalized_difficulty,
        },
        "prompts": prompts,
    }

@router.get("/random")
def prompt_random(
    prompt_type: str = Query("all", alias="type"),
    difficulty: str = Query("all"),
):
    normalized_type = normalize_prompt_type(prompt_type)
    normalized_difficulty = normalize_difficulty(difficulty)

    try:
        prompt = get_random_prompt(
            prompt_type=normalized_type,
            difficulty=normalized_difficulty,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return {
        "filters": {
            "type": normalized_type,
            "difficulty": normalized_difficulty,
        },
        "prompt": prompt,
    }
