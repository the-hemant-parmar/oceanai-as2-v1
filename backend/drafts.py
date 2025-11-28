from .mongo_db import get_db
import streamlit as st
from typing import Dict, Any
from .gmail_loader import create_gmail_draft


def save_draft_to_db(draft: Dict[str, Any], push_to_gmail: bool = False):
    """
    Saves draft to Mongo for the current user.
    If push_to_gmail=True, create the draft in Gmail as well (requires user OAuth).
    """
    if "user_email" not in st.session_state:
        raise RuntimeError("User not authenticated.")

    user_email = st.session_state["user_email"]
    db = get_db()

    doc = {
        "user_email": user_email,
        "subject": draft.get("subject"),
        "body": draft.get("body"),
        "meta": draft.get("meta", {}),
        "created_at": int(__import__("time").time()),
    }

    # Insert to Mongo
    res = db.drafts.insert_one(doc)
    doc["_id"] = str(res.inserted_id)

    # Optionally create a Gmail draft and record the gmail_draft_id
    if push_to_gmail:
        res2 = create_gmail_draft(
            doc["subject"], doc["body"], to_addr=doc["meta"].get("to")
        )
        # update doc with gmail_draft_id
        db.drafts.update_one(
            {"_id": res.inserted_id},
            {"$set": {"gmail_draft_id": res2["gmail_draft_id"]}},
        )
        doc["gmail_draft_id"] = res2["gmail_draft_id"]

    return doc
