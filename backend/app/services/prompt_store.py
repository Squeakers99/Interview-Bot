import random
from typing import Dict, List, Optional

# Later you can replace this with a DB, Notion, etc.
PROMPTS: List[Dict[str, str]] = [
    {
        "id": "p1",
        "text": "Tell me about a time you faced a challenge and how you handled it.",
        "type": "behavioral",
        "difficulty": "medium",
    },
    {
        "id": "p2",
        "text": "Describe a time you led a team through a conflict or setback.",
        "type": "behavioral",
        "difficulty": "hard",
    },
    {
        "id": "p3",
        "text": "Tell me about a time you failed and what you learned from it.",
        "type": "behavioral",
        "difficulty": "medium",
    },
    {
        "id": "p4",
        "text": "Describe a situation where you had to work with someone difficult.",
        "type": "behavioral",
        "difficulty": "hard",
    },
    {
        "id": "p5",
        "text": "Tell me about a project you're proud of and what your impact was.",
        "type": "behavioral",
        "difficulty": "easy",
    },
    {
        "id": "p6",
        "text": "Tell me about yourself and background.",
        "type": "general",
        "difficulty": "easy",
    },
    {
        "id": "p7",
        "text": "Tell me about your strengths and weaknesses.",
        "type": "general",
        "difficulty": "medium",
    },
    {
        "id": "p8",
        "text": "Tell me about a time you had lots of tasks and how you prioritized them.",
        "type": "behavioral",
        "difficulty": "medium",
    },
    {
        "id": "p9",
        "text": "Why did you apply for this job?",
        "type": "general",
        "difficulty": "easy",
    },
    {
        "id": "p10",
        "text": "Describe your ideal work environment.",
        "type": "situational",
        "difficulty": "easy",
    },
    {
        "id": "p11",
        "text": "Tell me about a time you asked for feedback.",
        "type": "behavioral",
        "difficulty": "easy",
    },
    {
        "id": "p12",
        "text": "What made you want to choose this area of study?",
        "type": "general",
        "difficulty": "easy",
    },
    {
        "id": "p13",
        "text": "What specific skills and experiences are you looking forward to in this role?",
        "type": "general",
        "difficulty": "medium",
    },
    {
        "id": "p14",
        "text": "Why are you looking for a job?",
        "type": "general",
        "difficulty": "easy",
    },
    {
        "id": "p15",
        "text": "How do you deal with pressure and stressful situations?",
        "type": "situational",
        "difficulty": "medium",
    },
    {
        "id": "p16",
        "text": "What is the hardest technical problem you have ever tackled?",
        "type": "technical",
        "difficulty": "hard",
    },
    {
        "id": "p17",
        "text": "What differentiates you from other candidates?",
        "type": "general",
        "difficulty": "medium",
    },
    {
        "id": "p18",
        "text": "What is your favorite subject and why?",
        "type": "general",
        "difficulty": "easy",
    },
    {
        "id": "p19",
        "text": "What is your least favorite subject and why?",
        "type": "general",
        "difficulty": "easy",
    },
    {
        "id": "p20",
        "text": "Walk me through your resume.",
        "type": "general",
        "difficulty": "medium",
    },
    {
        "id": "p21",
        "text": "Where do you see yourself in 5 years?",
        "type": "general",
        "difficulty": "medium",
    },
    {
        "id": "p22",
        "text": "Tell me about a time you worked in a team.",
        "type": "behavioral",
        "difficulty": "easy",
    },
    {
        "id": "p23",
        "text": "Describe a conflict with a coworker.",
        "type": "behavioral",
        "difficulty": "hard",
    },
    {
        "id": "p24",
        "text": "How do you handle pressure?",
        "type": "situational",
        "difficulty": "medium",
    },
    {
        "id": "p25",
        "text": "Explain the difference between REST and GraphQL APIs and when to use each.",
        "type": "technical",
        "difficulty": "easy",
    },
    {
        "id": "p26",
        "text": "How would you design a URL shortener service?",
        "type": "technical",
        "difficulty": "medium",
    },
    {
        "id": "p27",
        "text": "Describe a debugging process you would use for a memory leak in production.",
        "type": "technical",
        "difficulty": "medium",
    },
    {
        "id": "p28",
        "text": "How would you choose between SQL and NoSQL for a high-scale application?",
        "type": "technical",
        "difficulty": "hard",
    },
    {
        "id": "p29",
        "text": "A key endpoint is slow under load. Walk through your optimization strategy.",
        "type": "technical",
        "difficulty": "hard",
    },
    {
        "id": "p30",
        "text": "You're given an urgent deadline and missing requirements. How do you proceed?",
        "type": "situational",
        "difficulty": "hard",
    },
]

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
