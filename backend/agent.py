import os
import json
from typing import Dict, Any
from google import genai

# Try to import google-generativeai; operate in fallback mode if not present
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

if GEMINI_API_KEY:
    client = genai.Client()


def call_gemini(prompt: str, max_output_tokens: int = 300) -> str:
    """Wrapper to call Google Gemini."""
    if not GEMINI_API_KEY:
        raise RuntimeError("No GEMINI_API_KEY found. Provide one to enable LLM mode.")

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
    )

    print(response.text)
    return response.text


def simple_categorize(email: Dict[str, Any], categorization_prompt: str) -> str:
    subj = (email.get("subject") or "").lower()
    body = (email.get("body") or "").lower()
    if "unsubscribe" in body or "newsletter" in subj:
        return "Newsletter"
    if "sale" in body or "free" in body:
        return "Spam"
    if any(w in body for w in ["please", "could you", "kindly", "deadline", "due"]):
        return "To-Do"
    return "Important"


def simple_extract_actions(email: Dict[str, Any], action_prompt: str):
    body = email.get("body", "")
    tasks = []
    for line in body.splitlines():
        l = line.strip().lower()
        if l.startswith(("please", "could you", "kindly", "review", "update", "send")):
            tasks.append({"task": line.strip(), "deadline": "", "assignee": ""})
    return tasks


# ---------------- HIGH-LEVEL AGENT ----------------
def run_agent_on_email(email: Dict[str, Any], user_query: str, prompts: Dict[str, str]):
    body = email.get("body", "")
    subject = email.get("subject", "")

    # --- Summaries ---
    if not user_query or user_query.lower().strip() == "summarize this email":
        if GEMINI_API_KEY:
            txt = call_gemini(
                f"Summarize the following email:\n\nSubject: {subject}\n\nBody:\n{body}"
            )
            return {"text": txt}
        else:
            return {"text": " ".join(body.split()[:50]) + "..."}

    # --- Task Extraction ---
    if "task" in user_query.lower() or "todo" in user_query.lower():
        if GEMINI_API_KEY:
            txt = call_gemini(prompts["action_item"] + "\n\nEmail:\n" + body)
            try:
                parsed = json.loads(txt)
            except:
                parsed = {"raw": txt}
            return {"structured": True, "actions": parsed}
        else:
            return {
                "structured": True,
                "actions": simple_extract_actions(
                    email, prompts.get("action_item", "")
                ),
            }

    # --- Draft Reply ---
    if "reply" in user_query.lower() or "draft" in user_query.lower():
        tone = ""
        if "tone:" in user_query.lower():
            tone = user_query.split("tone:")[-1].strip()

        if GEMINI_API_KEY:
            prompt = (
                prompts.get("auto_reply", "")
                + f"\nTone: {tone}\n\nEmail Subject: {subject}\nEmail Body:\n{body}"
            )
            txt = call_gemini(prompt, max_output_tokens=400)

            # Expect JSON
            try:
                draft = json.loads(txt)
            except:
                draft = {"subject": "Re: " + subject, "body": txt}
            return {"draft": draft, "text": "Draft created", "structured": True}
        else:
            draft = {
                "subject": "Re: " + subject,
                "body": "Thanks for reaching out — I’ll get back to you soon.",
            }
            return {"draft": draft, "structured": True}

    # --- General Query ---
    if GEMINI_API_KEY:
        prompt = (
            f"User query: {user_query}\n\n"
            f"Email:\nSubject: {subject}\n{body}\n\n"
            f"Use these prompts:\n{prompts}"
        )
        txt = call_gemini(prompt)
        return {"text": txt}
    return {"text": "Gemini not configured; offline mode is limited."}
