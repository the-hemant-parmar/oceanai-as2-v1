
# Prompt-Driven Email Productivity Agent — Updated

This project is an updated Streamlit-based Email Productivity Agent.

**Key features**
- Streamlit UI with Google OAuth (web flow): users can sign in with their Google accounts (read-only Gmail access).
- Gmail inbox loader fetches each user's latest N emails and saves to `data/mock_inbox.json`.
- Gemini (Google) integration via `google-generativeai` for LLM tasks (set `GEMINI_API_KEY` in environment).
- All prompts editable via Prompt Brain UI.
- Drafts saved locally and never sent automatically.

**Included assignment file**
The original assignment PDF uploaded by you is included at: `assets/Assignment - 2.pdf`

## Setup

1. Place your OAuth client credentials into Streamlit secrets. Create `secrets.toml` or use Streamlit Cloud secrets:
```
[general]
GOOGLE_CLIENT_ID = "<your_client_id>"
GOOGLE_CLIENT_SECRET = "<your_client_secret>"
REDIRECT_URI = "http://localhost:8501/"
```

2. Optional: set `GEMINI_API_KEY` environment variable for LLM features.

3. Install dependencies:
```
pip install -r requirements.txt
```

4. Run:
```
streamlit run app.py
```

## Notes
- The app uses a web OAuth flow — when users click Sign in with Google they authenticate with their own Google account.
- The app only requests read-only Gmail scope.
- The included assignment PDF path inside the project is `assets/Assignment - 2.pdf`.

