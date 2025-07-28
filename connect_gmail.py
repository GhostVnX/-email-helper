# connect_gmail.py
import os
import pickle
import base64
import time
from email.mime.text import MIMEText
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/gmail.send"]
LOG_FILE = "sent_log.pkl"

# Load previously sent log to prevent duplicates
def load_sent_log():
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "rb") as f:
            return pickle.load(f)
    return {}

def save_sent_log(log):
    with open(LOG_FILE, "wb") as f:
        pickle.dump(log, f)

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
            try:
                creds = flow.run_local_server(port=0)
            except Exception as e:
                raise RuntimeError("Gmail login failed: " + str(e))

        with open("token.pickle", "wb") as token:
            pickle.dump(creds, token)

    return creds

def send_email(creds, to, subject, body):
    sent_log = load_sent_log()
    if to in sent_log:
        return {"status": "duplicate", "message": f"Already sent to {to}"}

    service = build("gmail", "v1", credentials=creds)
    message = MIMEText(body, "html")
    message["to"] = to
    message["subject"] = subject
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
    try:
        result = service.users().messages().send(userId="me", body={"raw": raw}).execute()
        sent_log[to] = time.time()
        save_sent_log(sent_log)
        return result
    except Exception as e:
        return {"error": str(e)}

def send_follow_up(creds, to, subject, body, delay_min=10):
    time.sleep(delay_min * 60)
    follow_subject = f"Follow Up: {subject}"
    follow_body = body + "<br><br>This is a quick follow-up to my previous email. Looking forward to your response."
    send_email(creds, to, follow_subject, follow_body)
