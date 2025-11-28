# Prompt-Driven Email Productivity Agent

This project is a Streamlit-based Email Productivity Agent.

**Key features**

-   Streamlit UI with Google OAuth (web flow): users can sign in with their Google accounts (read-only Gmail access).
-   Gmail inbox loader fetches each user's latest N emails.
-   Gemini (Google) integration via `google-genai` for LLM tasks (set `GEMINI_API_KEY` in environment).
-   All prompts are editable via Prompt Brain UI.
-   Drafts saved locally and never sent automatically.

## Setup

1. Place your OAuth client credentials into Streamlit secrets. Create `secrets.toml` or use Streamlit Cloud secrets:

```
GOOGLE_CLIENT_ID = "<your_client_id>"
GOOGLE_CLIENT_SECRET = "<your_client_secret>"
REDIRECT_URI = "http://localhost:8501/"
GEMINI_API_KEY = <your_gemini_api_key>
MONGO_URI = <your_mongo_db_connection_string>
```

2. Optional: set `GEMINI_API_KEY` environment variable also for LLM features.

3. Install dependencies:

```
pip install -r requirements.txt
```

4. Run:

```
streamlit run app.py
```

## Notes

-   The app uses a web OAuth flow — when users click Sign in with Google they authenticate with their own Google account.
-   The app will only save drafts for the auto-reply mail and won't send them.
