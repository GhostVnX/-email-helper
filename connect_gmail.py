import os
import pickle
import base64
import json
from email.mime.text import MIMEText
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/gmail.send"]

def login_to_gmail():
    creds = None

    # Load token if exists
    if os.path.exists("token.pickle"):
        with open("token.pickle", "rb") as token:
            creds = pickle.load(token)

    # Authenticate if needed
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # ✅ OAuth credentials (replace with yours if needed)
            client_secret = {
                "installed": {
                    "client_id": "19168390529-eou1nme0dfl22tgm4ikdlb2s6gvoodp6.apps.googleusercontent.com",
                    "project_id": "ghost-467114",
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                    "client_secret": "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",
                    "redirect_uris": ["https://kugqqnrx8v9tkcwpochazr.streamlit.app"]
                }
            }

            flow = InstalledAppFlow.from_client_config(
                client_secret,
                SCOPES,
                redirect_uri="https://kugqqnrx8v9tkcwpochazr.streamlit.app"
            )

            # ✅ Proper method for Streamlit app (interactive redirect)
           creds = flow.run_local_server(port=8888)

        # Save token
        with open("token.pickle", "wb") as token:
            pickle.dump(creds, token)

    return creds


def send_email(creds, to, subject, message_text):
    service = build("gmail", "v1", credentials=creds)
    message = MIMEText(message_text, "html")
    message["to"] = to
    message["subject"] = subject
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
    message = {"raw": raw}
    send = service.users().messages().send(userId="me", body=message).execute()
    return send
