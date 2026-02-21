import random
from typing import Dict, List

# Later you can replace this with a DB, Notion, etc.
PROMPTS: List[Dict[str, str]] = [
    {"id": "p1", "text": "Tell me about a time you faced a challenge and how you handled it."},
    {"id": "p2", "text": "Describe a time you led a team through a conflict or setback."},
    {"id": "p3", "text": "Tell me about a time you failed and what you learned from it."},
    {"id": "p4", "text": "Describe a situation where you had to work with someone difficult."},
    {"id": "p5", "text": "Tell me about a project you’re proud of and what your impact was."},
    {"id": "p6", "text": "Tell me about yourself and background."},
    {"id": "p7", "text": "Tell me about a your strengths and weaknesses."},
    {"id": "p8", "text": "Tell me about a time you had lots of tasks and how you prioritized them."},
    {"id": "p9", "text": "Why did you apply for this job."},
    {"id": "p10", "text": "Describe your ideal work environment."},
    {"id": "p11", "text": "A time you asked for feedback."},
    {"id": "p12", "text": "What made you want to choose this area of study?"},
    {"id": "p13", "text": "What specific skills and experiences are you looking forward to in this role?"},
    {"id": "p14", "text": "Why are you looking for a job?"},
    {"id": "p15", "text": "How do you deal with pressure and stressful situations?"},
    {"id": "p16", "text": "What is the hardest problem you have ever tackled?"},
    {"id": "p17", "text": "What differentiates you from other candidates?"},
    {"id": "p18", "text": "What is your favorite subject and why?"},
    {"id": "p19", "text": "What is your least favorite subject and why?"},
    {"id": "p20", "text": "Walk me through your resume."},
    {"id": "p21", "text": "Where do you see yourself in 5 years?"},
    {"id": "p22", "text": "Tell me about a time you worked in a team."},
    {"id": "p23", "text": "Describe a conflict with a coworker."},
    {"id": "p24", "text": "How do you handle pressure?"},


]

def list_prompts() -> List[Dict[str, str]]:
    return PROMPTS

def get_random_prompt() -> Dict[str, str]:
    return random.choice(PROMPTS)
