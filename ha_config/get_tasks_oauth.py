"""Utilities to fetch Google Tasks data and OAuth tokens for Home Assistant."""
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
import os

SCOPES = ['https://www.googleapis.com/auth/tasks.readonly']

def main():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            # Force a predictable redirect:
            creds = flow.run_local_server(port=8080, host='localhost')  # <-- important
        with open('token.json', 'w') as f:
            f.write(creds.to_json())
    print("OK: token.json created")

if __name__ == '__main__':
    main()