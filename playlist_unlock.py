import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# --- Load Playlist Data ---
@st.cache_data
def load_playlist_data():
    df = pd.read_csv("playlist_contacts.csv")
    df["Points Required"] = df["followers"].apply(lambda x: 2 if x >= 10000 else 1)
    return df

# --- Initialize Session States ---
if "unlock_points" not in st.session_state:
    st.session_state.unlock_points = 10
if "unlocked_emails" not in st.session_state:
    st.session_state.unlocked_emails = []
if "last_reset" not in st.session_state:
    st.session_state.last_reset = datetime.now()

# --- Daily Reset Logic ---
if datetime.now() - st.session_state.last_reset > timedelta(days=1):
    st.session_state.unlock_points = 10
    st.session_state.unlocked_emails = []
    st.session_state.last_reset = datetime.now()

st.title("🔓 Unlock Playlist Contacts")

df = load_playlist_data()

# --- Sorting Controls ---
st.markdown(f"### You have **{st.session_state.unlock_points}** credits")
sort_by = st.selectbox("Sort by", ["followers (high → low)", "genre", "name"])
if sort_by == "followers (high → low)":
    df = df.sort_values(by="followers", ascending=False)
elif sort_by == "genre":
    df = df.sort_values(by="genre")
elif sort_by == "name":
    df = df.sort_values(by="name")

# --- Show Playlists ---
for i, row in df.iterrows():
    with st.expander(f"{row['name']} - {row['followers']} followers"):
        st.write(f"🎵 Genre: {row['genre']}")
        st.write(f"🔗 Playlist: {row['playlist_url']}")
        st.write(f"📧 Email: {'🔒 Locked' if row['email'] not in st.session_state.unlocked_emails else row['email']}")
        st.write(f"💳 Requires: {row['Points Required']} points")

        if row['email'] not in st.session_state.unlocked_emails:
            if st.button(f"🔓 Unlock {row['name']}", key=f"unlock_{i}"):
                if st.session_state.unlock_points >= row['Points Required']:
                    st.session_state.unlock_points -= row['Points Required']
                    st.session_state.unlocked_emails.append(row['email'])
                    st.success(f"Unlocked {row['email']}!")
                    st.rerun()
                else:
                    st.error("Not enough points to unlock.")
