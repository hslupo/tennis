import datetime
import tkinter as tk
import tkinter.font as tkfont
from tkinter import ttk

from google_calendar_auth import authenticate_calendar

# Wenn der Geltungsbereich geändert wird, löschen Sie die Datei token.json.
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']


def authenticate():
    """Authentifiziert sich bei der Google Calendar API und gibt ein Service-Objekt zurück."""
    return authenticate_calendar(SCOPES)


def get_calendars(service):
    """Liest alle Kalender, auf die das Konto Zugriff hat."""
    calendar_list = service.calendarList().list().execute()
    return calendar_list.get('items', [])


def get_events(service, calendar_id='primary', max_results=10):
    """Liest die nächsten Ereignisse aus dem angegebenen Kalender."""
    now = datetime.datetime.utcnow().isoformat() + 'Z'
    events_result = service.events().list(
        calendarId=calendar_id,
        timeMin=now,
        maxResults=max_results,
        singleEvents=True,
        orderBy='startTime'
    ).execute()
    return events_result.get('items', [])


def format_event_start(start_info):
    """Formatiert Startzeit aus dateTime/date für die Anzeige."""
    raw_value = start_info.get('dateTime', start_info.get('date', 'Unbekannt'))

    if 'T' in raw_value:
        try:
            dt_obj = datetime.datetime.fromisoformat(raw_value.replace('Z', '+00:00'))
            return dt_obj.strftime('%d.%m.%Y %H:%M')
        except ValueError:
            return raw_value

    try:
        date_obj = datetime.date.fromisoformat(raw_value)
        return date_obj.strftime('%d.%m.%Y (ganztags)')
    except ValueError:
        return raw_value


class CalendarGui(tk.Tk):
    def __init__(self, service):
        super().__init__()
        self.service = service
        self.calendars = []
        self.title('Google Kalender Vorschau')
        self.geometry('980x620')
        self.minsize(860, 520)

        default_font = tkfont.nametofont('TkDefaultFont')
        text_font = tkfont.nametofont('TkTextFont')
        default_font.configure(size=12)
        text_font.configure(size=12)

        self.option_add('*TCombobox*Listbox.Font', default_font)

        style = ttk.Style(self)
        style.configure('TLabel', font=default_font)
        style.configure('TCombobox', font=default_font)

        heading_font = tkfont.Font(family=default_font.actual('family'), size=13, weight='bold')

        ttk.Label(self, text='Kalender auswählen:', font=heading_font).pack(anchor='w', padx=16, pady=(16, 8))

        self.calendar_combo = ttk.Combobox(self, state='readonly')
        self.calendar_combo.pack(fill='x', padx=16, ipady=4)
        self.calendar_combo.bind('<<ComboboxSelected>>', self.on_calendar_selected)

        self.output_text = tk.Text(self, wrap='word', height=18, font=text_font, padx=8, pady=8)
        self.output_text.pack(fill='both', expand=True, padx=16, pady=16)

        self.load_calendars()

    def load_calendars(self):
        try:
            self.calendars = get_calendars(self.service)
            if not self.calendars:
                self.show_text('Keine Kalender gefunden.')
                return

            values = [f"{cal.get('summary', 'Ohne Namen')} ({cal.get('id', '-')})" for cal in self.calendars]
            self.calendar_combo['values'] = values
            self.calendar_combo.current(0)
            self.show_events_for_selection(0)
        except Exception as error:
            self.show_text(f'Fehler beim Laden der Kalender:\n{error}')

    def on_calendar_selected(self, _event):
        selected_index = self.calendar_combo.current()
        self.show_events_for_selection(selected_index)

    def show_events_for_selection(self, index):
        if index < 0 or index >= len(self.calendars):
            self.show_text('Ungültige Kalenderauswahl.')
            return

        selected_calendar = self.calendars[index]
        calendar_id = selected_calendar.get('id', 'primary')
        calendar_name = selected_calendar.get('summary', calendar_id)

        try:
            events = get_events(self.service, calendar_id=calendar_id, max_results=10)
            if not events:
                self.show_text(f'Kalender: {calendar_name}\n\nKeine anstehenden Termine gefunden.')
                return

            lines = [f'Kalender: {calendar_name}', '', 'Nächste 10 Termine:', '']
            for event in events:
                start = format_event_start(event.get('start', {}))
                title = event.get('summary', '(Ohne Titel)')
                lines.append(f'- {start} | {title}')

            self.show_text('\n'.join(lines))
        except Exception as error:
            self.show_text(f'Fehler beim Laden der Termine:\n{error}')

    def show_text(self, content):
        self.output_text.delete('1.0', tk.END)
        self.output_text.insert(tk.END, content)


# Hauptprogramm
if __name__ == '__main__':
    try:
        calendar_service = authenticate()
        app = CalendarGui(calendar_service)
        app.mainloop()
    except Exception as e:
        print(f"Ein schwerwiegender Fehler ist aufgetreten: {e}")