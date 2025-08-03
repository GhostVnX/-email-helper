# dashboard.py (Master UI - Unified Navigation & All Features)

import streamlit as st
import pandas as pd
if "campaigns" not in st.session_state:
    st.session_state["campaigns"] = {}
import os
from connect_gmail import login_to_gmail, send_email, load_campaign_log, fetch_replies
from campaign_utils import split_batches, load_campaign_data, save_campaign_data
from scraper_module import google_search, extract_emails
from datetime import datetime
import matplotlib.pyplot as plt

st.set_page_config(page_title="📧 GhostBot Dashboard", layout="wide", initial_sidebar_state="expanded")

# --- Custom Style ---
st.markdown("""
    <style>
        body { background-color: #0f1117; color: white; }
        .reportview-container .main .block-container { padding: 2rem; background-color: #1c1e26; }
        .sticky-box { background: #2a2d3e; padding: 1rem; border-radius: 10px; margin-bottom: 1rem; border-left: 4px solid #4ade80; }
        .stButton>button { background-color: #4ade80; color: #111827; border-radius: 0.5rem; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# --- Logo & Title ---
st.markdown("""
<div style="text-align:center">
    <img src="https://upload.wikimedia.org/wikipedia/commons/thumb/2/26/Ghostscript_Tiger.svg/1200px-Ghostscript_Tiger.svg.png" width="80"/>
    <h1 style="color:white;">GhostBot | All-in-One Creator Console</h1>
</div>
""", unsafe_allow_html=True)

# --- Unified Sidebar Navigation ---
nav = st.sidebar.radio("🚀 Navigate", [
    "🏠 Home",
    "📂 Upload or Search Contacts",
    "🧠 Preview & Personalize",
    "✉️ Send Emails",
    "📊 Email Tracker",
    "🔓 Unlock Playlist Contacts",
    "📣 Social Media Campaigns",
    "📺 Ads Campaigns",
    "🌐 Creator Website & EPK",
    "💬 Creator Forum",
    "💡 Creator Match",
    "📚 Resources & Blog"
])

# --- Home ---
if nav == "🏠 Home":
    st.header("🏠 Welcome to GhostBot")
    st.markdown("""
    Welcome to **GhostBot**, the ultimate platform for creators, musicians, and influencers to grow and manage their campaigns.

    ✅ Upload or Scrape Contacts
    ✅ Personalize Campaigns with Smart Prompts
    ✅ Send Bulk Emails & Track Results
    ✅ Unlock Playlist Curator Contacts
    ✅ Launch Social/Ad Campaigns
    ✅ Get Your Own Website + EPK
    ✅ Chat & Match with Other Creators
    ✅ Access Freebies & Tools
    """)

# --- Upload or Search ---
elif nav == "📂 Upload or Search Contacts":
    st.header("📂 Upload File OR Search Online")
    method = st.radio("Choose Method", ["Upload File", "Web Search"])

    if method == "Upload File":
        uploaded_file = st.file_uploader("Upload CSV or Excel", type=["csv", "xlsx"])
        campaign_name = st.text_input("Campaign Name")
        if uploaded_file and campaign_name:
            df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith(".csv") else pd.read_excel(uploaded_file)
            df.columns = [c.lower().strip() for c in df.columns]
            email_columns = [col for col in df.columns if "email" in col]
            if not email_columns:
                st.error("No email column found.")
            else:
                df.rename(columns={email_columns[0]: "email"}, inplace=True)
                df = df.dropna(subset=["email"])
                st.session_state.campaigns[campaign_name] = df
                save_campaign_data(campaign_name, df)
                st.success("Uploaded Successfully!")
                st.dataframe(df.head())

    else:
        keyword = st.text_input("Search Keywords")
        pages = st.slider("Pages", 1, 10, 3)
        if st.button("🔍 Search") and keyword:
            res = google_search(keyword, st.secrets["google"]["api_key"], st.secrets["google"]["cse_id"], pages)
            emails = extract_emails(res)
            st.success(f"Found {len(emails)} emails.")
            df = pd.DataFrame({"email": emails, "source": keyword})
            st.dataframe(df)
            name = st.text_input("Save Search as Campaign")
            if st.button("💾 Save Campaign") and name:
                st.session_state.campaigns[name] = df
                save_campaign_data(name, df)
                st.success("Saved successfully")

# --- Preview ---
elif nav == "🧠 Preview & Personalize":
    st.header("🧠 Email Personalization")
    if not st.session_state.get("campaigns"):
        st.warning("Upload or Search Contacts first")
    else:
        campaign = st.selectbox("Select Campaign", list(st.session_state.campaigns))
        style = st.selectbox("Tone", ["Formal", "Gen Z", "Chill", "Hype"])
        msg = st.text_area("Message", value=f"Thanks {{name}}, just checking in!")
        df = st.session_state.campaigns[campaign].copy()
        df["preview"] = df["email"].apply(lambda x: msg.replace("{name}", x.split("@")[0]))
        st.dataframe(df[["email", "preview"]])

# --- Send ---
elif nav == "✉️ Send Emails":
    st.header("✉️ Send Campaign")
    if not st.session_state.get("campaigns"):
        st.warning("No campaign selected")
    else:
        campaign = st.selectbox("Choose Campaign", list(st.session_state.campaigns))
        subject = st.text_input("Subject")
        message = st.text_area("Body")
        if st.button("🚀 Send Now"):
            creds = login_to_gmail()
            for _, row in st.session_state.campaigns[campaign].iterrows():
                send_email(creds, row["email"], subject, message.replace("{name}", row.get("name", "friend")), campaign)
            st.success("Emails Sent!")

# --- Tracker ---
elif nav == "📊 Email Tracker":
    st.header("📊 Campaign Tracker")
    for name in st.session_state.get("campaigns", {}):
        log = load_campaign_log(name)
        sent = [x[0] for x in log if x[1] == "success"]
        failed = [x for x in log if x[1] != "success"]
        st.subheader(f"📦 {name}")
        st.metric("Total", len(st.session_state.campaigns[name]))
        st.metric("Sent", len(sent))
        st.metric("Failed", len(failed))
        st.progress(len(sent)/max(1, len(st.session_state.campaigns[name])))

# --- Playlist Unlock ---
elif nav == "🔓 Unlock Playlist Contacts":
    st.header("🔓 Unlock Curator Contacts")
    st.info("You have 10 unlock credits left today")
    dummy = pd.DataFrame({"Curator": ["Blog A", "Blog B"], "Email": ["a@mail.com", "b@mail.com"]})
    st.dataframe(dummy)
    if st.button("🔓 Unlock One"):
        st.success("Contact Unlocked!")

# --- Social Campaigns ---
elif nav == "📣 Social Media Campaigns":
    st.header("📣 Schedule Social Content")
    st.text("Coming soon: Threads, IG, TikTok scheduler with caption AI")

# --- Ads Campaigns ---
elif nav == "📺 Ads Campaigns":
    st.header("📺 Launch Meta or YouTube Ads")
    st.text("Coming soon: Simple ad setup with targeting + auto cover art")

# --- Website & EPK ---
elif nav == "🌐 Creator Website & EPK":
    st.header("🌐 Create EPK or Artist Page")
    st.text("Coming soon: Choose template, upload images + auto bio builder")

# --- Forum ---
elif nav == "💬 Creator Forum":
    st.header("💬 Chat & Ask Questions")
    st.text("Coming soon: AMA & collab rooms with other GhostBot users")

# --- Match ---
elif nav == "💡 Creator Match":
    st.header("💡 Match with Collaborators")
    st.text("Coming soon: Tinder-style swipe to connect with producers, singers, etc.")

# --- Blog ---
elif nav == "📚 Resources & Blog":
    st.header("📚 Growth Tips & Freebies")
    st.markdown("""
    ✅ Free sample packs
    ✅ Promo contact lists
    ✅ Submission sites
    ✅ Growth guides
    """)
