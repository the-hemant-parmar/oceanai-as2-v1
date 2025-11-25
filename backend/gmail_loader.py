import os
import base64
from pathlib import Path
from urllib.parse import urlencode
import requests
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import streamlit as st

# These should be stored securely; Streamlit secrets is recommended (st.secrets)
CLIENT_ID = st.secrets["GOOGLE_CLIENT_ID"]
CLIENT_SECRET = st.secrets["GOOGLE_CLIENT_SECRET"]
REDIRECT_URI = st.secrets["REDIRECT_URI"]

AUTH_URL = "https://accounts.google.com/o/oauth2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"

SCOPES = [
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

    try:
        st.session_state["oauth_token"] = str(creds.token)
        st.session_state["oauth_state"] = "connected"
    except:
        print("something wrong in session state")
    return


def fetch_inbox_with_token(n=20):
    if "oauth_token" not in st.session_state:
        raise RuntimeError("No oauth token. Please authenticate first.")

    service = build("gmail", "v1", credentials=flow.credentials)
    print("serivicing is done ")
    results = service.users().messages().list(userId="me", maxResults=n).execute()
    messages = results.get("messages", [])
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
        emails.append(
            {
                "id": msg["id"],
                "sender": sender,
                "subject": subject,
                "timestamp": timestamp,
                "body": body,
            }
        )
    return emails
