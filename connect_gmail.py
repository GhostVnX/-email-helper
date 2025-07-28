import json
import pickle
import os
import base64
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from email.mime.text import MIMEText
from googleapiclient.discovery import build
import streamlit as st

SCOPES = ['https://www.googleapis.com/auth/gmail.send']

def login_to_gmail():
    creds = None
    if os.path.exists("token.pickle"):
        with open("token.pickle", "rb") as token:
            creds = pickle.load(token)

    if creds and creds.valid:
        return creds

    flow = InstalledAppFlow.from_client_config(
        json.loads(st.secrets["GOOGLE_CLIENT_SECRET"]),
        SCOPES
    )

    auth_url, _ = flow.authorization_url(prompt='consent')

    st.info("To connect Gmail, follow this link below:")
    st.markdown(f"[Click here to authorize Gmail]({auth_url})")

    auth_code = st.text_input("Paste the authorization code here:")

    if auth_code:
        try:
            flow.fetch_token(code=auth_code)
            creds = flow.credentials
            with open("token.pickle", "wb") as token:
                pickle.dump(creds, token)
            st.success("✅ Gmail authenticated successfully!")
            return creds
        except Exception as e:
            st.error(f"Error: {e}")

    st.stop()

def send_email(creds, to, subject, message_text):
    service = build("gmail", "v1", credentials=creds)
    message = MIMEText(message_text, "html")
    message["to"] = to
    message["subject"] = subject
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
    body = {"raw": raw}
    return service.users().messages().send(userId="me", body=body).execute()
