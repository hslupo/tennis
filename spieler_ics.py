import datetime
from icalendar import Calendar, Event

from google_calendar_auth import authenticate_calendar

# Wenn der Geltungsbereich geändert wird, löschen Sie die Datei token.json.
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']


def authenticate():
    """Authentifiziert sich bei der Google Calendar API und gibt ein Service-Objekt zurück."""
    return authenticate_calendar(SCOPES)


def list_calendars(service):
    """Listet alle Kalender auf, auf die das Konto Zugriff hat."""
    print('Verfügbare Kalender:')
    calendar_list = service.calendarList().list().execute()
    return {cal['summary']: cal['id'] for cal in calendar_list.get('items', [])}


def get_user_input(available_calendars):
    """
    Fragt den Benutzer nach Kalendern und Spielernamen.

    Args:
        available_calendars (dict): Ein Wörterbuch mit {Name: ID} der verfügbaren Kalender.

    Returns:
        tuple: Eine Liste von Kalender-IDs und eine Liste von Spielernamen.
    """
    print("\n------------------------------")
    print("Bitte wählen Sie Kalender und geben Sie Spielernamen ein.")
    print("------------------------------")

    # Anzeigen der Kalendernamen zur Auswahl
    print("Verfügbare Kalender:")
    for name in available_calendars:
        print(f"- {name}")

    # Eingabe für Kalender
    selected_cal_names_str = input(
        "\nGeben Sie die Kalendernamen durch Kommas getrennt ein (z.B. Tennis 1, Tennis 2): ")
    selected_cal_names = [name.strip() for name in selected_cal_names_str.split(',')]

    # Konvertierung der Kalendernamen in IDs
    selected_cal_ids = []
    for name in selected_cal_names:
        if name in available_calendars:
            selected_cal_ids.append(available_calendars[name])
        else:
            print(f"Warnung: Kalender '{name}' nicht gefunden. Er wird ignoriert.")

    # Eingabe für Spieler
    players_str = input("Geben Sie die Spielernamen durch Kommas getrennt ein (z.B. Peter, Hans): ")
    players = [name.strip() for name in players_str.split(',')]

    if not selected_cal_ids or not players:
        print("Es wurden keine gültigen Kalender oder Spieler eingegeben. Das Skript wird beendet.")
        return None, None

    return selected_cal_ids, players


def find_tennis_events(service, calendar_ids, players, start_date, end_date):
    """
    Sucht nach Tennis-Terminen für angegebene Spieler in mehreren Kalendern.

    Args:
        service: Das Google Calendar API-Service-Objekt.
        calendar_ids (list): Eine Liste von Kalender-IDs.
        players (list): Eine Liste von Spielernamen.
        start_date (datetime): Der Startzeitpunkt der Suche.
        end_date (datetime): Der Endzeitpunkt der Suche.

    Returns:
        list: Eine Liste der passenden Google Calendar Events.
    """
    matched_events = []
    player_names_lower = [p.lower() for p in players]

    for cal_id in calendar_ids:
        events_result = service.events().list(
            calendarId=cal_id,
            timeMin=start_date.isoformat() + 'Z',
            timeMax=end_date.isoformat() + 'Z',
            singleEvents=True,
            orderBy='startTime'
        ).execute()

        events = events_result.get('items', [])

        for event in events:
            summary = event.get('summary', '')
            if 'Tennis:' in summary:
                for player in player_names_lower:
                    if player in summary.lower():
                        matched_events.append(event)
                        break

    return matched_events


def create_ics_file(events, filename):
    """
    Erzeugt eine ics-Datei aus einer Liste von Google Calendar Events.
    """
    cal = Calendar()
    cal.add('prodid', '-//My Tennis Events//EN')
    cal.add('version', '2.0')

    for event_data in events:
        event = Event()
        event.add('summary', event_data.get('summary', ''))

        start_time_str = event_data['start'].get('dateTime', event_data['start'].get('date'))
        end_time_str = event_data['end'].get('dateTime', event_data['end'].get('date'))

        if 'T' in start_time_str:
            event.add('dtstart', datetime.datetime.fromisoformat(start_time_str))
            event.add('dtend', datetime.datetime.fromisoformat(end_time_str))
        else:
            event.add('dtstart', datetime.date.fromisoformat(start_time_str))
            event.add('dtend', datetime.date.fromisoformat(end_time_str))

        cal.add_component(event)

    with open(filename, 'wb') as f:
        f.write(cal.to_ical())

    print(f"ICS-Datei '{filename}' erfolgreich erstellt mit {len(events)} Terminen.")


if __name__ == '__main__':
    try:
        service = authenticate()

        available_calendars = list_calendars(service)
        selected_cal_ids, players_to_find = get_user_input(available_calendars)

        if selected_cal_ids and players_to_find:
            # Suchen von September 2025 bis Mai 2026
            start_date = datetime.datetime(2025, 9, 1, 0, 0, 0)
            end_date = datetime.datetime(2026, 5, 31, 23, 59, 59)

            print("\nSuche nach Tennisterminen...")
            found_events = find_tennis_events(service, selected_cal_ids, players_to_find, start_date, end_date)

            if found_events:
                # Erzeugt einen Dateinamen aus den Spielernamen, getrennt durch Unterstrich
                player_string = '_'.join(players_to_find)
                filename = f'tennis_termine_{player_string}.ics'
                create_ics_file(found_events, filename)
            else:
                print("Keine passenden Termine gefunden.")

    except Exception as e:
        print(f"Ein schwerwiegender Fehler ist aufgetreten: {e}")
