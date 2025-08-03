import streamlit as st
import pandas as pd
import os

CSV_FILE = "playlist_contacts_final.csv"

@st.cache_data
def load_data():
    if os.path.exists(CSV_FILE):
        df = pd.read_csv(CSV_FILE)
        df.drop_duplicates(subset="email", inplace=True)
        return df
    else:
        return pd.DataFrame(columns=["playlist_name", "email", "followers", "genre", "curator", "social_link"])

def save_data(df):
    df.to_csv(CSV_FILE, index=False)

# ✅ This is the wrapper function
def run_playlist_unlock():
    st.set_page_config("🔓 Unlock Playlist Contacts", layout="wide")
    st.title("🔓 Unlock Playlist Contacts")

    df = load_data()

    # --- Admin Upload Section ---
    with st.expander("🔐 Admin: Upload New Playlist File"):
        admin_pass = st.text_input("Enter admin password", type="password")
        if admin_pass == "ghostadmin123":
            uploaded_file = st.file_uploader("Upload New Playlist CSV", type=["csv"])
            if uploaded_file:
                try:
                    new_df = pd.read_csv(uploaded_file)
                    required = {"playlist_name", "email", "followers", "genre", "curator"}
                    if not required.issubset(set(new_df.columns)):
                        st.error(f"File must include columns: {required}")
                    else:
                        combined = pd.concat([df, new_df], ignore_index=True)
                        combined.drop_duplicates(subset="email", inplace=True)
                        save_data(combined)
                        st.success(f"✅ Merged and saved! New total: {len(combined)}")
                        df = combined
                except Exception as e:
                    st.error(f"❌ Error: {e}")

    if "unlock_credits" not in st.session_state:
        st.session_state.unlock_credits = 10  # daily credits

    st.markdown(f"🧮 **Credits Remaining Today:** `{st.session_state.unlock_credits}`")

    col1, col2 = st.columns(2)
    with col1:
        genre_filter = st.selectbox("🎵 Filter by Genre", ["All"] + sorted(df["genre"].dropna().unique()))
    with col2:
        sort_order = st.selectbox("⬇️ Sort by", ["Playlist Name", "Followers (Low → High)", "Followers (High → Low)"])

    filtered = df.copy()
    if genre_filter != "All":
        filtered = filtered[filtered["genre"] == genre_filter]

    if sort_order == "Playlist Name":
        filtered = filtered.sort_values(by="playlist_name")
    elif sort_order == "Followers (Low → High)":
        filtered = filtered.sort_values(by="followers")
    else:
        filtered = filtered.sort_values(by="followers", ascending=False)

    st.markdown("### 📋 Playlist Curators")

    for idx, row in filtered.iterrows():
        cost = 2 if row["followers"] > 10000 else 1
        col1, col2 = st.columns([5, 1])
        with col1:
            st.markdown(f"""
            - **🎧 Playlist**: {row['playlist_name']}
            - 👤 Curator: {row.get('curator', 'N/A')}
            - 📧 Email: {"🔒 Locked" if f"unlocked_{idx}" not in st.session_state else row['email']}
            - 🌐 Followers: {int(row['followers']) if pd.notna(row['followers']) else "N/A"}
            - 🔗 Social: {row.get('social_link', 'N/A')}
            - 🏷️ Genre: {row.get('genre', 'N/A')}
            """)
        with col2:
            if f"unlocked_{idx}" not in st.session_state:
                if st.session_state.unlock_credits >= cost:
                    if st.button(f"Unlock (-{cost})", key=f"unlock_{idx}"):
                        st.session_state[f"unlocked_{idx}"] = True
                        st.session_state.unlock_credits -= cost
                else:
                    st.button("Out of credits", disabled=True, key=f"no_credit_{idx}")
            else:
                st.success("✅ Unlocked")
