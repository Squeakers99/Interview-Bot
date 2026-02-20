from fastapi import APIRouter
from app.services.prompt_store import list_prompts, get_random_prompt

router = APIRouter()

@router.get("/all")
def prompts_all():
    prompts = list_prompts()
    return {"count": len(prompts), "prompts": prompts}

@router.get("/random")
def prompt_random():
    return {"prompt": get_random_prompt()}
