import base64
import pickle
import os
from email.mime.text import MIMEText
from google.oauth2 import service_account
from googleapiclient.discovery import build
import time

SCOPES = ["https://www.googleapis.com/auth/gmail.send"]
TOKEN_FILE = "token.pickle"

def login_to_gmail():
    try:
        # Read credentials from Streamlit secrets
        credentials_info = {
            "type": st.secrets["gmail"]["type"],
            "project_id": st.secrets["gmail"]["project_id"],
            "private_key_id": st.secrets["gmail"]["private_key_id"],
            "private_key": st.secrets["gmail"]["private_key"].replace("\\n", "\n"),
            "client_email": st.secrets["gmail"]["client_email"],
            "client_id": st.secrets["gmail"]["client_id"],
            "auth_uri": st.secrets["gmail"]["auth_uri"],
            "token_uri": st.secrets["gmail"]["token_uri"],
            "auth_provider_x509_cert_url": st.secrets["gmail"]["auth_provider_x509_cert_url"],
            "client_x509_cert_url": st.secrets["gmail"]["client_x509_cert_url"],
        }

        creds = service_account.Credentials.from_service_account_info(
            credentials_info, scopes=SCOPES
        )
        return creds
    except Exception as e:
        raise RuntimeError("Gmail login failed: " + str(e))


def send_email(creds, to, subject, message_text):
    try:
        service = build("gmail", "v1", credentials=creds)
        message = MIMEText(message_text)
        message["to"] = to
        message["subject"] = subject
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        message_body = {"raw": raw_message}
        send_result = service.users().messages().send(userId="me", body=message_body).execute()
        return send_result
    except Exception as e:
        return {"error": str(e)}

def send_follow_up(creds, to, subject, message_text, delay_minutes=10):
    time.sleep(delay_minutes * 60)
    follow_up_message = f"Follow-up:\n\n{message_text}"
    send_email(creds, to, subject + " (Follow-up)", follow_up_message)

def load_sent_log():
    try:
        with open("sent_log.pickle", "rb") as f:
            return pickle.load(f)
    except:
        return {}

def save_sent_log(log):
    with open("sent_log.pickle", "wb") as f:
        pickle.dump(log, f)
