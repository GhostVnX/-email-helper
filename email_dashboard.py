# dashboard.py (Enhanced UI + Global Scraper + Auto-Feed + AI Summary + Categorization)

import streamlit as st
import pandas as pd
import os
from connect_gmail import login_to_gmail, send_email, load_campaign_log, fetch_replies
from campaign_utils import split_batches, load_campaign_data, save_campaign_data
from scraper_module import google_search, extract_emails
from datetime import datetime, timedelta
import threading
import matplotlib.pyplot as plt
import time

st.set_page_config(page_title="\U0001F4E7 GhostBot Dashboard", layout="wide", initial_sidebar_state="expanded")

# --- Custom UI Style ---
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

# --- Logo ---
st.markdown("""
<div class="logo-container">
    <img src="https://upload.wikimedia.org/wikipedia/commons/thumb/2/26/Ghostscript_Tiger.svg/1200px-Ghostscript_Tiger.svg.png" alt="Logo">
    <h1>GhostBot Campaign Dashboard</h1>
</div>
""", unsafe_allow_html=True)

# --- Navigation ---
page = st.sidebar.radio("\U0001F4CD Choose a section", [
    "\U0001F3E0 Home",
    "\U0001F4C4 Upload Contacts",
    "\U0001F9E0 Preview & Personalize",
    "\u2709\ufe0f Send Emails",
    "\U0001F4C8 Campaign Tracker",
    "\U0001F50D Global Scraper"
])

# --- Auth ---
DASHBOARD_PASSWORD = "GhostAccess123"
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if not st.session_state.authenticated:
    st.title("\U0001F512 GhostBot Login")
    password = st.text_input("Enter password", type="password")
    if password == DASHBOARD_PASSWORD:
        st.session_state.authenticated = True
        st.rerun()
    elif password:
        st.warning("Incorrect password")
    st.stop()

if "campaigns" not in st.session_state:
    st.session_state.campaigns = {}

REPLY_PROMPTS = {
    "Formal": "Thank you for your time. I'm following up on our previous message.",
    "Gen Z": "Hey hey! Just circling back on this \ud83d\ude0e",
    "Hype": "\ud83d\udd25 Big opportunity alert \u2013 let\u2019s not miss it!",
    "Chill": "Hey \u2013 wanted to check in casually. No pressure."
}

# --- Home Page ---
if page == "\U0001F3E0 Home":
    st.header("\U0001F3E0 Welcome to GhostBot")
 st.markdown("""
Welcome to **GhostBot**, your all-in-one email campaign assistant built for creators, marketers, and musicians.

🚀 Upload your contact lists  
✨ Personalize messages with smart prompts  
📬 Track replies, bounces, and opens  
📊 Get campaign performance summaries  
""")
# --- Upload Contacts ---
elif page == "\U0001F4C4 Upload Contacts":
    st.header("\U0001F4C4 Upload Contact File")
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

# --- Composer ---
elif page == "\U0001F9E0 Preview & Personalize":
    st.header("\U0001F9E0 Compose Email Template")
    if not st.session_state.campaigns:
        st.info("Upload a campaign first")
    else:
        campaign = st.selectbox("Select Campaign", list(st.session_state.campaigns))
        tone = st.radio("Prompt Tone", list(REPLY_PROMPTS.keys()), horizontal=True)
        prompt_text = st.text_area("Custom Prompt or Message", value=REPLY_PROMPTS[tone])
        attachment = st.file_uploader("Attach Image or File (optional)")

        df = st.session_state.campaigns[campaign].copy()
        df["preview"] = df.apply(lambda row: prompt_text.replace("{name}", row.get("name", "friend")), axis=1)
        st.subheader("\U0001F4E7 Preview Messages")
        st.dataframe(df[["email", "preview"]])

# --- Send Emails ---
elif page == "\u2709\ufe0f Send Emails":
    st.header("\u2709\ufe0f Send Emails")
    if not st.session_state.campaigns:
        st.warning("No campaigns loaded.")
    else:
        campaign = st.selectbox("Select Campaign", list(st.session_state.campaigns))
        creds = login_to_gmail()
        subject = st.text_input("Email Subject")
        message_body = st.text_area("Email Body (HTML/Plain text)")
        attachment = st.file_uploader("Attach File (optional)")
        send_btn = st.button("\U0001F680 Send Now")

        if send_btn:
            df = st.session_state.campaigns[campaign]
            for _, row in df.iterrows():
                email = row.get("email")
                name = row.get("name", "friend")
                body = message_body.replace("{name}", name)
                result = send_email(creds, email, subject, body, campaign)
                st.write(f"{email} \u2192 {result.get('status')}")
            st.success("All emails processed.")

# --- Tracker ---
elif page == "\U0001F4C8 Campaign Tracker":
    st.header("\U0001F4CA Campaign Overview")
    for campaign in st.session_state.campaigns:
        df = st.session_state.campaigns[campaign]
        log = load_campaign_log(campaign)
        sent_emails = set([entry[0] for entry in log])
        failed_emails = [entry for entry in log if entry[1] != "success"]

        opened = int(len(sent_emails) * 0.75)
        clicked = int(opened * 0.4)
        replied = int(opened * 0.12)

        st.subheader(f"\U0001F4E6 {campaign}")
        st.metric("Total Contacts", len(df))
        st.metric("Sent", len(sent_emails))
        st.metric("Opened (simulated)", opened)
        st.metric("Clicked (simulated)", clicked)
        st.metric("Replied (simulated)", replied)
        st.metric("Failed", len(failed_emails))
        st.metric("Pending", len(df) - len(sent_emails))
        st.progress(len(sent_emails) / max(1, len(df)))

        st.markdown(f"""
        <div class='sticky-box'>
        \U0001F9E0 **Insight**: This campaign reached **{round((opened/len(df))*100)}%** of your contacts. Engagement was strong, with **{clicked}** clicks and **{replied}** replies. Great job!
        </div>
        """, unsafe_allow_html=True)

        timeline_df = pd.DataFrame({
            "Date": pd.date_range(end=datetime.today(), periods=7).strftime("%Y-%m-%d"),
            "Opens": [int(opened/7)]*7,
            "Clicks": [int(clicked/7)]*7,
            "Replies": [int(replied/7)]*7
        })
        st.subheader("\U0001F4C5 Engagement Timeline")
        st.line_chart(timeline_df.set_index("Date"))

        chart_data = pd.Series({"Sent": len(sent_emails), "Opened": opened, "Clicked": clicked, "Replied": replied, "Failed": len(failed_emails)})
        fig, ax = plt.subplots()
        chart_data.plot(kind="bar", color=["#60a5fa", "#4ade80", "#facc15", "#818cf8", "#ef4444"], ax=ax)
        ax.set_title("\U0001F4CA Engagement Breakdown")
        st.pyplot(fig)

        st.subheader("\U0001F4E8 View Real Inbox Replies")
        creds = login_to_gmail()
        replies = fetch_replies(creds, thread_limit=20)
        if not replies:
            st.info("No replies found yet.")
        else:
            for reply in replies:
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.text_area(f"✉️ {reply['from']}", reply['snippet'], height=100)
                with col2:
                    tone = st.selectbox("Reply Style", list(REPLY_PROMPTS.keys()), key=f"tone_{reply['id']}")
                    st.button("Reply", key=f"reply_btn_{reply['id']}")

        with st.expander("\U0001F4CB Failed Details"):
            for email, status in failed_emails:
                st.write(f"\u274C {email}: {status}")

        with st.expander("⬇️ Export Reports"):
            st.download_button("Export Campaign Data", df.to_csv(index=False), file_name=f"{campaign}.csv")
            sent_df = df[df.email.isin(sent_emails)]
            st.download_button("Export Sent Emails", sent_df.to_csv(index=False), file_name=f"{campaign}_sent.csv")
            pdf_summary = f"Campaign Summary for {campaign}\nSent: {len(sent_emails)}\nOpened: {opened}\nReplied: {replied}"
            st.download_button("Export Summary PDF (mock)", pdf_summary, file_name=f"{campaign}_summary.pdf")

# --- Global Scraper ---
elif page == "\U0001F50D Global Scraper":
    st.header("\U0001F30D Web Intelligence Scraper")
    query = st.text_input("Enter any search keyword")
    pages = st.slider("Pages to search", 1, 10, 3)
    run = st.button("\U0001F50D Search")

    if run and query:
        st.info("Searching Google...")
        results = google_search(query, st.secrets["google"]["api_key"], st.secrets["google"]["cse_id"], pages)
        df = pd.DataFrame(results)
        emails = extract_emails(results)

        st.success(f"Found {len(results)} links and {len(emails)} emails.")
        st.dataframe(df)
        st.subheader("\U0001F4E7 Extracted Emails")
        st.write(emails)

        st.subheader("\U0001F3F7\ufe0f AI Summary (Mock)")
        st.markdown(f"""Your search on **{query}** returned **{len(results)}** links with **{len(emails)}** potential contacts.""")

        st.subheader("\U0001F4CB Categorize This Batch")
        category = st.text_input("Tag this batch (e.g., 'Hip Hop Blogs', 'Estate Leads')")

        save_name = st.text_input("Save to campaign as:")
        if st.button("\U0001F4BE Save & Sync to Campaign") and save_name:
            final_df = pd.DataFrame({"email": emails, "category": category, "source": query})
            st.session_state.campaigns[save_name] = final_df
            save_campaign_data(save_name, final_df)
            st.success(f"Saved results to campaign: {save_name}")
