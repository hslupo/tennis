import datetime
from typing import List


def ermittle_state(jahr: int):
    """
    Prüft den Zustand für ein Jahr:
    - NO_SAISON: keine Saison in der Datenbank vorhanden
    - NO_GROUP: Saison existiert, aber keine Gruppen
    - SHOW_GROUP: es gibt Gruppen
    """
    import legacy_adapter

    saison = legacy_adapter.lade_saison(jahr)
    if saison is None:
        return "NO_SAISON", None

    if not saison.get("groups"):
        return "NO_GROUP", saison

    return "SHOW_GROUP", saison


def generiere_termine(start_iso: str, end_iso: str, wochentag_name: str) -> List[str]:
    """Alle Termine zwischen Start/Ende, die auf den Wochentag fallen (TT.MM.JJJJ)."""
    WTAG = {
        "Montag": 0, "Dienstag": 1, "Mittwoch": 2,
        "Donnerstag": 3, "Freitag": 4, "Samstag": 5, "Sonntag": 6
    }
    start_d = datetime.date.fromisoformat(start_iso)
    end_d = datetime.date.fromisoformat(end_iso)
    tag_idx = WTAG[wochentag_name]
    diff = (tag_idx - start_d.weekday()) % 7
    cur = start_d + datetime.timedelta(days=diff)
    out = []
    while cur <= end_d:
        out.append(cur.strftime("%d.%m.%Y"))
        cur += datetime.timedelta(days=7)
    return out