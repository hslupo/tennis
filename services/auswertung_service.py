"""Reine Textauswertung ohne UI-Abhängigkeiten (vorher in auswertung.py mit
tkinter/Clipboard-Code vermischt)."""

from typing import Dict, List

from services.termine_service import generiere_termine


def erstelle_auswertungstext(saison: Dict, gruppe: Dict, spieler_namen: Dict) -> str:
    """
    Baut den Auswertungstext als string auf.
    Format:
      Spieler → Nicht mögliche Termine
      Name (id): TT.MM.JJJJ, ...
      ...
      (leerzeile)
      Termine → Verfügbare Spieler
      TT.MM.JJJJ: alle können
      TT.MM.JJJJ: id1, id2
    """
    lines: List[str] = []
    lines.append("Spieler → Nicht mögliche Termine")
    for pid, daten in gruppe.get("players", {}).items():
        name = spieler_namen.get(pid, str(pid))
        nm_list = daten.get("nicht_moeglich", []) or []
        nm = ", ".join(nm_list)
        lines.append(f"{name}: {nm if nm else '—'}")

    lines.append("")
    lines.append("Termine → Verfügbare Spieler")

    start = saison.get("start_date", "")
    end = saison.get("end_date", "")
    if not start or not end:
        lines.append("Keine Saison-Daten (start/end) vorhanden.")
        return "\n".join(lines)

    termine = generiere_termine(start, end, gruppe.get("wochentag", ""))
    alle_spieler = list(gruppe.get("players", {}).keys())

    for t in termine:
        available = [pid for pid, d in gruppe.get("players", {}).items() if t not in d.get("nicht_moeglich", [])]
        if len(available) == 0:
            lines.append(f"{t}: keiner kann")
        elif len(available) == len(alle_spieler):
            lines.append(f"{t}: alle können")
        else:
            namen = [str(spieler_namen.get(pid, pid)) for pid in available]
            lines.append(f"{t}: {', '.join(namen)}")

    return "\n".join(lines)
