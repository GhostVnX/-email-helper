# playlist_unlock.py
import streamlit as st
import pandas as pd

st.set_page_config(page_title="🔓 Unlock Playlists", layout="wide")

# --- Load Playlist Contact File ---
@st.cache_data

def load_data():
    return pd.read_csv("playlist_contacts_final.csv")

playlist_df = load_data()

# --- UI Header ---
st.title("🔓 Unlock Playlist Contacts")
st.markdown("""
Welcome to your vault of high-quality playlist curator contacts. 
Use your daily credits to unlock new leads!
""")

# --- Credit Management ---
if "credits" not in st.session_state:
    st.session_state.credits = 10

st.info(f"💳 You have {st.session_state.credits} credits left today")

# --- Filters ---
col1, col2, col3 = st.columns(3)
with col1:
    genre = st.selectbox("🎧 Filter by Genre", ["All"] + sorted(playlist_df["genre"].dropna().unique()))
with col2:
    has_social = st.selectbox("📱 With Social Links?", ["All", "Yes", "No"])
with col3:
    sort_type = st.selectbox("⬇️ Sort By", ["Followers High to Low", "Followers Low to High"])

filtered = playlist_df.copy()

if genre != "All":
    filtered = filtered[filtered["genre"] == genre]

if has_social == "Yes":
    filtered = filtered[filtered["instagram"].notna() | filtered["twitter"].notna()]
elif has_social == "No":
    filtered = filtered[filtered["instagram"].isna() & filtered["twitter"].isna()]

if sort_type == "Followers High to Low":
    filtered = filtered.sort_values("followers", ascending=False)
else:
    filtered = filtered.sort_values("followers")

# --- Display Table ---
st.dataframe(filtered[["playlist_name", "email", "followers", "genre", "instagram", "twitter", "unlock_cost"]].reset_index(drop=True))

# --- Unlock Feature ---
idx_to_unlock = st.number_input("🔢 Enter row number to unlock", min_value=0, max_value=len(filtered)-1, step=1)

if st.button("🔓 Unlock Selected Contact"):
    contact = filtered.iloc[idx_to_unlock]
    cost = contact["unlock_cost"]
    if st.session_state.credits >= cost:
        st.session_state.credits -= cost
        st.success(f"Unlocked {contact['playlist_name']} ({contact['email']})")
    else:
        st.error("Not enough credits!")
