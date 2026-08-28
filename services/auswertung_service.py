"""Reine Textauswertung ohne UI-Abhängigkeiten (vorher in auswertung.py mit
tkinter/Clipboard-Code vermischt)."""

from collections import defaultdict
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

    lines.append("")
    lines.append("Spielerstatistik → Einsätze und gemeinsame Einsätze")
    gemeinsame_einsaetze = defaultdict(lambda: defaultdict(int))
    einsaetze = defaultdict(int)
    for spieler_ids in gruppe.get("verteilung", {}).values():
        eindeutige_spieler_ids = list(dict.fromkeys(spieler_ids))
        for pid in eindeutige_spieler_ids:
            einsaetze[pid] += 1
        for index, pid in enumerate(eindeutige_spieler_ids):
            for anderer_pid in eindeutige_spieler_ids[index + 1:]:
                gemeinsame_einsaetze[pid][anderer_pid] += 1
                gemeinsame_einsaetze[anderer_pid][pid] += 1

    for pid in alle_spieler:
        name = spieler_namen.get(pid, str(pid))
        mitspieler = [
            f"{spieler_namen.get(anderer_pid, anderer_pid)}: {anzahl}"
            for anderer_pid, anzahl in sorted(
                gemeinsame_einsaetze[pid].items(),
                key=lambda eintrag: str(spieler_namen.get(eintrag[0], eintrag[0])).lower(),
            )
        ]
        zusammen = ", ".join(mitspieler) if mitspieler else "keine"
        einsatz_text = "Einsatz" if einsaetze[pid] == 1 else "Einsätze"
        lines.append(f"{name}: {einsaetze[pid]} {einsatz_text}; zusammen mit {zusammen}")

    return "\n".join(lines)
