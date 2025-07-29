import streamlit as st
from google.oauth2 import service_account
from googleapiclient.discovery import build
from email.mime.text import MIMEText
import base64
import time
import pickle
import os

# --- Gmail Login ---
def login_to_gmail():
    try:
        secrets_dict = dict(st.secrets["gmail_service"])
        creds = service_account.Credentials.from_service_account_info(
            secrets_dict,
            scopes=["https://www.googleapis.com/auth/gmail.modify"]
        )
        delegated_creds = creds.with_subject(secrets_dict["gmail_user"])
        return delegated_creds
    except Exception as e:
        raise RuntimeError("Gmail login failed: " + str(e))

# --- Send Email ---
def send_email(creds, to, subject, message_text, campaign=None):
    try:
        service = build("gmail", "v1", credentials=creds)
        message = MIMEText(message_text, "html")
        message["to"] = to
        message["subject"] = subject
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
        body = {"raw": raw}

        sent_log = load_campaign_log(campaign)
        if any(entry[0] == to for entry in sent_log):
            return {"status": "duplicate", "message": "Already sent to this email."}

        service.users().messages().send(userId="me", body=body).execute()
        log_campaign_email(campaign, to, "success")
        return {"status": "success"}

    except Exception as e:
        log_campaign_email(campaign, to, str(e))
        return {"error": str(e)}

# --- Send Follow-Up (after delay) ---
def send_follow_up(creds, to, subject, message_text, delay_minutes=10):
    time.sleep(delay_minutes * 60)
    follow_up_subject = f"Re: {subject}"
    follow_up_text = f"Just following up on my previous message:\n\n{message_text}"
    send_email(creds, to, follow_up_subject, follow_up_text)

# --- Campaign Logging ---
def log_campaign_email(campaign, email, status):
    log_path = f"campaign_log_{campaign}.pkl"
    if os.path.exists(log_path):
        with open(log_path, "rb") as f:
            log = pickle.load(f)
    else:
        log = []
    log.append((email, status))
    with open(log_path, "wb") as f:
        pickle.dump(log, f)

def load_campaign_log(campaign):
    log_path = f"campaign_log_{campaign}.pkl"
    if os.path.exists(log_path):
        with open(log_path, "rb") as f:
            return pickle.load(f)
    return []

# --- Inbox Fetch: Replies ---
def fetch_replies(creds, thread_limit=20):
    try:
        service = build("gmail", "v1", credentials=creds)
        results = service.users().messages().list(userId="me", q="is:inbox", maxResults=thread_limit).execute()
        messages = results.get("messages", [])

        replies = []
        for msg in messages:
            full_msg = service.users().messages().get(userId="me", id=msg["id"], format="metadata", metadataHeaders=["From", "Subject"]).execute()
            snippet = full_msg.get("snippet", "")
            headers = full_msg.get("payload", {}).get("headers", [])
            sender = next((h["value"] for h in headers if h["name"] == "From"), "Unknown")
            replies.append({
                "id": msg["id"],
                "from": sender,
                "snippet": snippet,
            })
        return replies
    except Exception as e:
        print("Error fetching replies:", e)
        return []
