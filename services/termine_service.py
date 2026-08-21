"""Einzige Implementierung der Terminberechnung (vorher unabhängig dupliziert
in tennisrunden_app.py, utils.py, auswertung.py und verteilen.py)."""

import datetime

WOCHENTAGE = {
    "Montag": 0, "Dienstag": 1, "Mittwoch": 2,
    "Donnerstag": 3, "Freitag": 4, "Samstag": 5, "Sonntag": 6,
}


def generiere_termine(start_iso: str, end_iso: str, wochentag_name: str) -> list[str]:
    """Alle Termine zwischen Start/Ende, die auf den Wochentag fallen (TT.MM.JJJJ)."""
    if wochentag_name not in WOCHENTAGE:
        return []

    start_d = datetime.date.fromisoformat(start_iso)
    end_d = datetime.date.fromisoformat(end_iso)
    tag_idx = WOCHENTAGE[wochentag_name]
    diff = (tag_idx - start_d.weekday()) % 7
    cur = start_d + datetime.timedelta(days=diff)
    out = []
    while cur <= end_d:
        out.append(cur.strftime("%d.%m.%Y"))
        cur += datetime.timedelta(days=7)
    return out
