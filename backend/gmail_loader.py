# backend/gmail_loader.py

from __future__ import print_function
import base64
import json
from email import message_from_bytes
from pathlib import Path

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

def authenticate_gmail():
    """Authenticate user via OAuth and return Gmail service."""
    creds = None
    token_path = Path("token.json")

    if token_path.exists():
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)

    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
        creds = flow.run_local_server(port=0)

        with open("token.json", "w") as token:
            token.write(creds.to_json())

    service = build("gmail", "v1", credentials=creds)
    return service


def get_latest_emails(n=20):
    service = authenticate_gmail()

    results = service.users().messages().list(userId="me", maxResults=n).execute()
    messages = results.get("messages", [])

    emails = []

    for msg in messages:
        msg_data = service.users().messages().get(userId="me", id=msg["id"], format="full").execute()

        headers = msg_data.get("payload", {}).get("headers", [])
        subject = next((h["value"] for h in headers if h["name"] == "Subject"), "")
        sender = next((h["value"] for h in headers if h["name"] == "From"), "")
        timestamp = msg_data.get("internalDate")

        # Extract body
        body = ""

        if "parts" in msg_data["payload"]:
            for part in msg_data["payload"]["parts"]:
                if part.get("mimeType") == "text/plain":
                    data = part["body"].get("data")
                    if data:
                        body = base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")
        else:
            data = msg_data["payload"]["body"].get("data")
            if data:
                body = base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")

        emails.append({
            "id": msg["id"],
            "sender": sender,
            "subject": subject,
            "timestamp": timestamp,
            "body": body
        })

    return emails
