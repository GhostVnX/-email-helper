# email_dashboard.py
import streamlit as st
import pandas as pd
from connect_gmail import login_to_gmail, send_email
import time
import io

st.set_page_config(page_title="Email Helper", layout="wide")

# --- Auth ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

DASHBOARD_PASSWORD = "ghostvnx"

if not st.session_state.authenticated:
    st.title("🔒 Email Helper Login")
    password = st.text_input("Enter Dashboard Password", type="password")
    if password and password == DASHBOARD_PASSWORD:
        st.session_state.authenticated = True
        st.rerun()
    elif password:
        st.warning("Incorrect password. Please try again.")
    st.stop()

# --- Navigation ---
nav = st.sidebar.radio("Navigate", ["📤 Upload File", "🧠 Prompt Filter", "✍️ Email Composer", "📊 Dashboard"])

# --- Upload Page ---
if nav == "📤 Upload File":
    st.header("📤 Upload Your Data File")
    uploaded_file = st.file_uploader("Choose a CSV or Excel file", type=["csv", "xlsx"])
    if uploaded_file:
        try:
            if uploaded_file.name.endswith(".csv"):
                df = pd.read_csv(uploaded_file)
            else:
                df = pd.read_excel(uploaded_file)
            st.session_state.data = df
            st.success("✅ File loaded successfully!")
            st.dataframe(df)
        except Exception as e:
            st.error(f"Error loading file: {e}")

# --- Prompt Filter Page ---
elif nav == "🧠 Prompt Filter":
    st.header("🧠 Smart Prompt Filter")
    if "data" in st.session_state:
        prompt = st.text_area("Describe what you want to extract (e.g., 'Emails and Instagram handles')")
        if st.button("Run Prompt"):
            df = st.session_state.data
            extracted_cols = []
            if "email" in prompt.lower():
                for col in df.columns:
                    if df[col].astype(str).str.contains("@", na=False).any():
                        extracted_cols.append(col)
            if extracted_cols:
                result_df = df[extracted_cols].dropna()
                st.session_state.filtered = result_df
                st.success("Filtered results:")
                st.dataframe(result_df)
            else:
                st.warning("No matching data found based on prompt.")
    else:
        st.warning("Please upload a file first.")

# --- Email Composer Page ---
elif nav == "✍️ Email Composer":
    st.header("✍️ Compose Email & Send")
    if "filtered" in st.session_state:
        credentials = login_to_gmail()
        if credentials:
            message_template = st.text_area("Type your base message here (use {name} if you want to personalize)")
            subject = st.text_input("Subject of Email")
            attachment = st.file_uploader("Optional: Upload attachment (PDF, image, etc.)")
            send_button = st.button("🚀 Send Emails")

            if send_button:
                df = st.session_state.filtered
                for index, row in df.iterrows():
                    name = row.get("Name", "")
                    email = row.get("Email") or row.get("email")
                    if email:
                        personalized_msg = message_template.replace("{name}", name)
                        try:
                            send_email(credentials, email, subject, personalized_msg)
                            st.success(f"✅ Sent to {email}")
                        except Exception as e:
                            st.error(f"❌ Failed to send to {email}: {e}")
                        time.sleep(1)
        else:
            st.error("Gmail login failed.")
    else:
        st.warning("Please run a filter prompt first.")

# --- Dashboard Page ---
elif nav == "📊 Dashboard":
    st.header("📊 Campaign Dashboard")
    if "filtered" in st.session_state:
        df = st.session_state.filtered
        total = len(df)
        st.metric("Total Contacts", total)
        if "Email" in df.columns or "email" in df.columns:
            emails = df["Email"] if "Email" in df.columns else df["email"]
            st.metric("Emails Found", emails.count())
        st.dataframe(df)
    else:
        st.info("Upload and filter data to see the dashboard.")
