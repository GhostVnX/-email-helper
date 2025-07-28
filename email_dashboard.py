# email_dashboard.py
import streamlit as st
import pandas as pd
from connect_gmail import login_to_gmail, send_email
import time
import os

# Set up Streamlit page config
st.set_page_config(page_title="Email Helper Dashboard", layout="centered")

# Dashboard Auth
DASHBOARD_PASSWORD = "ghostvnx123"

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("🔒 Email Helper Login")
    password = st.text_input("Enter Dashboard Password", type="password")
    if password == DASHBOARD_PASSWORD:
        st.session_state.authenticated = True
        st.experimental_rerun()
    elif password:
        st.warning("Incorrect password.")
    st.stop()

# Navigation
st.sidebar.title("📍 Navigation")
nav = st.sidebar.radio("Go to", ["📤 Upload File", "🧠 Process Data", "✍️ Email Composer", "📊 Dashboard", "🔚 Logout"])

# Global session state for data
if "data" not in st.session_state:
    st.session_state.data = None
if "sent_log" not in st.session_state:
    st.session_state.sent_log = []

# Page 1: Upload File
if nav == "📤 Upload File":
    st.title("📤 Upload Your File")
    uploaded_file = st.file_uploader("Upload CSV or Excel", type=["csv", "xlsx"])
    if uploaded_file:
        try:
            if uploaded_file.name.endswith(".csv"):
                df = pd.read_csv(uploaded_file)
            else:
                df = pd.read_excel(uploaded_file)
            st.session_state.data = df
            st.success("✅ File uploaded and read successfully.")
            st.dataframe(df.head())
        except Exception as e:
            st.error(f"❌ Failed to process file: {e}")

# Page 2: Process Data
elif nav == "🧠 Process Data":
    st.title("🧠 Process & Filter Data")
    if st.session_state.data is not None:
        df = st.session_state.data.copy()

        prompt = st.text_area("Enter prompt for what to extract (e.g., valid emails, names):")
        if st.button("Run Prompt Filter"):
            if "Contact" in df.columns:
                df = df.dropna(subset=["Contact"])
                df = df[df["Contact"].str.contains("@")]
                st.session_state.data = df
                st.success(f"Filtered {len(df)} email entries.")
                st.dataframe(df)
            else:
                st.warning("Column `Contact` not found.")
    else:
        st.warning("Please upload a file first.")

# Page 3: Compose Email
elif nav == "✍️ Email Composer":
    st.header("✍️ Compose Email & Send")
    if st.session_state.data is not None:
        credentials = login_to_gmail()
        if credentials:
            message_template = st.text_area("Type your base message here", height=200)
            subject = st.text_input("Subject of Email")
            attachment = st.file_uploader("Optional: Upload attachment", type=None)

            limit = st.slider("Max emails to send this run", min_value=1, max_value=50, value=10)

            if st.button("🚀 Send Emails"):
                df = st.session_state.data
                df = df.dropna(subset=["Contact"])
                success, failed = 0, 0
                for idx, row in df.head(limit).iterrows():
                    try:
                        email = row["Contact"]
                        name = row["Name"] if "Name" in row else ""
                        personalized = message_template.replace("{name}", name)
                        send_email(credentials, email, subject, personalized)
                        st.session_state.sent_log.append({
                            "to": email,
                            "status": "Sent",
                            "timestamp": time.ctime()
                        })
                        success += 1
                        time.sleep(2)  # Avoid hitting Gmail API limits
                    except Exception as e:
                        st.session_state.sent_log.append({
                            "to": row.get("Contact", "N/A"),
                            "status": f"Failed: {e}",
                            "timestamp": time.ctime()
                        })
                        failed += 1
                st.success(f"✅ Emails sent: {success}, Failed: {failed}")
    else:
        st.warning("Please upload and filter your file first.")

# Page 4: Dashboard
elif nav == "📊 Dashboard":
    st.title("📊 Campaign Dashboard")
    if st.session_state.sent_log:
        st.write(f"📨 Total emails processed: {len(st.session_state.sent_log)}")
        st.dataframe(pd.DataFrame(st.session_state.sent_log))
    else:
        st.info("No emails sent yet. Once you send emails, logs will show here.")

# Page 5: Logout
elif nav == "🔚 Logout":
    st.session_state.authenticated = False
    st.experimental_rerun()
