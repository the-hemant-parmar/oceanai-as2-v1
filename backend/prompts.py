# backend/prompts.py
from pathlib import Path
from . import db

DATA_DIR = Path("data")
PROMPT_FILE = DATA_DIR / "prompts.json"

DEFAULT_PROMPTS = {
    "categorization": (
        "Categorize this email into one of: Important, Newsletter, Spam, To-Do.\n"
        "Answer with a single category and short explanation. 'To-Do' must be used when the email contains a direct request requiring user action."
    ),
    "action_item": (
        "Extract action items from the email. Respond in JSON array form where each item has: "
        '{"task": "...", "deadline": "...", "assignee": "..."}\n'
        "If no explicit deadline or assignee, use empty strings."
    ),
    "auto_reply": (
        "Draft a polite reply based on the email content. Keep it concise (3-6 sentences). Include a suggested subject if applicable. Do NOT send — return as a draft object: { 'subject': '...', 'body': '...' }."
    ),
    "tone_instructions": "If user specifies a tone (friendly/professional/concise), adapt the reply accordingly."
}

def load_prompts():
    p = db.load_json(PROMPT_FILE, default=None)
    if not p:
        save_prompts(DEFAULT_PROMPTS)
        return DEFAULT_PROMPTS
    return p

def save_prompts(prompts: dict):
    db.save_json(PROMPT_FILE, prompts)

def reset_prompts():
    save_prompts(DEFAULT_PROMPTS)
