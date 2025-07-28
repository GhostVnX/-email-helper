# email_dashboard.py (Enhanced Version with Follow-up & Tracking)
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from connect_gmail import login_to_gmail, send_email
import time
import json
import base64
from datetime import datetime, timedelta

# --- Constants ---
DASHBOARD_PASSWORD = "GhostAccess123"
FOLLOW_UP_DELAY = 600  # 10 minutes in seconds

# --- Page Config ---
st.set_page_config(page_title="Email Helper AI Dashboard", layout="wide")

# --- Initialize session state ---
def init_state():
    defaults = {
        "authenticated": False,
        "data": None,
        "filtered": None,
        "results": [],
        "sent_log": {},
        "followups": []
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_state()

# --- Login Page ---
st.title("🔐 Login to Email Helper")
if not st.session_state.authenticated:
    password = st.text_input("Enter Dashboard Password", type="password")
    if password.strip() == DASHBOARD_PASSWORD:
        st.session_state.authenticated = True
        st.rerun()
    elif password:
        st.warning("Incorrect password. Please try again.")
    st.stop()

# --- Navigation Sidebar ---
nav = st.sidebar.radio("Navigation", ["📤 Upload File", "🧠 Filter Prompt", "✉️ Compose Email", "📬 Follow-up Manager", "📊 Dashboard"])

# --- Upload Page ---
if nav == "📤 Upload File":
    st.header("📤 Upload CSV or Excel File")
    uploaded_file = st.file_uploader("Upload a CSV or Excel file", type=["csv", "xlsx"])
    if uploaded_file:
        df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith(".csv") else pd.read_excel(uploaded_file)
        st.session_state.data = df
        st.session_state.filtered = None
        st.success("✅ File uploaded successfully!")
        st.dataframe(df.head())

        st.subheader("📊 Quick File Overview")
        st.metric("Total Rows", df.shape[0])
        st.metric("Total Columns", df.shape[1])

        col_summary = {col: df[col].notna().sum() for col in df.columns}
        st.json(col_summary)

        fig, ax = plt.subplots()
        ax.bar(col_summary.keys(), col_summary.values())
        ax.set_title("📈 Non-Empty Values per Column")
        ax.tick_params(axis='x', rotation=45)
        st.pyplot(fig)

# --- Filter Prompt Page ---
elif nav == "🧠 Filter Prompt":
    st.header("🧠 Smart Filter Prompt")
    if st.session_state.data is not None:
        prompt = st.text_area("Describe what you want to filter (e.g. 'emails with @gmail')")
        if st.button("Apply Filter"):
            df = st.session_state.data
            filtered = df[df.apply(lambda row: prompt.lower() in str(row).lower(), axis=1)]
            st.session_state.filtered = filtered
            st.success("✅ Filter applied")
            st.dataframe(filtered.head())

            st.subheader("📈 Filtered Data Overview")
            st.metric("Filtered Rows", filtered.shape[0])
            st.metric("Filtered Columns", filtered.shape[1])
        elif st.session_state.filtered is not None:
            st.dataframe(st.session_state.filtered.head())
    else:
        st.warning("Please upload a file first.")

# --- Email Composer Page ---
elif nav == "✉️ Compose Email":
    st.header("✉️ Compose & Send Emails")
    df = st.session_state.filtered or st.session_state.data
    if df is not None:
        credentials = login_to_gmail()
        if credentials:
            subject = st.text_input("Email Subject")
            message_template = st.text_area("Email Body (use {name} for personalization)")
            attachment = st.file_uploader("Upload Attachment (optional)", type=None)
            send = st.button("🚀 Send Emails")

            if send:
                st.session_state.results.clear()
                now = datetime.utcnow()
                for _, row in df.iterrows():
                    email = row.get("email") or row.get("Email")
                    name = row.get("name") or row.get("Name", "")
                    if email and email not in st.session_state.sent_log:
                        personalized = message_template.replace("{name}", name)
                        try:
                            send_email(credentials, email, subject, personalized)
                            st.session_state.results.append({"email": email, "status": "Sent"})
                            st.session_state.sent_log[email] = now
                            st.session_state.followups.append({
                                "email": email,
                                "name": name,
                                "subject": f"Follow-up: {subject}",
                                "body": f"Hi {name}, just checking in regarding our previous message.",
                                "send_after": now + timedelta(seconds=FOLLOW_UP_DELAY)
                            })
                        except Exception as e:
                            st.session_state.results.append({"email": email, "status": f"Failed: {str(e)}"})
                        time.sleep(1)
                st.success("✅ Email batch completed.")
    else:
        st.warning("Please upload and filter data first.")

# --- Follow-up Manager ---
elif nav == "📬 Follow-up Manager":
    st.header("📬 Follow-Up Email Scheduler")
    credentials = login_to_gmail()
    if credentials:
        now = datetime.utcnow()
        to_send = [f for f in st.session_state.followups if f["send_after"] <= now]
        st.metric("Ready to Follow-Up", len(to_send))

        for task in to_send:
            try:
                send_email(credentials, task["email"], task["subject"], task["body"])
                st.success(f"📨 Follow-up sent to {task['email']}")
            except Exception as e:
                st.error(f"❌ Failed to send follow-up to {task['email']}: {e}")

        # Remove sent ones
        st.session_state.followups = [f for f in st.session_state.followups if f["send_after"] > now]
    else:
        st.warning("Login to Gmail first.")

# --- Dashboard Page ---
elif nav == "📊 Dashboard":
    st.header("📊 Campaign Dashboard")
    if st.session_state.data is not None:
        st.subheader("📋 Data Overview")
        st.metric("Total Contacts", len(st.session_state.data))

        if st.session_state.results:
            results_df = pd.DataFrame(st.session_state.results)
            sent_count = results_df[results_df["status"] == "Sent"].shape[0]
            failed_count = results_df.shape[0] - sent_count
            st.metric("✅ Sent Emails", sent_count)
            st.metric("❌ Failed Emails", failed_count)

            st.subheader("📬 Email Status Table")
            st.dataframe(results_df)

            fig, ax = plt.subplots()
            results_df["status"].value_counts().plot(kind='bar', ax=ax)
            ax.set_title("📊 Email Sending Results")
            st.pyplot(fig)

            st.subheader("📁 Sent Log")
            st.json(st.session_state.sent_log)
        else:
            st.info("No email activity yet.")
    else:
        st.warning("Upload data to view dashboard.")
