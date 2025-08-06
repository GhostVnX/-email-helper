import streamlit as st
import pandas as pd
import os
import re
from google.cloud import firestore
from streamlit.components.v1 import html
import json
import firebase_admin
from firebase_admin import credentials, auth

# --- 🔐 Firebase Admin SDK Setup ---
if not firebase_admin._apps:
    firebase_creds = json.loads(st.secrets["firebase_credentials"])
    cred = credentials.Certificate(firebase_creds)
    firebase_admin.initialize_app(cred)
    db = firestore.Client()

# --- Google Sign-In via Firebase Hosted UI ---
def render_google_login():
    login_url = (
        "https://music-hub-8d767.firebaseapp.com/__/auth/handler"
        "?redirect_uri=https://share.streamlit.io"
    )
    html(
        f"""
        <a href="{login_url}" target="_self">
            <button style="padding:0.5em 1em; font-size:16px;">Sign in with Google</button>
        </a>
        """,
        height=60,
    )

st.sidebar.title("🔐 Login")
email = st.sidebar.text_input("Email")
password = st.sidebar.text_input("Password", type="password")
render_google_login()

if "user_email" not in st.session_state:
    st.session_state.user_email = None

if st.sidebar.button("Login"):
    try:
        if email:
            user = auth.get_user_by_email(email)
            st.session_state.user_email = email
            st.sidebar.success(f"✅ Logged in as {email}")
        else:
            st.sidebar.error("❌ Please enter an email.")
            st.stop()
    except firebase_admin.auth.UserNotFoundError:
        st.sidebar.error("❌ No such user found.")
        st.stop()
    except Exception as e:
        st.sidebar.error(f"❌ Login error: {e}")
        st.stop()

if not st.session_state.user_email:
    st.warning("🔒 Please log in to access the app.")
    st.stop()

user_email = st.session_state.user_email
is_admin = user_email == "admin@email.com"

CSV_FILE = "Updated_Playlist_Data__with_extracted_emails_.csv"
UNLOCK_LOG = f"unlocked_{user_email.replace('@', '_at_')}.csv"

@st.cache_data
def load_data():
    def extract_email(text):
        if pd.isna(text):
            return ""
        match = re.search(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\\.[a-zA-Z0-9-.]+", str(text))
        return match.group(0) if match else ""

    if os.path.exists(CSV_FILE):
        df = pd.read_csv(CSV_FILE)
        df.columns = [col.strip().lower().replace(" ", "_") for col in df.columns]

        required_cols = [
            "playlist_name", "email", "followers", "genre", "curator",
            "social_link", "bio", "platform", "url"
        ]
        for col in required_cols:
            if col not in df.columns:
                df[col] = ""

        df["email"] = df["email"].fillna("").astype(str)
        df["email"] = df.apply(
            lambda row: row["email"] if "@" in row["email"] else extract_email(row.get("curator", "")),
            axis=1
        )
        df = df[df["email"].str.contains("@")]
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

    for _, row in df.iterrows():
        db.collection("unlocks").document(user_email).collection("contacts").document(row['email']).set(row.to_dict())

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
                - 📧 **Email**: {'🔒 Locked' if f"unlocked_{idx}" not in st.session_state else row['email']}
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
        st.markdown("### 📬 Your Unlocked Emails")
        unlocked_df = pd.read_csv(UNLOCK_LOG)
        st.download_button("📥 Download Your Contacts", unlocked_df.to_csv(index=False), file_name="my_unlocked_contacts.csv")

        if st.button("📤 Use These in Email Bot"):
            st.session_state.selected_recipients = unlocked_df
            st.success("✅ Emails sent to email bot memory. You can now proceed to sending.")

def send_email(email, playlist_name):
    print(f"📧 Sending email to {email} about playlist {playlist_name}")

def admin_upload():
    st.sidebar.markdown("### 🔧 Admin Upload")
    if not is_admin:
        st.sidebar.info("Only admins can upload new playlists.")
        return

    uploaded_file = st.sidebar.file_uploader("📤 Upload Playlist CSV", type=["csv"])
    if uploaded_file:
        df = pd.read_csv(uploaded_file)
        df.to_csv(CSV_FILE, index=False)
        st.sidebar.success("✅ Playlist database updated. Please refresh.")

if __name__ == "__main__":
    admin_upload()
    run_playlist_unlock()
