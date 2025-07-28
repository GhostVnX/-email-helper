def login_to_gmail():
    creds = None
    if os.path.exists("token.pickle"):
        with open("token.pickle", "rb") as token:
            creds = pickle.load(token)

    if creds and creds.valid:
        return creds

    flow = InstalledAppFlow.from_client_config(
        json.loads(st.secrets["GOOGLE_CLIENT_SECRET"]),
        SCOPES
    )

    auth_url, _ = flow.authorization_url(prompt='consent')

    st.info("To connect Gmail, follow this link below:")
    st.markdown(f"[Click here to authorize Gmail]({auth_url})")

    auth_code = st.text_input("Paste the authorization code here:")

    if auth_code:
        try:
            flow.fetch_token(code=auth_code)
            creds = flow.credentials
            with open("token.pickle", "wb") as token:
                pickle.dump(creds, token)
            st.success("✅ Gmail authenticated successfully!")
            return creds
        except Exception as e:
            st.error(f"Error: {e}")

    st.stop()
