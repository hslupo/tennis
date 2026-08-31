"""ICS-Kalenderexport, migriert aus bisher/export_ics.py – reine Logik ohne
UI- oder Datei-I/O-Abhängigkeiten."""

from datetime import datetime
from typing import Dict, Iterable

import pytz
from ics import Calendar, Event

LOCAL_TZ = pytz.timezone("Europe/Berlin")


def _ereignis_fuer_termin(
    datum: str, gruppe: Dict, spieler_ids: Iterable, ersatz_ids: Iterable, spieler_namen: Dict
) -> Event:
    namen = [str(spieler_namen.get(pid, pid)) for pid in spieler_ids]
    ersatz_namen = [str(spieler_namen.get(pid, pid)) for pid in ersatz_ids]

    e = Event()
    e.name = f"Tennis: {', '.join(namen)}"
    startzeit = gruppe.get("startzeit")
    endzeit = gruppe.get("endzeit")
    if startzeit and endzeit:
        e.begin = LOCAL_TZ.localize(datetime.strptime(f"{datum} {startzeit}", "%d.%m.%Y %H:%M"))
        e.end = LOCAL_TZ.localize(datetime.strptime(f"{datum} {endzeit}", "%d.%m.%Y %H:%M"))
    else:
        e.begin = datetime.strptime(datum, "%d.%m.%Y").date()
        e.make_all_day()
    e.location = f"Platz {gruppe['platz']}" if gruppe.get("platz") else None
    e.description = (
        f"Mögliche Ersatzspieler: {', '.join(ersatz_namen)}" if ersatz_namen else "Keine Ersatzspieler verfügbar."
    )
    return e


def _ersatz_ids(gruppe: Dict, datum: str, spieler_ids: Iterable) -> list:
    verfuegbare_ids = [
        pid for pid, d in gruppe.get("players", {}).items() if datum not in d.get("nicht_moeglich", [])
    ]
    return [pid for pid in verfuegbare_ids if pid not in spieler_ids]


def erstelle_ics_fuer_gruppe(gruppe: Dict, spieler_namen: Dict) -> str:
    """Erstellt einen ICS-Kalender mit allen geplanten Terminen einer Gruppe."""
    c = Calendar()
    c.creator = f"Tennisverteilung {gruppe.get('wochentag', '')}"
    for datum, spieler_ids in gruppe.get("verteilung", {}).items():
        ersatz_ids = _ersatz_ids(gruppe, datum, spieler_ids)
        c.events.add(_ereignis_fuer_termin(datum, gruppe, spieler_ids, ersatz_ids, spieler_namen))
    return c.serialize()


def erstelle_ics_fuer_spieler(
    saison: Dict, spieler_id, spieler_namen: Dict, *, gruppe_key: str | None = None
) -> str:
    """Erstellt einen ICS-Kalender mit den Terminen eines Spielers.

    Ohne gruppe_key (Saisonkalender) werden alle Gruppen der Saison durchsucht,
    mit gruppe_key (Gruppenkalender) nur die angegebene Gruppe.
    """
    c = Calendar()
    c.creator = "Tennisverteilung"
    gruppen = saison.get("groups", {})
    ziel_gruppen = {gruppe_key: gruppen[gruppe_key]} if gruppe_key else gruppen
    for gruppe in ziel_gruppen.values():
        if spieler_id not in gruppe.get("players", {}):
            continue
        for datum, spieler_ids in gruppe.get("verteilung", {}).items():
            if spieler_id not in spieler_ids:
                continue
            ersatz_ids = _ersatz_ids(gruppe, datum, spieler_ids)
            c.events.add(_ereignis_fuer_termin(datum, gruppe, spieler_ids, ersatz_ids, spieler_namen))
    return c.serialize()
