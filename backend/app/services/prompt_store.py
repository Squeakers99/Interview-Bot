import random
from typing import Dict, List

# Later you can replace this with a DB, Notion, etc.
PROMPTS: List[Dict[str, str]] = [
    {"id": "p1", "text": "Tell me about a time you faced a challenge and how you handled it."},
    {"id": "p2", "text": "Describe a time you led a team through a conflict or setback."},
    {"id": "p3", "text": "Tell me about a time you failed and what you learned from it."},
    {"id": "p4", "text": "Describe a situation where you had to work with someone difficult."},
    {"id": "p5", "text": "Tell me about a project you’re proud of and what your impact was."},
]

def list_prompts() -> List[Dict[str, str]]:
    return PROMPTS

def get_random_prompt() -> Dict[str, str]:
    return random.choice(PROMPTS)
