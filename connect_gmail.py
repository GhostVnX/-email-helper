def login_to_gmail():
    creds = None
    if os.path.exists("token.pickle"):
        with open("token.pickle", "rb") as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_config(
                json.loads(st.secrets["GOOGLE_CLIENT_SECRET"]),
                SCOPES
            )
            creds = flow.run_console()  # Cloud-safe method

        with open("token.pickle", "wb") as token:
            pickle.dump(creds, token)

    return creds

