# connect_gmail.py
import os
import pickle
import base64
import json
from email.mime.text import MIMEText
from googleapiclient.discovery import build
from google.oauth2 import service_account

SERVICE_ACCOUNT_FILE = "ghost-467114-bec02d5ffef4.json"
SCOPES = ["https://www.googleapis.com/auth/gmail.send"]
IMPERSONATED_USER = "admin@ghostvnx.com"

def login_to_gmail():
    try:
        creds = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE,
            scopes=SCOPES,
            subject=IMPERSONATED_USER
        )
        return creds
    except Exception as e:
        raise RuntimeError("Gmail login failed: " + str(e))


def send_email(creds, to, subject, message_text):
    try:
        service = build("gmail", "v1", credentials=creds)
        message = MIMEText(message_text, "html")
        message["to"] = to
        message["subject"] = subject
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
        message = {"raw": raw}
        send = service.users().messages().send(userId="me", body=message).execute()
        return send
    except Exception as e:
        return {"error": str(e)}


# Optional: Follow-up scheduler
import time

def send_follow_up(creds, to, subject, message_text, delay_minutes=10):
    time.sleep(delay_minutes * 60)
    follow_up_subject = f"Follow-up: {subject}"
    follow_up_message = f"Hi again,<br><br>Just checking in on my previous message:<br><br>{message_text}"
    send_email(creds, to, follow_up_subject, follow_up_message)

def load_sent_log():
    log_file = "sent_log.json"
    if os.path.exists(log_file):
        with open(log_file, "r") as f:
            return json.load(f)
    return {}

def save_sent_log(log):
    with open("sent_log.json", "w") as f:
        json.dump(log, f)
