from pathlib import Path
import streamlit as st
import time
from backend.mongo_db import get_db

DATA_DIR = Path("data")
PROMPT_FILE = DATA_DIR / "prompts.json"

DEFAULT_PROMPTS = {
    "categorization": "Categorize this email into one of: Important, Newsletter, Spam, To-Do. To-Do must be used when the email contains a direct request requiring user action.",
    "action_item": "Extract tasks from the email. Respond in JSON: [{ 'task': '...', 'deadline': '...', 'assignee': '...' }]. If none, return an empty array.",
    "auto_reply": "If the email requests an action, draft a polite reply appropriate to the request. Return JSON: {'subject': '...','body': '...','followups': ['...']}. Keep replies concise (3-6 sentences).",
    "tone_instructions": "If user specifies a tone (friendly/professional/concise), adapt the reply accordingly.",
}

db = get_db()


def save_prompts(new_prompts):
    db.prompts.insert_one(
        {
            "user_email": st.session_state["user_email"],
            "timestamp": int(time.time()),
            "prompt_brain": new_prompts,
        }
    )


def load_prompts():
    prompt_data = db.prompts.find(
        {"user_email": st.session_state["user_email"]}
    ).to_list()
    if prompt_data:
        prompts = dict(prompt_data[0])["prompt_brain"]
        return prompts
    else:
        reset_prompts()
        return DEFAULT_PROMPTS


def reset_prompts():
    save_prompts(DEFAULT_PROMPTS)
