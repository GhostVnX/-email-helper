# playlist_unlock.py

import streamlit as st
import pandas as pd
import os
import re

CSV_FILE = "Updated_Playlist_Data__with_extracted_emails_.csv"
UNLOCK_LOG = "unlocked_contacts.csv"

@st.cache_data
def load_data():
    def extract_email(text):
        if pd.isna(text):
            return ""
        match = re.search(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", str(text))
        return match.group(0) if match else ""

    if os.path.exists(CSV_FILE):
        df = pd.read_csv(CSV_FILE)
        df.columns = [col.strip().lower().replace(" ", "_") for col in df.columns]

        # Ensure required columns
        required_cols = [
            "playlist_name", "email", "followers", "genre", "curator",
            "social_link", "bio", "platform", "url"
        ]
        for col in required_cols:
            if col not in df.columns:
                df[col] = ""

        # Clean and extract emails if missing
        df["email"] = df["email"].fillna("").astype(str)
        df["email"] = df.apply(
            lambda row: row["email"] if "@" in row["email"] else extract_email(row.get("curator", "")),
            axis=1
        )

        # Keep only rows with valid emails
        df = df[df["email"].str.contains("@")]

        # Normalize values
        df["genre"] = df["genre"].astype(str).str.strip().str.title()
        df["platform"] = df["platform"].astype(str).str.strip().str.title()
        df["followers"] = pd.to_numeric(df["followers"], errors="coerce").fillna(0)

        df.drop_duplicates(subset="email", inplace=True)

        return df
    else:
        return pd.DataFrame(columns=[
            "playlist_name", "email", "followers", "genre", "curator",
            "social_link", "bio", "platform", "url"
        ])

def save_unlocked(df):
    if os.path.exists(UNLOCK_LOG):
        existing = pd.read_csv(UNLOCK_LOG)
        df = pd.concat([existing, df], ignore_index=True).drop_duplicates(subset=["email"])
    df.to_csv(UNLOCK_LOG, index=False)

def run_playlist_unlock():
    st.set_page_config("🔓 Unlock Playlist Contacts", layout="wide")
    st.title("🔓 Unlock Playlist Contacts")

    df = load_data()

    if "unlock_credits" not in st.session_state:
        st.session_state.unlock_credits = 10

    st.markdown(f"""
    🧮 **Credits Remaining Today:** `{st.session_state.unlock_credits}`  
    🔍 *Search thousands of playlists with contact details across major platforms. Filter and unlock now!*
    """)

    col1, col2, col3 = st.columns(3)
    with col1:
        genre_filter = st.selectbox("🎵 Filter by Genre", ["All"] + sorted(df["genre"].dropna().unique()))
    with col2:
        platform_filter = st.selectbox("💽 Platform", ["All"] + sorted(df["platform"].dropna().unique()))
    with col3:
        sort_order = st.selectbox("⬇️ Sort by", ["Playlist Name", "Followers (Low → High)", "Followers (High → Low)"])

    filtered = df.copy()
    if genre_filter != "All":
        filtered = filtered[filtered["genre"] == genre_filter]
    if platform_filter != "All":
        filtered = filtered[filtered["platform"] == platform_filter]

    if sort_order == "Playlist Name":
        filtered = filtered.sort_values(by="playlist_name")
    elif sort_order == "Followers (Low → High)":
        filtered = filtered.sort_values(by="followers")
    else:
        filtered = filtered.sort_values(by="followers", ascending=False)

    st.markdown("### 📋 Playlist Curators")
    colA, colB = st.columns(2)
    unlocked_records = []

    for idx, row in filtered.iterrows():
        cost = 2 if row["followers"] and row["followers"] > 10000 else 1
        section = colA if idx % 2 == 0 else colB

        with section:
            with st.container():
                st.markdown(f"""
                #### 🎧 {row['playlist_name'] or 'N/A'}
                - 👤 **Curator**: {row.get('curator', 'N/A')}
                - 📧 **Email**: {"🔒 Locked" if f"unlocked_{idx}" not in st.session_state else row['email']}
                - 🌐 **Followers**: {int(row['followers']) if pd.notna(row['followers']) else 'N/A'}
                - 🏷️ **Genre**: {row.get('genre', 'N/A')}
                - 💽 **Platform**: {row.get('platform', 'N/A')}
                - 🔗 **Social**: {row.get('social_link', 'N/A')}
                - 🔗 **URL**: {row.get('url', 'N/A')}
                - 📝 **Bio**: {row.get('bio', 'N/A')}
                """)

                if f"unlocked_{idx}" not in st.session_state:
                    if st.session_state.unlock_credits >= cost:
                        if st.button(f"Unlock (-{cost})", key=f"unlock_{idx}"):
                            st.session_state[f"unlocked_{idx}"] = True
                            st.session_state.unlock_credits -= cost
                            unlocked_records.append(row)
                    else:
                        st.button("Out of credits", disabled=True, key=f"no_credit_{idx}")
                else:
                    st.success("✅ Unlocked")

    if unlocked_records:
        new_unlocked_df = pd.DataFrame(unlocked_records)
        save_unlocked(new_unlocked_df)

    if os.path.exists(UNLOCK_LOG):
        st.markdown("### 📬 Export Unlocked Emails")
        unlocked_df = pd.read_csv(UNLOCK_LOG)
        st.download_button("📥 Download Unlocked Contacts", unlocked_df.to_csv(index=False), file_name="unlocked_contacts.csv")

        if st.button("📤 Use These in Email Bot"):
            st.session_state.selected_recipients = unlocked_df
            st.success("✅ Emails sent to email bot memory. You can now proceed to sending.")
