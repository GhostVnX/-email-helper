# Phase 2, 2.1, 2.2 Streamlit App — Full Functional Code
# Author: Ghost VnX x GPT

import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta
from connect_gmail import login_to_gmail, send_email

st.set_page_config(page_title="Email Helper", layout="wide")

# === App State ===
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'uploaded_file' not in st.session_state:
    st.session_state.uploaded_file = None
if 'data' not in st.session_state:
    st.session_state.data = None
if 'prompt' not in st.session_state:
    st.session_state.prompt = ""
if 'custom_message' not in st.session_state:
    st.session_state.custom_message = ""
if 'email_sent_log' not in st.session_state:
    st.session_state.email_sent_log = []

# === Login Section ===
st.title("📧 Email Helper by Ghost VnX")
DASHBOARD_PASSWORD = "GhostAccess123"

if not st.session_state.authenticated:
    password = st.text_input("Enter Dashboard Password", type="password")
    if password and password == DASHBOARD_PASSWORD:
        st.session_state.authenticated = True
        st.experimental_rerun()
    elif password:
        st.warning("Incorrect password. Please try again.")
    st.stop()

# === Sidebar ===
st.sidebar.title("📂 Navigation")
nav = st.sidebar.radio("Go to:", ["Upload File", "Prompt File Analysis", "Email Composer", "Dashboard"])

# === Upload Page ===
if nav == "Upload File":
    st.header("📁 Upload Your Contact File")
    uploaded = st.file_uploader("Upload .csv, .xlsx, or .txt file", type=["csv", "xlsx", "txt"])
    if uploaded:
        if uploaded.name.endswith("csv"):
            df = pd.read_csv(uploaded)
        elif uploaded.name.endswith("xlsx"):
            df = pd.read_excel(uploaded)
        elif uploaded.name.endswith("txt"):
            df = pd.read_csv(uploaded, delimiter="\t")
        else:
            st.error("Unsupported file format")
            st.stop()

        st.session_state.uploaded_file = uploaded
        st.session_state.data = df
        st.success("✅ File uploaded and previewed below")
        st.dataframe(df.head())

# === Prompt Page ===
elif nav == "Prompt File Analysis":
    st.header("🔎 Prompt-Based File Filter")
    if st.session_state.data is not None:
        prompt = st.text_area("Enter your filter prompt (e.g. 'Find hip hop curators in UK')")
        if st.button("Apply Prompt"):
            # Simulated: real AI filtering logic to come
            st.session_state.prompt = prompt
            st.info(f"Prompt applied: {prompt}")
            st.dataframe(st.session_state.data.head())
    else:
        st.warning("Please upload a file first")

# === Composer Page ===
elif nav == "Email Composer":
    st.header("✍️ Compose Email & Send")
    if st.session_state.data is not None:
        credentials = login_to_gmail()
        if credentials:
            message_template = st.text_area("Type your base message here. Use [Name] and [Platform] for personalization.", height=150)
            attachment = st.file_uploader("Optional: Upload attachment to include in email")
            send_button = st.button("Send Emails")

            if send_button:
                sent_log = []
                for index, row in st.session_state.data.iterrows():
                    to = row.get("Contact") or row.get("Email")
                    if pd.isna(to):
                        continue
                    name = row.get("Title", "")
                    platform = row.get("Platform", "")
                    message = message_template.replace("[Name]", name).replace("[Platform]", platform)

                    try:
                        send_result = send_email(credentials, to, "Ghost VnX Submission", message)
                        sent_log.append({"to": to, "status": "Sent", "timestamp": datetime.now().isoformat()})
                    except Exception as e:
                        sent_log.append({"to": to, "status": f"Error: {e}", "timestamp": datetime.now().isoformat()})

                st.session_state.email_sent_log.extend(sent_log)
                st.success("✅ Emails sent (or attempted). Check dashboard tab.")
        else:
            st.warning("Gmail login required.")
    else:
        st.warning("Please upload and analyze file first")

# === Dashboard Page ===
elif nav == "Dashboard":
    st.header("📊 Campaign Dashboard")
    if st.session_state.email_sent_log:
        df_log = pd.DataFrame(st.session_state.email_sent_log)
        st.metric("Emails Sent", len(df_log[df_log['status'] == 'Sent']))
        st.metric("Errors", len(df_log[df_log['status'].str.contains('Error')]))
        st.dataframe(df_log.tail(20))
        st.download_button("Download Full Log", df_log.to_csv(index=False), file_name="email_log.csv")
    else:
        st.info("No email activity logged yet.")
