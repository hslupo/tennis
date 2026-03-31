import datetime
import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Wenn der Geltungsbereich geändert wird, löschen Sie die Datei token.json.
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']


def authenticate():
    """Authentifiziert sich bei der Google Calendar API und gibt ein Service-Objekt zurück."""
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    return build('calendar', 'v3', credentials=creds)


def list_calendars(service):
    """Listet alle Kalender auf, auf die das Konto Zugriff hat."""
    print('Verfügbare Kalender:')
    calendar_list = service.calendarList().list().execute()
    for calendar in calendar_list.get('items', []):
        print(f"Name: {calendar['summary']} | ID: {calendar['id']}")


def list_events(service, calendar_id='primary'):
    """Listet die nächsten 10 Ereignisse aus dem angegebenen Kalender auf."""
    try:
        now = datetime.datetime.utcnow().isoformat() + 'Z'
        print(f'\nDie nächsten 10 Termine aus dem Kalender "{calendar_id}":')

        events_result = service.events().list(
            calendarId=calendar_id,
            timeMin=now,
            maxResults=10,
            singleEvents=True,
            orderBy='startTime'
        ).execute()

        events = events_result.get('items', [])

        if not events:
            print('Keine anstehenden Termine gefunden.')
            return

        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            print(start, event['summary'])

    except Exception as error:
        print(f'Ein Fehler ist aufgetreten: {error}')


# Hauptprogramm
if __name__ == '__main__':
    try:
        calendar_service = authenticate()
        list_calendars(calendar_service)
        list_events(calendar_service, 'primary')
    except Exception as e:
        print(f"Ein schwerwiegender Fehler ist aufgetreten: {e}")