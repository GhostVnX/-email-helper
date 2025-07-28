# email_dashboard.py (Enhanced)
import streamlit as st
import pandas as pd
from connect_gmail import login_to_gmail, send_email, send_follow_up
import time
import io
import matplotlib.pyplot as plt

st.set_page_config(page_title="Email Helper Dashboard", layout="wide")

# --- Auth ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

DASHBOARD_PASSWORD = "GhostAccess123"

if not st.session_state.authenticated:
    st.title("🔒 Email Helper Login")
    password = st.text_input("Enter Dashboard Password", type="password")
    if password.strip() == DASHBOARD_PASSWORD:
        st.session_state.authenticated = True
        st.rerun()
    elif password:
        st.warning("Incorrect password. Please try again.")
    st.stop()

# --- Session State Defaults ---
if "data" not in st.session_state:
    st.session_state.data = None
if "filtered" not in st.session_state:
    st.session_state.filtered = None

# --- Navigation ---
st.sidebar.title("📍 Navigation")
nav = st.sidebar.radio("Go to", ["📤 Upload File", "🧠 Prompt File Analysis", "✉️ Email Composer", "📊 Campaign Dashboard"])

# --- Upload File ---
if nav == "📤 Upload File":
    st.header("📤 Upload Your Contact File")
    uploaded_file = st.file_uploader("Upload a CSV or Excel file", type=["csv", "xlsx"])
    if uploaded_file:
        try:
            if uploaded_file.name.endswith(".csv"):
                df = pd.read_csv(uploaded_file)
            else:
                df = pd.read_excel(uploaded_file)
            st.session_state.data = df
            st.success("✅ File uploaded successfully")

            # Preview and Summary
            st.subheader("📌 File Summary")
            st.dataframe(df.head())
            st.write(f"**Rows:** {df.shape[0]}, **Columns:** {df.shape[1]}")
            st.bar_chart(df.notna().sum())
        except Exception as e:
            st.error(f"Error loading file: {e}")

# --- Prompt Page ---
elif nav == "🧠 Prompt File Analysis":
    st.header("🔎 Prompt-Based File Filter")
    if st.session_state.data is not None:
        prompt = st.text_area("Enter your filter prompt (e.g. 'Find high engagement emails')")
        if st.button("Apply Prompt"):
            df = st.session_state.data
            extracted = df.copy()

            # Auto-detect email columns for demo purposes
            email_cols = [col for col in df.columns if "email" in col.lower()]
            if email_cols:
                extracted = df[email_cols + [col for col in df.columns if "name" in col.lower() or "handle" in col.lower()]]
                st.session_state.filtered = extracted.dropna()
                st.success("✅ Data filtered with prompt")

                # Visual Summary
                st.subheader("📊 Filtered Data Overview")
                st.metric("Contacts Found", len(st.session_state.filtered))
                st.dataframe(st.session_state.filtered.head())
            else:
                st.warning("No email-like column detected.")
    else:
        st.info("📁 Please upload data file first.")

# --- Email Composer ---
elif nav == "✉️ Email Composer":
    st.header("✉️ Compose & Send Emails")
    df = st.session_state.filtered if st.session_state.filtered is not None else None
    if df is not None:
        credentials = login_to_gmail()
        if credentials:
            subject = st.text_input("Email Subject")
            message_template = st.text_area("Email Body (use {name} for personalization)")
            follow_up_toggle = st.checkbox("Send follow-up email after 10 minutes if no reply")
            send_btn = st.button("🚀 Send Emails")

            if send_btn:
                for i, row in df.iterrows():
                    name = row.get("Name", "")
                    email = row.get("Email") or row.get("email")
                    if email:
                        message = message_template.replace("{name}", name)
                        result = send_email(credentials, email, subject, message)
                        if isinstance(result, dict) and result.get("status") == "duplicate":
                            st.warning(f"⚠️ {result['message']}")
                        elif "error" in result:
                            st.error(f"❌ Failed to send to {email}: {result['error']}")
                        else:
                            st.success(f"✅ Sent to {email}")

                            if follow_up_toggle:
                                # Trigger follow-up email in background thread
                                import threading
                                threading.Thread(target=send_follow_up, args=(credentials, email, subject, message, 10)).start()
                        time.sleep(1)
        else:
            st.error("Gmail authentication failed.")
    else:
        st.info("📌 Please filter data before sending.")

# --- Dashboard ---
elif nav == "📊 Campaign Dashboard":
    st.header("📊 Campaign Overview")
    if st.session_state.filtered is not None:
        df = st.session_state.filtered
        st.metric("Total Contacts", len(df))
        emails_sent = 0
        from connect_gmail import load_sent_log
        sent_log = load_sent_log()
        for contact in df["Email"] if "Email" in df.columns else df["email"]:
            if contact in sent_log:
                emails_sent += 1
        st.metric("Emails Sent", emails_sent)
        st.metric("Pending Emails", len(df) - emails_sent)
        st.dataframe(df)

        st.subheader("📁 Sent Log")
        st.json(sent_log)
    else:
        st.info("📌 Upload and process data to track campaigns.")
