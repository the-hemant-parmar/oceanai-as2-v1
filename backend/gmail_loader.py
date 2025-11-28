import base64
from email.message import EmailMessage
import time
from urllib.parse import urlencode
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
import requests
import streamlit as st
from .mongo_db import get_db

# These should be stored securely; Streamlit secrets is recommended (st.secrets)
CLIENT_ID = st.secrets["GOOGLE_CLIENT_ID"]
CLIENT_SECRET = st.secrets["GOOGLE_CLIENT_SECRET"]
REDIRECT_URI = st.secrets["REDIRECT_URI"]

AUTH_URL = "https://accounts.google.com/o/oauth2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"
USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"

SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
    "https://www.googleapis.com/auth/gmail.compose",
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/gmail.readonly",
]

flow = Flow.from_client_config(
    client_config={
        "web": {
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "redirect_uris": [REDIRECT_URI],
            "auth_uri": AUTH_URL,
            "token_uri": TOKEN_URL,
        }
    },
    scopes=SCOPES,
)


def generate_oauth_url():
    authorization_url, _ = flow.authorization_url()
    authorization_url += "&" + urlencode({"redirect_uri": REDIRECT_URI})
    return authorization_url


def handle_oauth_callback(query_params):
    # exchange code for tokens and store in session_state
    code = query_params["code"][0]

    if not code:
        raise ValueError("No code in callback.")

    flow.redirect_uri = REDIRECT_URI
    flow.fetch_token(code=query_params["code"])
    creds = flow.credentials
    access_token = str(creds.token)

    headers = {"Authorization": f"Bearer {access_token}"}
    userinfo_resp = requests.get(USERINFO_URL, headers=headers)
    userinfo_resp.raise_for_status()
    userinfo = userinfo_resp.json()
    user_email = userinfo.get("email")

    # Save tokens & basic profile in Mongo
    db = get_db()
    users = db.users
    # Upsert user tokens (note: storing refresh token for reuse; rotate/encrypt for production)
    users.update_one(
        {"email": user_email},
        {
            "$set": {
                "email": user_email,
                "name": userinfo.get("name"),
                "picture": userinfo.get("picture"),
                "access_token": access_token,  # access_token, refresh_token, expires_in, scope, token_type
            }
        },
        upsert=True,
    )

    try:
        st.session_state["oauth_token"] = access_token
        st.session_state["user_email"] = user_email
        st.session_state["oauth_state"] = "connected"
    except:
        print("something wrong in session state")
    return


def fetch_inbox_with_token(n=20):
    if "oauth_token" not in st.session_state or "user_email" not in st.session_state:
        raise RuntimeError("No oauth token. Please authenticate first.")

    service = build("gmail", "v1", credentials=flow.credentials)
    print("serivicing is done ")
    results = service.users().messages().list(userId="me", maxResults=n).execute()
    messages = results.get("messages", [])

    db = get_db()
    inbox_coll = db.inboxes

    emails = []
    for msg in messages:
        msg_data = (
            service.users()
            .messages()
            .get(userId="me", id=msg["id"], format="full")
            .execute()
        )
        headers = msg_data.get("payload", {}).get("headers", [])
        subject = next((h["value"] for h in headers if h["name"] == "Subject"), "")
        sender = next((h["value"] for h in headers if h["name"] == "From"), "")
        timestamp = msg_data.get("internalDate", "")
        body = ""
        payload = msg_data.get("payload", {})
        # handle simple parts
        if "parts" in payload:
            for part in payload["parts"]:
                if part.get("mimeType") == "text/plain":
                    data = part.get("body", {}).get("data")
                    if data:
                        body = base64.urlsafe_b64decode(data).decode(
                            "utf-8", errors="ignore"
                        )
                        break
        else:
            data = payload.get("body", {}).get("data")
            if data:
                body = base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")

        email_doc = {
            "user_email": st.session_state["user_email"],
            "email_id": msg["id"],
            "sender": sender,
            "subject": subject,
            "timestamp": timestamp,
            "body": body,
            "fetched_at": time.time(),
        }

        inbox_coll.update_one(
            {"user_email": st.session_state["user_email"], "email_id": msg["id"]},
            {"$set": email_doc},
            upsert=True,
        )
        emails.append(email_doc)

    return emails


# ------- TO HANDLE DRAFTS ------------------------------
def create_gmail_draft(subject: str, body: str, to_addr: str = None):
    """
    Create a Gmail draft in the authenticated user's account and save metadata to Mongo.
    Returns the created Gmail draft id and stored doc.
    """
    service = (
        build("gmail", "v1", credentials=flow.credentials),
        st.session_state["user_email"],
    )
    user_email = st.session_state["user_email"]

    # Build MIME message
    msg = EmailMessage()
    from_header = user_email
    to_header = to_addr or user_email  # for drafts you can use user_email or recipient
    msg["From"] = from_header
    msg["To"] = to_header
    msg["Subject"] = subject
    msg.set_content(body)

    raw_bytes = msg.as_bytes()
    raw_b64 = base64.urlsafe_b64encode(raw_bytes).decode("utf-8")

    body_payload = {"message": {"raw": raw_b64}}

    draft = service.users().drafts().create(userId="me", body=body_payload).execute()
    draft_id = draft.get("id")
    # save to Mongo
    db = get_db()
    drafts_coll = db.drafts
    doc = {
        "user_email": user_email,
        "gmail_draft_id": draft_id,
        "subject": subject,
        "body": body,
        "created_at": int(__import__("time").time()),
    }
    res = drafts_coll.insert_one(doc)
    doc["_id"] = str(res.inserted_id)
    return {"gmail_draft_id": draft_id, "doc": doc}
