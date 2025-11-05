"""Utilities to fetch Google Tasks data and OAuth tokens for Home Assistant."""
import os
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

# --- Constants ---
SCOPES = ["https://www.googleapis.com/auth/tasks.readonly"]
TOKEN_PATH = os.getenv("HA_TOKEN_PATH", "token.json")           # override with env if needed
CREDENTIALS_PATH = os.getenv("HA_CREDENTIALS_PATH", "credentials.json")
REDIRECT_HOST = "localhost"
REDIRECT_PORT = 8080


def main() -> None:
    creds = None

    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
            # Force a predictable redirect for Home Assistant dev envs:
            creds = flow.run_local_server(port=REDIRECT_PORT, host=REDIRECT_HOST)

        with open(TOKEN_PATH, "w", encoding="utf-8") as f:
            f.write(creds.to_json())

    print(f"OK: {os.path.abspath(TOKEN_PATH)} created")


if __name__ == "__main__":
    main()
