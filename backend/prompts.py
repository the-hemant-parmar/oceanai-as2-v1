from pathlib import Path
from . import db

DATA_DIR = Path("data")
PROMPT_FILE = DATA_DIR / "prompts.json"

DEFAULT_PROMPTS = {
    "categorization": "Categorize this email into one of: Important, Newsletter, Spam, To-Do. To-Do must be used when the email contains a direct request requiring user action.",
    "action_item": "Extract tasks from the email. Respond in JSON: [{ 'task': '...', 'deadline': '...', 'assignee': '...' }]. If none, return an empty array.",
    "auto_reply": "If the email requests an action, draft a polite reply appropriate to the request. Return JSON: {'subject': '...','body': '...','followups': ['...']}. Keep replies concise (3-6 sentences).",
    "tone_instructions": "If user specifies a tone (friendly/professional/concise), adapt the reply accordingly.",
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
