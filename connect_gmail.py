# connect_gmail.py
import os
import json
import base64
from email.mime.text import MIMEText
from googleapiclient.discovery import build
from google.oauth2 import service_account
import time

# Service account credentials and impersonation
SERVICE_ACCOUNT_FILE = "ghost-467114-bec02d5ffef4.json"
SCOPES = ["https://www.googleapis.com/auth/gmail.send"]
IMPERSONATED_USER = "admin@ghostvnx.com"  # 👈 your verified Workspace user

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
        sent = service.users().messages().send(userId="me", body=message).execute()
        return sent
    except Exception as e:
        return {"error": str(e)}


def send_follow_up(creds, to, subject, message_text, delay_minutes=10):
    time.sleep(delay_minutes * 60)
    follow_up_subject = f"Follow-up: {subject}"
    follow_up_message = f"Hi again,<br><br>Just checking in:<br><br>{message_text}"
    send_email(creds, to, follow_up_subject, follow_up_message)


def load_sent_log():
    if os.path.exists("sent_log.json"):
        with open("sent_log.json", "r") as f:
            return json.load(f)
    return {}

def save_sent_log(log):
    with open("sent_log.json", "w") as f:
        json.dump(log, f)
