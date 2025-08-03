# playlist_unlock.py

import streamlit as st
import pandas as pd
import os

CSV_FILE = "Cleaned_Playlist_DB.csv"
UNLOCK_LOG = "unlocked_contacts.csv"

@st.cache_data
def load_data():
    if os.path.exists(CSV_FILE):
        df = pd.read_csv(CSV_FILE)
        df.columns = [col.strip().lower().replace(" ", "_") for col in df.columns]

        # Required fields
        required_cols = [
            "playlist_name", "email", "followers", "genre", "curator",
            "social_link", "bio", "platform", "url"
        ]
        for col in required_cols:
            if col not in df.columns:
                df[col] = None

        df.drop_duplicates(subset="email", inplace=True)
        df["genre"] = df["genre"].fillna("Unknown").astype(str).str.strip().str.title()
        df["platform"] = df["platform"].fillna("Spotify").astype(str).str.strip().str.title()
        df["followers"] = pd.to_numeric(df["followers"], errors="coerce").fillna(0)

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

def send_email_to_curator(email, playlist_name):
    print(f"Sending email to {email} for playlist: {playlist_name}")

def run_playlist_unlock():
    st.set_page_config("🔓 Unlock Playlist Contacts", layout="wide")
    st.title("🔓 Unlock Playlist Contacts")

    df = load_data()

    if "unlock_credits" not in st.session_state:
        st.session_state.unlock_credits = 10

    st.markdown(f"""
    🧮 **Credits Remaining Today:** `{st.session_state.unlock_credits}`  
    🔍 *Filter and unlock playlists across platforms. Only genre and followers are visible until unlocked.*
    """)

    # Filter valid emails only
    df = df[df["email"].notna() & df["email"].str.contains("@")]

    genre_options = sorted(df["genre"].dropna().unique())
    platform_options = sorted(df["platform"].dropna().unique())

    col1, col2, col3 = st.columns(3)
    with col1:
        genre_filter = st.selectbox("🎵 Filter by Genre", ["All"] + genre_options)
    with col2:
        platform_filter = st.selectbox("💽 Filter by Platform", ["All"] + platform_options)
    with col3:
        sort_order = st.selectbox("⬇️ Sort by", ["Followers (High → Low)", "Followers (Low → High)", "Playlist Name"])

    # Apply filters
    filtered = df.copy()
    if genre_filter != "All":
        filtered = filtered[filtered["genre"] == genre_filter]
    if platform_filter != "All":
        filtered = filtered[filtered["platform"] == platform_filter]

    # Apply sorting
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
        cost = 2 if row["followers"] > 10000 else 1
        section = colA if idx % 2 == 0 else colB

        with section:
            with st.container():
                st.markdown(f"""
                #### 🎵 *{row.get('genre', 'Unknown')}*  
                - 👥 **Followers**: {int(row['followers']) if pd.notna(row['followers']) else 'N/A'}
                """)
                
                # If unlocked, show more
                if f"unlocked_{idx}" in st.session_state:
                    st.markdown(f"""
                    - 🎧 **Playlist Name**: {row.get('playlist_name', 'N/A')}
                    - 👤 **Curator**: {row.get('curator', 'N/A')}
                    - 📧 **Email**: {row.get('email', 'N/A')}
                    - 🔗 **URL**: {row.get('url', 'N/A')}
                    - 📝 **Description**: {row.get('bio', 'N/A')}
                    - 🌐 **Social**: {row.get('social_link', 'N/A')}
                    """)
                    st.success("✅ Unlocked")
                else:
                    if st.session_state.unlock_credits >= cost:
                        if st.button(f"🔓 Unlock (-{cost})", key=f"unlock_{idx}"):
                            st.session_state[f"unlocked_{idx}"] = True
                            st.session_state.unlock_credits -= cost
                            unlocked_records.append(row)
                    else:
                        st.button("Out of credits", disabled=True, key=f"disabled_{idx}")

    # Save newly unlocked contacts
    if unlocked_records:
        new_unlocked_df = pd.DataFrame(unlocked_records)
        save_unlocked(new_unlocked_df)

    # Export / send unlocked
    if os.path.exists(UNLOCK_LOG):
        unlocked_df = pd.read_csv(UNLOCK_LOG)
        st.markdown("### 📬 Export / Use Unlocked Contacts")
        st.download_button("📥 Download as CSV", unlocked_df.to_csv(index=False), file_name="unlocked_contacts.csv")

        if st.button("📤 Send to Email Bot"):
            st.session_state.selected_recipients = unlocked_df
            st.success("✅ Unlocked emails saved to email bot memory")

        if "selected_recipients" in st.session_state:
            if st.button("Send Emails Now"):
                for _, row in st.session_state.selected_recipients.iterrows():
                    send_email_to_curator(row["email"], row["playlist_name"])
                st.success("✅ Emails sent!")
