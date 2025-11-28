import streamlit as st
from pathlib import Path
import json
from backend import (
    db,
    prompts as prompts_module,
    ingestion,
    agent as agent_module,
    drafts as drafts_module,
)
from backend.gmail_loader import (
    generate_oauth_url,
    handle_oauth_callback,
    fetch_inbox_with_token,
    create_gmail_draft,
)
from backend.mongo_db import get_db


DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

st.set_page_config(page_title="Prompt-Driven Email Agent", layout="wide")

# --- Sidebar navigation ---
st.sidebar.title("Email Agent")
page = st.sidebar.radio(
    "Go to",
    ["Inbox Loader", "Prompt Brain", "Email Agent", "Draft Manager", "About"],
)

# Load prompts and data
prompts = prompts_module.load_prompts()
processed = db.load_json(DATA_DIR / "processed.json", default={})


def refresh():
    st.rerun()


# --- Page: Inbox Loader ---
if page == "Inbox Loader":
    st.title("Inbox Loader")
    st.markdown(
        "Load emails from a mock inbox (local JSON) or connect your Gmail account."
    )

    # Mock upload
    uploaded = st.file_uploader("Upload mock_inbox.json", type=["json"])
    if uploaded:
        inbox = json.load(uploaded)
        db.save_json(DATA_DIR / "mock_inbox.json", inbox)
        st.success("mock_inbox.json uploaded and saved.")
        refresh()

    st.markdown("---")
    st.subheader("Sign in with Google (Gmail)")

    # Show user's inbox from Mongo
    if "user_email" in st.session_state:
        db = get_db()
        inbox_coll = db.inboxes
        user_email = st.session_state["user_email"]
        # optionally apply processed tags from processed.json or from processed collection if you add one
        cursor = (
            inbox_coll.find({"user_email": user_email})
            .sort("fetched_at", -1)
            .limit(200)
        )
        emails = list(cursor)
        # display as dataframe
        import pandas as pd

        df = pd.DataFrame(
            [
                {
                    "email_id": e["email_id"],
                    "sender": e["sender"],
                    "subject": e["subject"],
                    "timestamp": e["timestamp"],
                }
                for e in emails
            ]
        )
        st.dataframe(df)
    else:
        st.info("Please sign in with Google to view your inbox.")

    # OAuth link and callback handling
    query_params = st.query_params
    if "code" in query_params:
        # handle code exchange (callback)
        try:
            handle_oauth_callback(query_params)
            st.success("Authenticated successfully. You can now fetch emails.")
            st.query_params.clear()
        except Exception as e:
            print(e)
            st.error(f"Authentication failed: {e}")

    if "oauth_state" not in st.session_state:
        oauth_url = generate_oauth_url()
        st.markdown(f"[Sign in with Google]({oauth_url})")
    else:
        st.success("Connected to Gmail (session active).")
        n = st.number_input(
            "Number of latest emails to load", min_value=1, max_value=100, value=20
        )
        if st.button("Load latest emails from Gmail"):
            try:
                emails = fetch_inbox_with_token(n)
                db.save_json(DATA_DIR / "mock_inbox.json", emails)
                st.success(f"Loaded {len(emails)} emails into data/mock_inbox.json")
                # refresh()
            except Exception as e:
                st.error(f"Error fetching emails: {e}")

    st.markdown("---")
    st.info(
        "You can also run ingestion after loading emails to categorize and extract action items."
    )
    if st.button("Run ingestion (categorize & extract)"):
        ingestion.run_ingestion(str(DATA_DIR), prompts)
        st.success("Ingestion complete.")
        refresh()

# Prompt Brain
elif page == "Prompt Brain":
    st.title("Prompt Brain — Edit templates")
    prompts = prompts_module.load_prompts()
    with st.form("prompts_form"):
        cat = st.text_area(
            "Categorization Prompt", value=prompts["categorization"], height=120
        )
        action = st.text_area(
            "Action-item Extraction Prompt", value=prompts["action_item"], height=120
        )
        reply = st.text_area(
            "Auto-Reply Draft Prompt", value=prompts["auto_reply"], height=120
        )
        tone = st.text_area(
            "Optional Tone Prompt",
            value=prompts.get("tone_instructions", ""),
            height=80,
        )
        submitted = st.form_submit_button("Save prompts")
        if submitted:
            new = {
                "categorization": cat,
                "action_item": action,
                "auto_reply": reply,
                "tone_instructions": tone,
            }
            prompts_module.save_prompts(new)
            st.success("Prompts saved.")
            refresh()
    if st.button("Reset to defaults"):
        prompts_module.reset_prompts()
        st.success("Prompts reset.")
        refresh()

# Email Agent
elif page == "Email Agent":
    st.title("Email Agent")
    inbox = db.load_json(DATA_DIR / "mock_inbox.json", default=[])
    if not inbox:
        st.info("No emails loaded. Use Inbox Loader to upload or connect Gmail.")
    else:
        subjects = [e["subject"] for e in inbox]
        selected = st.sidebar.selectbox("Select email", options=subjects)
        email = next(e for e in inbox if e["subject"] == selected)
        st.subheader(f"From: {email.get('sender')}  |  Subject: {email.get('subject')}")
        st.write("**Timestamp:**", email.get("timestamp"))
        st.markdown("---")
        st.write(email.get("body"))

        st.markdown("---")
        st.subheader("Ask the Agent")
        question = st.text_input(
            "Instruction (e.g. 'Summarize this email', 'What tasks do I need to do?', 'Draft a reply in tone: friendly')",
            value="",
        )
        if st.button("Run Agent"):
            with st.spinner("Running agent..."):
                response = agent_module.run_agent_on_email(email, question, prompts)
                if isinstance(response, dict) and response.get("structured"):
                    st.json(response)
                else:
                    st.markdown("**Agent response:**")
                    st.write(
                        response.get("text") if isinstance(response, dict) else response
                    )

                if isinstance(response, dict) and response.get("draft"):
                    if st.button("Save draft"):
                        drafts_module.save_draft(response["draft"], str(DATA_DIR))
                        st.success("Draft saved.")

# Draft Manager
elif page == "Draft Manager":

    if "user_email" not in st.session_state:
        st.info("Please sign in.")
    else:
        db = get_db()
        drafts_coll = db.drafts
        user = st.session_state["user_email"]
        docs = list(drafts_coll.find({"user_email": user}).sort("created_at", -1))
        for d in docs:
            with st.expander(f"{d.get('subject')}"):
                st.write(d.get("body"))
                if st.button(f"Push this draft to Gmail ({d.get('_id')})"):
                    # use create_gmail_draft to create draft in Gmail and update DB
                    res = create_gmail_draft(d.get("subject"), d.get("body"))
                    drafts_coll.update_one(
                        {"_id": d["_id"]},
                        {"$set": {"gmail_draft_id": res["gmail_draft_id"]}},
                    )
                    st.success("Draft pushed to Gmail.")


# About
elif page == "About":
    st.title("About & Assignment")
    st.markdown("- Built with Streamlit frontend.")
    st.markdown("- Prompts are stored in `data/prompts.json` and editable.")
    st.markdown(
        "- LLM integration uses Google Gemini via `google-generativeai` when `GEMINI_API_KEY` is set."
    )
    st.markdown(
        "- OAuth-based Gmail sign-in lets any user connect their inbox (read-only)."
    )
