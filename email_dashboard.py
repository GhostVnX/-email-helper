# dashboard.py (Enhanced UI with Upload, Composer, Attachment, Prompt, and Personalization)

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

# --- Upload Contacts ---
if page == "📤 Upload Contacts":
    st.header("📤 Upload Contact File")
    uploaded_file = st.file_uploader("Upload CSV or Excel file", type=["csv", "xlsx"])
    campaign_name = st.text_input("Enter Campaign Name")
    if uploaded_file and campaign_name:
        df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith(".csv") else pd.read_excel(uploaded_file)
        df.columns = [c.lower().strip() for c in df.columns]
        if "email" not in df.columns:
            st.error("No 'email' column found.")
        else:
            st.session_state.campaigns[campaign_name] = df
            save_campaign_data(campaign_name, df)
            st.success(f"Campaign '{campaign_name}' uploaded successfully!")
            st.dataframe(df.head())

# --- Composer and Preview ---
elif page == "🧠 Preview & Personalize":
    st.header("🧠 Compose Email Template")
    if not st.session_state.campaigns:
        st.info("Upload a campaign first")
    else:
        campaign = st.selectbox("Select Campaign", list(st.session_state.campaigns))
        tone = st.radio("Prompt Tone", list(REPLY_PROMPTS.keys()), horizontal=True)
        prompt_text = st.text_area("Custom Prompt or Message", value=REPLY_PROMPTS[tone])
        attachment = st.file_uploader("Attach Image or File (optional)")

        df = st.session_state.campaigns[campaign].copy()
        df["preview"] = df.apply(lambda row: prompt_text.replace("{name}", row.get("name", "friend")), axis=1)
        st.subheader("📩 Preview Messages")
        st.dataframe(df[["email", "preview"]])

# --- Send Emails ---
elif page == "✉️ Send Emails":
    st.header("✉️ Send Emails")
    if not st.session_state.campaigns:
        st.warning("No campaigns loaded.")
    else:
        campaign = st.selectbox("Select Campaign", list(st.session_state.campaigns))
        creds = login_to_gmail()
        subject = st.text_input("Email Subject")
        message_body = st.text_area("Email Body (HTML/Plain text)")
        attachment = st.file_uploader("Attach File (optional)")
        send_btn = st.button("🚀 Send Now")

        if send_btn:
            df = st.session_state.campaigns[campaign]
            for _, row in df.iterrows():
                email = row.get("email")
                name = row.get("name", "friend")
                body = message_body.replace("{name}", name)
                result = send_email(creds, email, subject, body, campaign)
                st.write(f"{email} → {result.get('status')}")
            st.success("All emails processed.")

# --- Campaign Tracker ---
elif page == "📈 Campaign Tracker":
    st.header("📊 Campaign Overview")
    for campaign in st.session_state.campaigns:
        df = st.session_state.campaigns[campaign]
        log = load_campaign_log(campaign)
        sent_emails = set([entry[0] for entry in log])
        st.subheader(f"📦 {campaign}")
        st.metric("Total Contacts", len(df))
        st.metric("Sent", len(sent_emails))
        st.metric("Pending", len(df) - len(sent_emails))
        st.progress(len(sent_emails) / max(1, len(df)))
