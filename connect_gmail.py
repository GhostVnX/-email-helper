import streamlit as st
import base64
import pickle
import os
from email.mime.text import MIMEText
from google.oauth2 import service_account
from googleapiclient.discovery import build
import time
import json

TOKEN_PATH = "token.pickle"
LOG_FILE = "sent_log.json"

SCOPES = ["https://www.googleapis.com/auth/gmail.send"]

def load_sent_log():
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r") as f:
            return json.load(f)
    return {}

def save_sent_log(log):
    with open(LOG_FILE, "w") as f:
        json.dump(log, f, indent=2)

def login_to_gmail():
    try:
        service_account_info = json.loads(st.secrets["gmail_service"])
        creds = service_account.Credentials.from_service_account_info(
            service_account_info,
            scopes=SCOPES,
        )

        delegated_creds = creds.with_subject(st.secrets["gmail_user"])
        return delegated_creds
    except Exception as e:
        raise RuntimeError("Gmail login failed: " + str(e))

def send_email(creds, to, subject, message_text):
    try:
        sent_log = load_sent_log()
        if to in sent_log:
            return {"status": "duplicate", "message": f"Already emailed {to} at {sent_log[to]}"}

        service = build("gmail", "v1", credentials=creds)

        message = MIMEText(message_text, "plain")
        message["to"] = to
        message["subject"] = subject

        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
        body = {"raw": raw}

        sent_message = service.users().messages().send(userId="me", body=body).execute()

        # Update sent log
        sent_log[to] = time.strftime("%Y-%m-%d %H:%M:%S")
        save_sent_log(sent_log)

        return sent_message
    except Exception as e:
        return {"error": str(e)}

def send_follow_up(creds, to, subject, message_text, delay_minutes=10):
    time.sleep(delay_minutes * 60)
    follow_up_subject = "⏳ Just Checking In: " + subject
    follow_up_body = f"Hi again,\n\nJust following up on my previous message:\n\n{message_text}\n\nBest regards,"
    return send_email(creds, to, follow_up_subject, follow_up_body)
