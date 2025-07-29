# dashboard.py (Enhanced UI with Upload, Composer, Attachment, Prompt, and Personalization)

import streamlit as st
import pandas as pd
import os
from connect_gmail import login_to_gmail, send_email, load_campaign_log
from campaign_utils import split_batches, load_campaign_data, save_campaign_data
from datetime import datetime, timedelta
import threading
import matplotlib.pyplot as plt
import time

st.set_page_config(page_title="📧 GhostBot Dashboard", layout="wide", initial_sidebar_state="expanded")

# --- Custom UI Style (Dark Mode + Card Layout) ---
st.markdown("""
    <style>
        body {
            background-color: #0f1117;
            color: white;
        }
        .reportview-container .main .block-container {
            padding: 2rem;
            background-color: #1c1e26;
        }
        .sticky-box {
            background: #2a2d3e;
            padding: 1rem;
            border-radius: 10px;
            margin-bottom: 1rem;
            border-left: 4px solid #4ade80;
        }
        .metric-label {
            color: #cbd5e1;
            font-size: 0.8rem;
        }
        .stButton>button {
            background-color: #4ade80;
            color: #111827;
            border-radius: 0.5rem;
            font-weight: bold;
        }
        .stDownloadButton>button {
            background-color: #60a5fa;
            color: white;
            font-weight: 600;
        }
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

    if uploaded_file:
        try:
            df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith(".csv") else pd.read_excel(uploaded_file)
            df.columns = [c.lower().strip() for c in df.columns]
            email_columns = [col for col in df.columns if "email" in col]

            if not email_columns:
                st.error("No email column detected in your file. Please include one (like 'Email' or 'email address').")
            else:
                if not campaign_name:
                    st.info("Please enter a campaign name to proceed.")
                else:
                    df.rename(columns={email_columns[0]: "email"}, inplace=True)
                    df = df.dropna(subset=["email"])
                    st.session_state.campaigns[campaign_name] = df
                    save_campaign_data(campaign_name, df)
                    st.success(f"Campaign '{campaign_name}' uploaded successfully!")
                    st.dataframe(df.head())
        except Exception as e:
            st.error(f"Error reading file: {e}")
    elif campaign_name:
        st.info("Waiting for you to upload a file.")

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

# --- Campaign Tracker + Analytics ---
elif page == "📈 Campaign Tracker":
    st.header("📊 Campaign Overview")
    for campaign in st.session_state.campaigns:
        df = st.session_state.campaigns[campaign]
        log = load_campaign_log(campaign)
        sent_emails = set([entry[0] for entry in log])
        failed_emails = [entry for entry in log if entry[1] != "success"]

        # Simulated engagement metrics with timestamps
        opened = int(len(sent_emails) * 0.75)
        clicked = int(opened * 0.4)
        replied = int(opened * 0.12)

        st.subheader(f"📦 {campaign}")
        st.metric("Total Contacts", len(df))
        st.metric("Sent", len(sent_emails))
        st.metric("Opened (simulated)", opened)
        st.metric("Clicked (simulated)", clicked)
        st.metric("Replied (simulated)", replied)
        st.metric("Failed", len(failed_emails))
        st.metric("Pending", len(df) - len(sent_emails))
        st.progress(len(sent_emails) / max(1, len(df)))

        # AI-style summary
        st.markdown(f"""
        <div class='sticky-box'>
        🧠 **Insight**: This campaign reached **{round((opened/len(df))*100)}%** of your contacts. Engagement was strong, with **{clicked}** clicks and **{replied}** replies. Great job!
        </div>
        """, unsafe_allow_html=True)

        # Timeline chart (simulated)
        timeline_df = pd.DataFrame({
            "Date": pd.date_range(end=datetime.today(), periods=7).strftime("%Y-%m-%d"),
            "Opens": [int(opened/7)]*7,
            "Clicks": [int(clicked/7)]*7,
            "Replies": [int(replied/7)]*7
        })
        st.subheader("📅 Engagement Timeline")
        st.line_chart(timeline_df.set_index("Date"))

        # Bar chart breakdown
        chart_data = pd.Series({"Sent": len(sent_emails), "Opened": opened, "Clicked": clicked, "Replied": replied, "Failed": len(failed_emails)})
        fig, ax = plt.subplots()
        chart_data.plot(kind="bar", color=["#60a5fa", "#4ade80", "#facc15", "#818cf8", "#ef4444"], ax=ax)
        ax.set_title("📊 Engagement Breakdown")
        st.pyplot(fig)

        # Real Inbox View (using Gmail API)
        from connect_gmail import login_to_gmail, fetch_replies
        creds = login_to_gmail()
        st.subheader("📨 View Real Inbox Replies")
        replies = fetch_replies(creds, thread_limit=20)
        if not replies:
            st.info("No replies found yet.")
        else:
            for reply in replies:
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.text_area(f"✉️ {reply['from']}", reply['snippet'], height=100)
                with col2:
                    tone = st.selectbox("Reply Style", ["Formal", "Gen Z", "Hype", "Chill"], key=f"tone_{reply['id']}")
                    st.button("Reply", key=f"reply_btn_{reply['id']}")

        with st.expander("📋 Failed Details"):
            for email, status in failed_emails:
                st.write(f"❌ {email}: {status}")

        with st.expander("⬇️ Export Reports"):
            st.download_button("Export Campaign Data", df.to_csv(index=False), file_name=f"{campaign}.csv")
            sent_df = df[df.email.isin(sent_emails)]
            st.download_button("Export Sent Emails", sent_df.to_csv(index=False), file_name=f"{campaign}_sent.csv")
            pdf_summary = f"Campaign Summary for {campaign}\nSent: {len(sent_emails)}\nOpened: {opened}\nReplied: {replied}"
            st.download_button("Export Summary PDF (mock)", pdf_summary, file_name=f"{campaign}_summary.pdf")
