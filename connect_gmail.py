import os
import json
import pickle
import streamlit as st
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from email.mime.text import MIMEText
import base64

SCOPES = ["https://www.googleapis.com/auth/gmail.send"]

def login_to_gmail():
    creds = None

    # Load credentials if token exists
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)

    # If no valid credentials, request login
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = Flow.from_client_config(
                json.loads(st.secrets["GOOGLE_CLIENT_SECRET"]),
                scopes=SCOPES,
                redirect_uri="https://ghostvnx-email-helper.streamlit.app/"
            )

            auth_url, _ = flow.authorization_url(prompt='consent')
            st.markdown(f"### 🔐 [Click here to login with Google]({auth_url})")
            auth_code = st.text_input("Paste the authorization code here:")

            if auth_code:
                try:
                    flow.fetch_token(code=auth_code)
                    creds = flow.credentials
                    # Save credentials
                    with open("token.json", "w") as token_file:
                        token_file.write(creds.to_json())
                    st.success("✅ Gmail authenticated successfully!")
                except Exception as e:
                    st.error(f"❌ Failed to authenticate: {e}")
                st.stop()
            else:
                st.stop()

    return creds

def send_email(creds, to, subject, body):
    from googleapiclient.discovery import build
    service = build("gmail", "v1", credentials=creds)

    message = MIMEText(body)
    message["to"] = to
    message["subject"] = subject

    raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
    message_body = {"raw": raw_message}

    try:
        send_result = service.users().messages().send(userId="me", body=message_body).execute()
        return send_result
    except Exception as e:
        raise e
