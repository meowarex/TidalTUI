import tidalapi
import json
import os
from datetime import datetime

CREDENTIALS_FILE = "credentials.json"

def load_credentials():
    if os.path.exists(CREDENTIALS_FILE):
        with open(CREDENTIALS_FILE, "r") as file:
            try:
                return json.load(file)
            except json.JSONDecodeError:
                return {}
    return {}

def save_credentials(session):
    with open(CREDENTIALS_FILE, "w") as file:
        json.dump({
            "access_token": session.access_token,
            "refresh_token": session.refresh_token,
            "expiry_time": session.expiry_time.isoformat(),
            "token_type": session.token_type
        }, file)

def initialize_session():
    session = tidalapi.Session()
    credentials = load_credentials()

    if credentials:
        session.load_oauth_session(
            access_token=credentials.get("access_token"),
            refresh_token=credentials.get("refresh_token"),
            expiry_time=datetime.fromisoformat(credentials.get("expiry_time")),
            token_type=credentials.get("token_type", "Bearer")
        )
    else:
        session.login_oauth_simple()
        save_credentials(session)

    return session

def get_playlists(session):
    return session.user.playlists()
