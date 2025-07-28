# dashboard.py (Includes Reply Detection + Campaign Reports Setup)

import streamlit as st
import pandas as pd
import os
from connect_gmail import login_to_gmail, send_email, load_campaign_log, check_reply_status
from campaign_utils import split_batches, load_campaign_data, save_campaign_data
from datetime import datetime, timedelta
import threading
import matplotlib.pyplot as plt
import time

st.set_page_config(page_title="📧 GhostBot Dashboard", layout="wide", initial_sidebar_state="expanded")

# --- Dark Theme & CSS ---
st.markdown("""
    <style>
        .stApp { background-color: #111827; color: #e5e7eb; }
        h1, h2, h3, h4 { color: #93c5fd; }
        .sidebar .sidebar-content { background-color: #1f2937; }
        .stButton>button { background-color: #2563eb; color: white; font-weight: bold; }
        .stMetric-value { color: #60a5fa !important; }
        .sticky-box { position: sticky; top: 0; background: #1f2937; padding: 1em; margin-bottom: 1em; border: 1px solid #374151; border-radius: 8px; }
    </style>
""", unsafe_allow_html=True)

# --- Auth ---
DASHBOARD_PASSWORD = "GhostAccess123"
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if not st.session_state.authenticated:
    st.title("🔐 GhostBot Login")
    password = st.text_input("Enter password", type="password")
    if password == DASHBOARD_PASSWORD:
        st.session_state.authenticated = True
        st.rerun()
    elif password:
        st.warning("Incorrect password")
    st.stop()

# --- Navigation ---
st.sidebar.title("👻 GhostBot Navigation")
page = st.sidebar.radio("📍 Choose a section", ["📤 Upload Contacts", "🧠 Preview & Personalize", "✉️ Send Emails", "📈 Campaign Tracker"])

if "campaigns" not in st.session_state:
    st.session_state.campaigns = {}

FOLLOW_UP_DELAY_DAYS = 3

REPLY_PROMPTS = {
    "Formal": "Thank you for your time. I'm following up on our previous message.",
    "Gen Z": "Hey hey! Just circling back on this 😎",
    "Hype": "🔥 Big opportunity alert – let’s not miss it!",
    "Chill": "Hey – wanted to check in casually. No pressure."
}

if page == "🧠 Preview & Personalize":
    st.header("🧠 Compose and Preview Emails")
    tone = st.radio("Select Tone Style", list(REPLY_PROMPTS.keys()), horizontal=True)
    if tone:
        st.code(REPLY_PROMPTS[tone], language="text")
    st.markdown("---")

# --- Daily Batching Trigger ---
def auto_batch_send(campaign_name, df, subject, body, creds):
    log = load_campaign_log(campaign_name)
    already_sent = set([entry[0] for entry in log])
    failed_emails = set()
    failed_path = f"failed_{campaign_name}.csv"

    if os.path.exists(failed_path):
        failed_emails.update(pd.read_csv(failed_path)['email'].tolist())

    global_sent = set()
    for all_logs in os.listdir():
        if all_logs.startswith("log_") and all_logs.endswith(".csv"):
            try:
                sent_log_df = pd.read_csv(all_logs)
                global_sent.update(sent_log_df['email'].dropna().tolist())
            except:
                pass

    to_send = df[~df['email'].isin(already_sent) & ~df['email'].isin(failed_emails) & ~df['email'].isin(global_sent)]
    batch = to_send.head(100)

    new_log = []
    for _, row in batch.iterrows():
        email = row.get("email")
        name = row.get("name", "there")
        body_personalized = body.replace("{name}", name)
        result = send_email(creds, email, subject, body_personalized, campaign_name)

        timestamp = datetime.now().isoformat()
        if result.get("status") == "success":
            new_log.append((email, "sent", timestamp))
        elif "error" in result:
            error_df = pd.DataFrame([[email, result['error'], timestamp]], columns=["email", "error", "timestamp"])
            if os.path.exists(failed_path):
                prev = pd.read_csv(failed_path)
                pd.concat([prev, error_df]).drop_duplicates('email').to_csv(failed_path, index=False)
            else:
                error_df.to_csv(failed_path, index=False)

        time.sleep(1)

    if new_log:
        prev_log = log + new_log
        with open(f"log_{campaign_name}.csv", "w") as f:
            pd.DataFrame(prev_log, columns=["email", "status", "timestamp"]).to_csv(f, index=False)

# ✅ Follow-Up Handler

def schedule_follow_up_if_needed(campaign_name, creds, tone="Formal"):
    df = load_campaign_data(campaign_name)
    log = load_campaign_log(campaign_name)
    sent_map = {row[0]: row[2] for row in log if row[1] == "sent"}  # email: timestamp

    today = datetime.now()
    for email, sent_date in sent_map.items():
        sent_time = datetime.fromisoformat(sent_date)
        if (today - sent_time).days >= FOLLOW_UP_DELAY_DAYS:
            if not check_reply_status(creds, email):
                follow_up_msg = REPLY_PROMPTS.get(tone, REPLY_PROMPTS["Formal"])
                subject = f"Just Checking In"
                send_email(creds, email, subject, follow_up_msg, campaign_name)
                time.sleep(1)
