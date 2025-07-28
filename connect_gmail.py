import streamlit as st
from google.oauth2 import service_account
from googleapiclient.discovery import build
from email.mime.text import MIMEText
import base64
import time
import json
import pickle
import os

# --- Gmail Auth ---
def login_to_gmail():
    try:
        secrets_dict = dict(st.secrets["gmail_service"])
        creds = service_account.Credentials.from_service_account_info(
            secrets_dict,
            scopes=["https://www.googleapis.com/auth/gmail.send", "https://www.googleapis.com/auth/gmail.readonly"]
        )
        delegated_creds = creds.with_subject(secrets_dict["gmail_user"])
        return delegated_creds
    except Exception as e:
        raise RuntimeError("Gmail login failed: " + str(e))


# --- Send Email ---
def send_email(creds, to, subject, message_text, campaign=None):
    try:
        service = build("gmail", "v1", credentials=creds)
        message = MIMEText(message_text, "plain")
        message["to"] = to
        message["subject"] = subject

        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
        body = {"raw": raw}

        # Check for duplicate if campaign log exists
        if campaign:
            log_path = f"log_{campaign}.csv"
            if os.path.exists(log_path):
                df = pd.read_csv(log_path)
                if to in df["email"].values:
                    return {"status": "duplicate", "message": "Already sent."}

        service.users().messages().send(userId="me", body=body).execute()

        return {"status": "success"}

    except Exception as e:
        return {"error": str(e)}


# --- Campaign Log ---
def load_campaign_log(campaign_name):
    log_path = f"log_{campaign_name}.csv"
    if os.path.exists(log_path):
        try:
            df = pd.read_csv(log_path)
            return df.values.tolist()
        except:
            return []
    return []


# --- Check Reply Status ---
def check_reply_status(creds, recipient_email):
    """
    Check Gmail inbox to see if the recipient replied.
    """
    try:
        service = build("gmail", "v1", credentials=creds)
        query = f"from:{recipient_email} in:inbox"
        result = service.users().messages().list(userId="me", q=query, maxResults=1).execute()
        messages = result.get("messages", [])
        return len(messages) > 0
    except Exception as e:
        print(f"Failed to check reply: {e}")
        return False
