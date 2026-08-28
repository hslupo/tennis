import os

from google.auth.exceptions import RefreshError
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TOKEN_FILE = os.path.join(BASE_DIR, 'token.json')
CREDENTIALS_FILE = os.path.join(BASE_DIR, 'credentials.json')


def _request_new_credentials(scopes):
    flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, scopes)
    return flow.run_local_server(port=0)


def authenticate_calendar(scopes):
    """Authentifiziert sich bei der Google Calendar API und erzeugt ein Service-Objekt."""
    creds = None

    if os.path.exists(TOKEN_FILE):
        try:
            creds = Credentials.from_authorized_user_file(TOKEN_FILE, scopes)
        except (ValueError, OSError):
            creds = None

    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
        except RefreshError:
            creds = None
            if os.path.exists(TOKEN_FILE):
                os.remove(TOKEN_FILE)

    if not creds or not creds.valid:
        creds = _request_new_credentials(scopes)
        with open(TOKEN_FILE, 'w', encoding='utf-8') as token:
            token.write(creds.to_json())

    return build('calendar', 'v3', credentials=creds)
