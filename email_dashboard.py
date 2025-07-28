# email_dashboard.py (Updated Version)
import streamlit as st
import pandas as pd
from connect_gmail import login_to_gmail, send_email
import time
import json
import base64

# --- Constants ---
DASHBOARD_PASSWORD = "GhostAccess123"

# --- Page Config ---
st.set_page_config(page_title="Email Helper", layout="wide")

# --- Initialize session state ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "data" not in st.session_state:
    st.session_state.data = None
if "filtered" not in st.session_state:
    st.session_state.filtered = None
if "results" not in st.session_state:
    st.session_state.results = []

# --- Login Page ---
st.title("🔐 Login to Email Helper")
if not st.session_state.authenticated:
    password = st.text_input("Enter Dashboard Password", type="password")
    if password.strip() == DASHBOARD_PASSWORD:
        st.session_state.authenticated = True
        st.rerun()  # ✅ updated from st.experimental_rerun()
    elif password:
        st.warning("Incorrect password. Please try again.")
    st.stop()

# --- Navigation Sidebar ---
nav = st.sidebar.radio("Navigation", ["📤 Upload File", "🧠 Filter Prompt", "✉️ Compose Email", "📊 Dashboard"])

# --- Upload Page ---
if nav == "📤 Upload File":
    st.header("📤 Upload CSV or Excel File")
    uploaded_file = st.file_uploader("Upload a CSV or Excel file", type=["csv", "xlsx"])
    if uploaded_file:
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
        st.session_state.data = df
        st.session_state.filtered = None
        st.success("✅ File uploaded successfully!")
        st.dataframe(df.head())

        st.subheader("🔎 Quick Stats")
        st.metric("Total Rows", df.shape[0])
        st.metric("Total Columns", df.shape[1])
        col_summary = {col: df[col].notna().sum() for col in df.columns}
        st.json(col_summary)

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
    df = st.session_state.filtered if st.session_state.filtered is not None else st.session_state.data
    if df is not None:
        credentials = login_to_gmail()
        if credentials:
            subject = st.text_input("Email Subject")
            message_template = st.text_area("Email Body (use {name} for personalization)")
            attachment = st.file_uploader("Upload Attachment (optional)", type=None)
            send = st.button("🚀 Send Emails")

            if send:
                st.session_state.results.clear()
                for _, row in df.iterrows():
                    email = row.get("email") or row.get("Email")
                    name = row.get("name") or row.get("Name", "")
                    if email:
                        personalized = message_template.replace("{name}", name)
                        try:
                            send_email(credentials, email, subject, personalized)
                            st.session_state.results.append({"email": email, "status": "Sent"})
                        except Exception as e:
                            st.session_state.results.append({"email": email, "status": f"Failed: {str(e)}"})
                        time.sleep(1)
                st.success("✅ Email batch completed.")
    else:
        st.warning("Please upload and filter data first.")

# --- Dashboard Page ---
elif nav == "📊 Dashboard":
    st.header("📊 Campaign Dashboard")
    if st.session_state.data is not None:
        st.subheader("📋 Overview")
        st.metric("Total Contacts", len(st.session_state.data))

        if st.session_state.results:
            results_df = pd.DataFrame(st.session_state.results)
            st.subheader("📬 Email Results")
            st.dataframe(results_df)
        else:
            st.info("No email activity yet.")
    else:
        st.warning("Upload data to view dashboard.")
