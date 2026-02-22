import html
import re
from urllib.parse import urlparse

import httpx
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from app.services.prompt_store import (
    get_random_prompt,
    list_prompts,
    normalize_difficulty,
    normalize_prompt_type,
)
from app.services.job_ad_prompt_service import generate_prompt_from_job_ad_with_grok

router = APIRouter()


class JobAdPromptRequest(BaseModel):
    url: str = Field(..., min_length=8)
    prompt_type: str = "all"
    difficulty: str = "all"


def _extract_title(raw_html: str) -> str:
    for pattern in (
        r'<meta[^>]+property=["\']og:title["\'][^>]+content=["\'](.*?)["\']',
        r'<meta[^>]+name=["\']twitter:title["\'][^>]+content=["\'](.*?)["\']',
        r"<title[^>]*>(.*?)</title>",
        r"<h1[^>]*>(.*?)</h1>",
    ):
        match = re.search(pattern, raw_html, flags=re.IGNORECASE | re.DOTALL)
        if not match:
            continue
        text = re.sub(r"<[^>]+>", " ", match.group(1))
        text = re.sub(r"\s+", " ", html.unescape(text)).strip()
        if text:
            return text
    return ""


def _extract_visible_text(raw_html: str) -> str:
    cleaned = re.sub(
        r"<(script|style|noscript|svg|iframe)[^>]*>.*?</\1>",
        " ",
        raw_html,
        flags=re.IGNORECASE | re.DOTALL,
    )
    cleaned = re.sub(r"<!--.*?-->", " ", cleaned, flags=re.DOTALL)
    cleaned = re.sub(r"<br\s*/?>", "\n", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"</(p|div|li|section|article|h\d)>", "\n", cleaned, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", cleaned)
    text = html.unescape(text)
    text = re.sub(r"[ \t\r\f\v]+", " ", text)
    text = re.sub(r"\n\s*\n+", "\n", text)
    return text.strip()


async def _fetch_job_ad(url: str) -> dict:
    parsed = urlparse(url.strip())
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise HTTPException(status_code=400, detail="Please provide a valid http(s) job ad URL.")

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122 Safari/537.36"
        )
    }
    try:
        async with httpx.AsyncClient(timeout=12.0, follow_redirects=True, headers=headers) as client:
            response = await client.get(url)
            response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Job ad request failed with status {exc.response.status_code}.",
        ) from exc
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"Could not fetch job ad URL: {exc}") from exc

    content_type = (response.headers.get("content-type") or "").lower()
    text_start = response.text.lstrip()[:200].lower()
    if "html" not in content_type and "<!doctype html" not in text_start and "<html" not in text_start:
        raise HTTPException(status_code=400, detail="URL did not return an HTML page.")

    raw_html = response.text
    title = _extract_title(raw_html) or parsed.netloc
    visible_text = _extract_visible_text(raw_html)
    if len(visible_text) < 200:
        raise HTTPException(
            status_code=400,
            detail="Could not extract enough readable text from this page. Try another job ad URL.",
        )

    return {
        "url": str(response.url),
        "domain": parsed.netloc,
        "title": title,
        "text": visible_text[:12000],
        "excerpt": visible_text[:600],
    }

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


@router.post("/from-job-ad")
async def prompt_from_job_ad(request: JobAdPromptRequest):
    normalized_type = normalize_prompt_type(request.prompt_type)
    normalized_difficulty = normalize_difficulty(request.difficulty)
    job_ad = await _fetch_job_ad(request.url)
    try:
        prompt = generate_prompt_from_job_ad_with_grok(
            job_url=job_ad["url"],
            job_title=job_ad["title"],
            job_text=job_ad["text"],
            prompt_type=normalized_type,
            difficulty=normalized_difficulty,
        )
    except ValueError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Grok prompt generation failed: {exc}") from exc

    return {
        "filters": {
            "type": normalized_type,
            "difficulty": normalized_difficulty,
        },
        "job_ad": {
            "url": job_ad["url"],
            "domain": job_ad["domain"],
            "title": job_ad["title"],
            "excerpt": job_ad["excerpt"],
        },
        "prompt": prompt,
    }
