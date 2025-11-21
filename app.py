# app.py
import streamlit as st
from backend import db, prompts as prompts_module, ingestion, agent as agent_module, drafts as drafts_module
import json
from pathlib import Path

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

st.set_page_config(page_title="Prompt-Driven Email Agent", layout="wide")

# --- Sidebar navigation ---
st.sidebar.title("Email Agent")
page = st.sidebar.radio("Go to", ["Inbox Loader", "Prompt Brain", "Email Agent", "Draft Manager", "About"])

# Load data
mock_inbox = db.load_json(DATA_DIR / "mock_inbox.json", default=[])
prompts = prompts_module.load_prompts()
processed = db.load_json(DATA_DIR / "processed.json", default={})
drafts = db.load_json(DATA_DIR / "drafts.json", default=[])

# Utility to refresh
def refresh_state():
    st.experimental_rerun()

# --- Page: Inbox Loader ---
if page == "Inbox Loader":
    st.title("Inbox Loader")
    st.markdown("Upload a mock inbox JSON (or use provided).")
    uploaded = st.file_uploader("Upload mock_inbox.json", type=["json"])
    if uploaded:
        inbox = json.load(uploaded)
        db.save_json(DATA_DIR / "mock_inbox.json", inbox)
        st.success("mock_inbox.json uploaded and saved.")
        mock_inbox = inbox

    st.subheader("Current Inbox")
    if not mock_inbox:
        st.info("Inbox empty. Use Prompt Brain to load sample, or upload mock_inbox.json.")
    else:
        import pandas as pd
        df = pd.DataFrame([{
            "id": e.get("id", idx),
            "sender": e.get("sender",""),
            "subject": e.get("subject",""),
            "timestamp": e.get("timestamp",""),
            "category": processed.get(str(e.get("id", idx)), {}).get("category","(not processed)")
        } for idx,e in enumerate(mock_inbox)])
        st.dataframe(df)

    st.markdown("---")
    st.button("Run ingestion (categorize & extract actions) 🔁", on_click=lambda: ingestion.run_ingestion(str(DATA_DIR), prompts))

# --- Page: Prompt Brain ---
elif page == "Prompt Brain":
    st.title("Prompt Brain — Edit templates")
    st.markdown("Edit and save the prompts which will be used by the agent on all operations.")
    with st.form("prompts_form"):
        cat = st.text_area("Categorization Prompt", value=prompts["categorization"], height=120)
        action = st.text_area("Action-item Extraction Prompt", value=prompts["action_item"], height=120)
        reply = st.text_area("Auto-Reply Draft Prompt", value=prompts["auto_reply"], height=120)
        tone = st.text_area("Optional Tone Prompt (example: friendly/concise)", value=prompts.get("tone_instructions",""), height=80)
        submitted = st.form_submit_button("Save prompts")
        if submitted:
            new = {
                "categorization": cat,
                "action_item": action,
                "auto_reply": reply,
                "tone_instructions": tone
            }
            prompts_module.save_prompts(new)
            st.success("Prompts saved.")

    st.markdown("---")
    if st.button("Reset to defaults"):
        prompts_module.reset_prompts()
        st.experimental_rerun()

# --- Page: Email Agent ---
elif page == "Email Agent":
    st.title("Email Agent")
    inbox = db.load_json(DATA_DIR / "mock_inbox.json", default=[])
    if not inbox:
        st.info("No emails loaded. Use Inbox Loader to upload or add mock_inbox.json.")
    else:
        ids = [str(e.get("id", idx)) for idx,e in enumerate(inbox)]
        selected = st.sidebar.selectbox("Select email", options=ids)
        email = next((e for e in inbox if str(e.get("id","")) == selected), inbox[int(selected)])
        st.subheader(f"From: {email.get('sender')}  |  Subject: {email.get('subject')}")
        st.write("**Timestamp:**", email.get("timestamp"))
        st.markdown("---")
        st.write(email.get("body"))

        st.markdown("---")
        st.subheader("Ask the Agent")
        question = st.text_input("Your instruction (e.g. 'Summarize this email', 'What tasks do I need to do?', 'Draft a reply in a friendly tone')", value="")
        if st.button("Run"):
            with st.spinner("Contacting agent..."):
                response = agent_module.run_agent_on_email(email, question, prompts)
                st.success("Done.")
                if isinstance(response, dict) and response.get("structured"):
                    st.json(response)
                else:
                    st.markdown("**Agent response:**")
                    st.write(response.get("text") if isinstance(response, dict) else response)

                # If a draft was created, prompt to save
                if isinstance(response, dict) and response.get("draft"):
                    if st.button("Save draft"):
                        drafts_module.save_draft(response["draft"], str(DATA_DIR))
                        st.success("Draft saved.")

# --- Page: Draft Manager ---
elif page == "Draft Manager":
    st.title("Draft Manager")
    drafts = db.load_json(DATA_DIR / "drafts.json", [])
    if not drafts:
        st.info("No drafts saved yet.")
    else:
        for i, d in enumerate(drafts):
            with st.expander(f"{i+1}. {d.get('subject','(no subject)')} — {d.get('meta',{}).get('email_id','-')}"):
                st.write("**Subject**")
                new_sub = st.text_input(f"subject_{i}", value=d.get("subject",""))
                st.write("**Body**")
                new_body = st.text_area(f"body_{i}", value=d.get("body",""), height=180)
                if st.button(f"Save changes #{i}"):
                    d["subject"] = new_sub
                    d["body"] = new_body
                    db.save_json(DATA_DIR / "drafts.json", drafts)
                    st.success("Saved.")

        if st.button("Clear all drafts"):
            db.save_json(DATA_DIR / "drafts.json", [])
            st.experimental_rerun()

# --- Page: About ---
elif page == "About":
    st.title("About — Prompt-Driven Email Productivity Agent")
    st.markdown("""
- Built with Streamlit frontend.
- Prompts are stored in `data/prompts.json` and can be edited in the Prompt Brain page.
- LLM integration uses Gemini if `GEMINI_API_KEY` env var is set. Otherwise a safe mock processor is used.
- Drafts are never sent automatically — they are saved as drafts in `data/drafts.json`.

**To run locally:**
1. `pip install -r requirements.txt`
2. `streamlit run app.py`
    """)
