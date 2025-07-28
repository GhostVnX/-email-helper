# dashboard.py (Enhanced with AI Suggestions, Export, Auto-Schedule)

import streamlit as st
import pandas as pd
import os
from connect_gmail import login_to_gmail, send_email
from campaign_utils import split_batches, load_campaign_data, save_campaign_data
from datetime import datetime, timedelta
import threading
import requests
import matplotlib.pyplot as plt
import openai

st.set_page_config(page_title="📧 GhostBot Dashboard", layout="wide")

# --- Auth ---
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

# --- Navigation ---
st.sidebar.title("GhostBot Navigation")
page = st.sidebar.radio("Go to", ["📤 Upload Contacts", "🧠 Preview & Personalize", "✉️ Send Emails", "📈 Campaign Tracker"])

if "campaigns" not in st.session_state:
    st.session_state.campaigns = {}

# --- Upload Contacts ---
if page == "📤 Upload Contacts":
    st.title("📤 Upload Contact File")
    uploaded_file = st.file_uploader("Upload CSV or Excel", type=["csv", "xlsx"])
    campaign_name = st.text_input("Campaign Name (unique)")
    if uploaded_file and campaign_name:
        df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith(".csv") else pd.read_excel(uploaded_file)
        df.columns = [c.lower().strip() for c in df.columns]
        if not any("email" in col for col in df.columns):
            st.error("No column containing the word 'email' found.")
        else:
            st.session_state.campaigns[campaign_name] = df
            save_campaign_data(campaign_name, df)
            st.success(f"Campaign '{campaign_name}' uploaded successfully!")
            st.dataframe(df.head())

# --- Preview ---
elif page == "🧠 Preview & Personalize":
    st.title("🧠 Email Preview, Filtering & Save-As-Campaign")
    if not st.session_state.campaigns:
        st.info("Upload a contact list first.")
    else:
        campaign = st.selectbox("Select Campaign", list(st.session_state.campaigns))
        df = st.session_state.campaigns[campaign].copy()

        # AI Keyword Suggestion (Optional)
        if st.button("💡 Suggest Filter Topics"):
            try:
                openai.api_key = os.getenv("OPENAI_API_KEY")
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "system", "content": "Suggest email list filters based on music or niche audience"},
                              {"role": "user", "content": str(df.head(50))}]
                )
                suggestions = response.choices[0].message.content
                st.info(f"Suggested Filters: {suggestions}")
            except Exception as e:
                st.error(f"OpenAI Error: {e}")

        prompt_keywords = st.text_area("Prompt: What do you want to find? (e.g. hiphop curators, afrobeat emails)")
        matched = df.copy()
        if prompt_keywords:
            keywords = [k.strip().lower() for k in prompt_keywords.split(",") if k.strip()]
            matched = df[df.apply(lambda row: any(k in str(row).lower() for k in keywords), axis=1)]

        if st.checkbox("Only rows with emails"):
            matched = matched[matched.apply(lambda row: any("@" in str(val) for val in row if isinstance(val, str)), axis=1)]

        sample_n = st.slider("Limit preview rows", 1, len(matched), min(50, len(matched))) if len(matched) > 50 else len(matched)
        matched = matched.head(sample_n)

        subject = st.text_input("Subject")
        body = st.text_area("Body with {name} placeholder")
        matched["preview"] = matched.apply(lambda row: body.replace("{name}", row.get("name", "there")), axis=1)
        st.dataframe(matched[[col for col in matched.columns if "email" in col] + ["preview"]])

        # Export as CSV Option
        if st.download_button("📤 Download Filtered CSV", data=matched.to_csv(index=False).encode(), file_name="filtered_campaign.csv"):
            st.success("Filtered CSV downloaded.")

        new_campaign_name = st.text_input("New Campaign Name to Save Filtered List")
        if st.button("💾 Save Filtered as Campaign") and new_campaign_name:
            st.session_state.campaigns[new_campaign_name] = matched
            save_campaign_data(new_campaign_name, matched)
            st.success(f"Filtered contacts saved as '{new_campaign_name}' and ready for sending!")

# --- Send Emails ---
elif page == "✉️ Send Emails":
    st.title("✉️ Send Emails")
    if not st.session_state.campaigns:
        st.warning("Upload a contact list first.")
    else:
        campaign = st.selectbox("Select Campaign to Send", list(st.session_state.campaigns))
        creds = login_to_gmail()
        subject = st.text_input("Subject")
        body = st.text_area("Email Body (HTML supported)")
        followup = st.checkbox("Enable Follow-Up After 10 Minutes")
        auto_batch = st.checkbox("Auto-Schedule Emails by Gmail Daily Limit (100/day)")
        send_button = st.button("🚀 Start Sending")

        if send_button:
            df = st.session_state.campaigns[campaign]
            sent_count = 0

            def send_batch(start_index):
                batch = df.iloc[start_index:start_index+100]
                for _, row in batch.iterrows():
                    email = row.get("email")
                    name = row.get("name", "there")
                    html_body = body.replace("{name}", name)
                    result = send_email(creds, email, subject, html_body, campaign)
                    if result.get("status") == "success":
                        nonlocal sent_count
                        sent_count += 1
                    st.write(f"{email} → {result.get('status')}")

            if auto_batch:
                start_idx = 0
                while start_idx < len(df):
                    send_batch(start_idx)
                    start_idx += 100
                    st.info(f"Batch complete: {start_idx} emails. Waiting until next day.")
                    time.sleep(86400)  # Delay for next batch
            else:
                send_batch(0)

            st.success(f"✅ {sent_count} emails sent in '{campaign}'")

# --- Campaign Tracker ---
elif page == "📈 Campaign Tracker":
    st.title("📈 Campaign Dashboard")
    if not st.session_state.campaigns:
        st.info("No campaigns loaded.")
    else:
        for campaign, df in st.session_state.campaigns.items():
            st.subheader(f"📦 {campaign}")
            from connect_gmail import load_campaign_log
            log = load_campaign_log(campaign)
            st.metric("Contacts", len(df))
            st.metric("Sent", len(log))
            st.metric("Pending", len(df) - len(log))
            st.progress(len(log) / len(df))

            st.write("---")
            st.write("📊 **Open & Click Stats**")
            track_url = f"https://your-domain.com/stats?campaign={campaign}"
            try:
                res = requests.get(track_url)
                if res.status_code == 200:
                    stats = res.json()
                    st.metric("📬 Opens", stats["opens"])
                    st.metric("🔗 Clicks", stats["clicks"])

                    if stats["open_by_email"]:
                        st.write("**Open Rate by Email**")
                        fig1, ax1 = plt.subplots()
                        ax1.bar(stats["open_by_email"].keys(), stats["open_by_email"].values())
                        ax1.set_xticklabels(stats["open_by_email"].keys(), rotation=90)
                        st.pyplot(fig1)

                    if stats["click_by_email"]:
                        st.write("**Click Rate by Email**")
                        fig2, ax2 = plt.subplots()
                        ax2.bar(stats["click_by_email"].keys(), stats["click_by_email"].values(), color="green")
                        ax2.set_xticklabels(stats["click_by_email"].keys(), rotation=90)
                        st.pyplot(fig2)

                    st.write("🕵️‍♂️ Open Events")
                    st.json(stats["open_details"])
                    st.write("🧲 Click Events")
                    st.json(stats["click_details"])
                else:
                    st.warning("No tracking data or failed to fetch.")
            except Exception as e:
                st.error(f"Tracking error: {e}")
