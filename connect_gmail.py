# connect_gmail.py (Enhanced)

import os
import pickle
import time
import json
import base64
import mimetypes
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from google.oauth2 import service_account
from googleapiclient.discovery import build

LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

# Load credentials from Streamlit secrets

def login_to_gmail():
    import streamlit as st
    try:
        secrets_dict = dict(st.secrets["gmail_service"])
        creds = service_account.Credentials.from_service_account_info(
            secrets_dict,
            scopes=["https://www.googleapis.com/auth/gmail.send"]
        )
        delegated_creds = creds.with_subject(secrets_dict["gmail_user"])
        return delegated_creds
    except Exception as e:
        raise RuntimeError("Gmail login failed: " + str(e))


def create_email(to, subject, message_html, tracking_id=None):
    message = MIMEMultipart("alternative")
    message["to"] = to
    message["subject"] = subject

    if tracking_id:
        pixel_url = f"https://your-tracking-domain.com/track?tid={tracking_id}"
        message_html += f'<img src="{pixel_url}" alt="" width="1" height="1">'

    part_html = MIMEText(message_html, "html")
    message.attach(part_html)
    return {"raw": base64.urlsafe_b64encode(message.as_bytes()).decode()}


def send_email(creds, to, subject, message_html, campaign_name="default"):
    try:
        service = build("gmail", "v1", credentials=creds)

        log = load_campaign_log(campaign_name)
        if to in log:
            return {"status": "duplicate", "message": "Already sent."}

        tracking_id = f"{campaign_name}:{to}".replace("@", "_at_").replace(".", "_")
        email_data = create_email(to, subject, message_html, tracking_id)

        service.users().messages().send(userId="me", body=email_data).execute()
        log_sent_email(campaign_name, to)

        return {"status": "success"}

    except Exception as e:
        return {"status": "error", "error": str(e)}


def send_follow_up(creds, to, subject, message_html, delay_minutes=10):
    time.sleep(delay_minutes * 60)
    follow_subject = f"Re: {subject}"
    follow_body = f"Just following up on my last message:<br><br>{message_html}"
    send_email(creds, to, follow_subject, follow_body)


# Logging utils per campaign

def get_log_path(campaign_name):
    return os.path.join(LOG_DIR, f"{campaign_name}_log.pkl")


def log_sent_email(campaign_name, email):
    log = load_campaign_log(campaign_name)
    log.add(email)
    with open(get_log_path(campaign_name), "wb") as f:
        pickle.dump(log, f)


def load_campaign_log(campaign_name):
    path = get_log_path(campaign_name)
    if os.path.exists(path):
        with open(path, "rb") as f:
            return pickle.load(f)
    return set()
