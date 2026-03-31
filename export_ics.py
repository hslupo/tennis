import json
from ics import Calendar, Event
from datetime import datetime
import pytz
import os


# --- Hilfsfunktion zur Namensformatierung (unverändert) ---
def format_name(name):
    """Formatiert einen Spielernamen: Erster Buchstabe groß, Sonderfall 'horstS'."""
    if not isinstance(name, str):
        return ""
    if name.lower() == 'horsts':
        return 'Horst'
    return name.capitalize()


# --- NEU: Die Hauptlogik als Funktion gekapselt ---
def create_calendar(datendatei, gruppe_name, extratermin_spieler=None, dateischreiben=False):
    """
    Erstellt einen iCalendar (.ics) String aus einer JSON-Datendatei für eine Tennisgruppe.

    Args:
        datendatei (str): Pfad zur JSON-Datei.
        gruppe_name (str): Name der Gruppe (z.B. 'freitag'), die verarbeitet werden soll.
        extratermin_spieler (str, optional): Name eines Spielers, für den zusätzliche
                                             ganztägige Termine erstellt werden. Defaults to None.
        dateischreiben (bool, optional): Wenn True, wird eine .ics-Datei geschrieben.
                                         Defaults to False.

    Returns:
        str: Der generierte Kalender als .ics-formatierter String.
    """
    try:
        with open(datendatei, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        return f"Fehler: Die Datei '{datendatei}' wurde nicht gefunden."

    # Gruppe case-insensitive auswählen
    gruppe_key = gruppe_name.lower()
    if gruppe_key not in data["groups"]:
        return f"Fehler: Die Gruppe '{gruppe_name}' wurde in der Datei nicht gefunden."

    gruppe = data["groups"][gruppe_key]
    jahr = data["jahr"]
    local_tz = pytz.timezone('Europe/Berlin')

    # Kalender-Objekt erstellen
    kalender_name = f"{gruppe['wochentag']} {jahr}"
    c = Calendar()
    c.creator = kalender_name
    textausgabe = ''

    # Formatiere den Namen des Spielers für den Extratermin zur besseren Vergleichbarkeit
    extratermin_spieler_formatiert = format_name(extratermin_spieler)

    # Jeden Spieltag der Gruppe verarbeiten
    for datum_str, eingesetzte_spieler_roh in gruppe["verteilung"].items():

        eingesetzte_spieler_formatiert = [format_name(name) for name in eingesetzte_spieler_roh]
        textausgabe += f'{datum_str} - {", ".join(eingesetzte_spieler_formatiert)}\n'

        # 1. Ersatzspieler ermitteln
        verfuegbare_spieler = [sp for sp, det in gruppe["players"].items() if datum_str not in det["nicht_moeglich"]]
        ersatzspieler_roh = [sp for sp in verfuegbare_spieler if sp not in eingesetzte_spieler_roh]
        ersatzspieler_formatiert = [format_name(name) for name in ersatzspieler_roh]

        # 2. Haupt-Termin erstellen (mit Zeit)
        naive_start_dt = datetime.strptime(f"{datum_str} {gruppe['startzeit']}", "%d.%m.%Y %H:%M")
        naive_end_dt = datetime.strptime(f"{datum_str} {gruppe['endzeit']}", "%d.%m.%Y %H:%M")

        e = Event()
        e.name = f"Tennis: {', '.join(eingesetzte_spieler_formatiert)}"
        e.begin = local_tz.localize(naive_start_dt)
        e.end = local_tz.localize(naive_end_dt)
        e.location = f"Platz {gruppe['platz']}"
        e.description = f"Mögliche Ersatzspieler: {', '.join(ersatzspieler_formatiert)}" if ersatzspieler_formatiert else "Keine Ersatzspieler verfügbar."
        c.events.add(e)

        # 3. Zusätzlichen ganztägigen Termin erstellen, falls zutreffend
        if extratermin_spieler and extratermin_spieler_formatiert in eingesetzte_spieler_formatiert:
            extra_e = Event()
            extra_e.name = f"{extratermin_spieler_formatiert} spielt Tennis"
            # Für ganztägige Termine nur das Datum verwenden
            event_date = datetime.strptime(datum_str, "%d.%m.%Y").date()
            extra_e.begin = event_date
            extra_e.make_all_day()
            c.events.add(extra_e)

    # 4. Kalender als String serialisieren
    ics_string = c.serialize()

    # 5. Optional die Datei schreiben
    if dateischreiben:
        # Erstelle einen sicheren Dateinamen
        filename = f"tennis_{gruppe_key}_{jahr}.ics"
        with open(filename, "w", encoding='utf-8') as f:
            f.write(ics_string)
        print(f"\nKalender wurde erfolgreich in '{filename}' gespeichert.")

    return ics_string, textausgabe


# --- Hauptausführungsteil ---
if __name__ == "__main__":
    # Standard-Parameter setzen, wenn das Skript direkt ausgeführt wird
    json_datei = "2025.json"  # Annahme, dass deine Datei 'daten.json' heißt
    gewaehlte_gruppe = "freitag"
    extra_spieler = "horstSg"  # Hier den Roh-Namen aus der JSON-Datei verwenden

    print(f"Erstelle Kalender für Gruppe '{gewaehlte_gruppe}' aus Datei '{json_datei}'...")

    # Die Funktion mit den Parametern aufrufen
    kalender_ics, textausgabe = create_calendar(
        datendatei=json_datei,
        gruppe_name=gewaehlte_gruppe,
        extratermin_spieler=extra_spieler,
        dateischreiben=True
    )

    # Optional: Den Anfang des Ergebnisses auf der Konsole ausgeben
    print("\n--- Beginn der Einsätze ---\n\n")
    print(textausgabe)
    # print("\n".join(kalender_output.splitlines()[:20])) # Zeigt die ersten 20 Zeilen
    # print("...")