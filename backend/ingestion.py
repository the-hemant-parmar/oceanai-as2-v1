from backend.mongo_db import get_db
from backend.agent import simple_categorize, simple_extract_actions
from backend.mongo_db import get_db
import streamlit as st
import time


def upsert_processed(data):
    db = get_db()
    coll = db.processed
    coll.update_one(
        {"user_email": st.session_state["user_email"]},
        {"$set": {**data, "updated_at": int(time.time())}},
        upsert=True,
    )


def get_processed():
    db = get_db()
    coll = db.processed
    return list(coll.find({"user_email": st.session_state["user_email"]}))


def save_categories(custom_list):
    db = get_db()
    db.categories.update_one(
        {"user_email": st.session_state["user_email"]},
        {"$set": {"custom_categories": custom_list}},
        upsert=True,
    )


def run_ingestion(inbox: list = [], prompts: dict = None):
    processed = {}
    if prompts is None:
        prompts = prompts_module.load_prompts()

    for idx, email in enumerate(inbox):
        key = str(email.get("email_id", idx))
        if key in processed:
            continue
        try:
            category_resp = simple_categorize(email, prompts["categorization"])
            actions_resp = simple_extract_actions(email, prompts["action_item"])
            processed[key] = {"category": category_resp, "actions": actions_resp}
        except Exception as e:
            processed[key] = {"error": str(e)}

    upsert_processed(processed)
    return processed
