import streamlit as st
from google.oauth2 import service_account
from googleapiclient.discovery import build
from email.mime.text import MIMEText
import base64
import time
import json
import pickle
import os

# Load credentials from Streamlit secrets
def login_to_gmail():
    try:
        # Convert st.secrets section to regular dict
        secrets_dict = dict(st.secrets["gmail_service"])

        # Authenticate using service account credentials
        creds = service_account.Credentials.from_service_account_info(
            secrets_dict,
            scopes=["https://www.googleapis.com/auth/gmail.send"]
        )

        # Delegate access to a user in your domain
        delegated_creds = creds.with_subject(secrets_dict["gmail_user"])
        return delegated_creds

    except Exception as e:
        raise RuntimeError("Gmail login failed: " + str(e))


# Send a single email
def send_email(creds, to, subject, message_text):
    try:
        service = build("gmail", "v1", credentials=creds)

        message = MIMEText(message_text)
        message["to"] = to
        message["subject"] = subject

        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
        body = {"raw": raw}

        # Duplicate check
        sent_log = load_sent_log()
        if to in sent_log:
            return {"status": "duplicate", "message": "Already sent to this email."}

        # Send
        service.users().messages().send(userId="me", body=body).execute()

        # Save to log
        log_sent_email(to)
        return {"status": "success"}

    except Exception as e:
        return {"error": str(e)}


# Send follow-up email
def send_follow_up(creds, to, subject, message_text, delay_minutes=10):
    time.sleep(delay_minutes * 60)
    follow_up_subject = f"Re: {subject}"
    follow_up_text = f"Just following up on my previous message:\n\n{message_text}"
    send_email(creds, to, follow_up_subject, follow_up_text)


# --- Logging utilities ---

LOG_FILE = "sent_log.pkl"

def log_sent_email(email):
    try:
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, "rb") as f:
                log = pickle.load(f)
        else:
            log = set()
        log.add(email)
        with open(LOG_FILE, "wb") as f:
            pickle.dump(log, f)
    except:
        pass

def load_sent_log():
    try:
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, "rb") as f:
                return pickle.load(f)
        else:
            return set()
    except:
        return set()
