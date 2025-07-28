import os
import pickle
import base64
import json
import streamlit as st
from email.mime.text import MIMEText
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/gmail.send"]

def login_to_gmail():
    creds = None

    if os.path.exists("token.pickle"):
        with open("token.pickle", "rb") as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            client_secret = {
                "installed": {
                    "client_id": "19168390529-eou1nme0dfl22tgm4ikdlb2s6gvoodp6.apps.googleusercontent.com",
                    "project_id": "ghost-467114",
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                    "client_secret": "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",
                    "redirect_uris": ["http://localhost"]
                }
            }

            flow = InstalledAppFlow.from_client_config(client_secret, SCOPES)
            auth_url, _ = flow.authorization_url(prompt='consent')

            st.warning("🔐 Please copy the link below, open it in your browser, sign in with your Gmail account, and paste the code below.")
            st.code(auth_url)
            code = st.text_input("Paste the authorization code here:")

            if code:
                try:
                    flow.fetch_token(code=code)
                    creds = flow.credentials
                    with open("token.pickle", "wb") as token:
                        pickle.dump(creds, token)
                    st.success("✅ Gmail login successful!")
                except Exception as e:
                    st.error(f"❌ Login failed: {e}")
                    st.stop()
            else:
                st.stop()

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
