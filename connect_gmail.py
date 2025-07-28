import os
import pickle
import base64
import time
import streamlit as st
from email.mime.text import MIMEText
from google.oauth2 import service_account
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/gmail.send"]

# Utility: Save sent email log to avoid duplicates
def load_sent_log():
    if os.path.exists("sent_log.pkl"):
        with open("sent_log.pkl", "rb") as f:
            return pickle.load(f)
    return set()

def save_sent_log(log):
    with open("sent_log.pkl", "wb") as f:
        pickle.dump(log, f)

# Authenticate Gmail via service account or local config
def login_to_gmail():
    try:
        if "gmail" in st.secrets:
            creds = service_account.Credentials.from_service_account_info(
                st.secrets["gmail"], scopes=SCOPES
            )
        else:
            creds = None
            if os.path.exists("token.pickle"):
                with open("token.pickle", "rb") as token:
                    creds = pickle.load(token)

            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    with open("client_secret.json") as f:
                        client_config = json.load(f)

                    flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
                    creds = flow.run_local_server(port=0)

                with open("token.pickle", "wb") as token:
                    pickle.dump(creds, token)
        return creds
    except Exception as e:
        raise RuntimeError("Gmail login failed: " + str(e))


def send_email(creds, to, subject, message_text):
    try:
        sent_log = load_sent_log()
        if to in sent_log:
            return {"status": "duplicate", "message": f"{to} already sent."}

        service = build("gmail", "v1", credentials=creds)
        message = MIMEText(message_text, "html")
        message["to"] = to
        message["subject"] = subject
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
        body = {"raw": raw}

        service.users().messages().send(userId="me", body=body).execute()

        sent_log.add(to)
        save_sent_log(sent_log)
        return {"status": "success"}
    except Exception as e:
        return {"error": str(e)}


def send_follow_up(creds, to, subject, message_text, delay_minutes=10):
    time.sleep(delay_minutes * 60)
    follow_up_subject = f"Follow-up: {subject}"
    follow_up_msg = f"Hi again,<br><br>Just following up on my previous message.<br><br>{message_text}"
    return send_email(creds, to, follow_up_subject, follow_up_msg)
