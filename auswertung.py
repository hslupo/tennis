"""
auswertung.py

Erstellt eine textliche Auswertung für eine Gruppe innerhalb einer Saison,
kopiert die Auswertung in die Zwischenablage und zeigt sie in einem Fenster an.

Exportierte Funktion:
- kopiere_auswertung(root, saison: dict, gruppe: dict, spieler_namen: dict)

Erwartete Formate:
- saison["start_date"], saison["end_date"] : ISO-Strings "YYYY-MM-DD"
- gruppe["wochentag"] : deutscher Wochentag ("Montag", "Dienstag", ...)
- gruppe["players"] : { pid: {"nicht_moeglich": ["DD.MM.YYYY", ...]}, ... }
- spieler_namen : dict id->vollerName
"""

import datetime
import json
from pathlib import Path
import tkinter as tk
from tkinter import messagebox, filedialog
from typing import List, Dict


def generiere_termine(start_iso: str, end_iso: str, wochentag_name: str) -> List[str]:
    """
    Alle Termine zwischen start_iso und end_iso, die auf wochentag_name fallen.
    Rückgabe: Liste von Strings im Format "TT.MM.JJJJ".
    Erwartet start_iso/end_iso im ISO-Format "YYYY-MM-DD".
    """
    WTAG = {
        "Montag": 0, "Dienstag": 1, "Mittwoch": 2,
        "Donnerstag": 3, "Freitag": 4, "Samstag": 5, "Sonntag": 6
    }
    if wochentag_name not in WTAG:
        return []

    start_d = datetime.date.fromisoformat(start_iso)
    end_d = datetime.date.fromisoformat(end_iso)
    tag_idx = WTAG[wochentag_name]
    diff = (tag_idx - start_d.weekday()) % 7
    cur = start_d + datetime.timedelta(days=diff)

    out: List[str] = []
    while cur <= end_d:
        out.append(cur.strftime("%d.%m.%Y"))
        cur += datetime.timedelta(days=7)
    return out


def _erstelle_text(saison: Dict, gruppe: Dict, spieler_namen: Dict) -> str:
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
    # Spieler-Abschnitt
    for pid, daten in gruppe.get("players", {}).items():
        name = spieler_namen.get(pid, pid)
        nm_list = daten.get("nicht_moeglich", []) or []
        nm = ", ".join(nm_list)
        lines.append(f"{name} ({pid}): {nm if nm else '—'}")

    lines.append("")  # Leerzeile
    lines.append("Termine → Verfügbare Spieler")

    # Termine generieren
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
            # Keiner kann
            lines.append(f"{t}: keiner kann")
        elif len(available) == len(alle_spieler):
            lines.append(f"{t}: alle können")
        else:
            lines.append(f"{t}: {', '.join(available)}")

    return "\n".join(lines)


def kopiere_auswertung(root: tk.Tk, saison: Dict, gruppe: Dict, spieler_namen: Dict):
    """
    Erstellt Auswertungstext, kopiert ihn in die Zwischenablage und zeigt ein Fenster mit dem Text.
    root: Haupt-Tkinter-Fenster (wird für Clipboard genutzt).
    """
    # Text erstellen
    text = _erstelle_text(saison, gruppe, spieler_namen)

    # In Zwischenablage schreiben
    try:
        root.clipboard_clear()
        root.clipboard_append(text)
        root.update()  # wichtig, damit Clipboard erhalten bleibt
    except Exception:
        # Fehler beim Clipboard nicht fatal - wir zeigen trotzdem das Fenster
        messagebox.showwarning("Zwischenablage", "Konnte Text nicht in die Zwischenablage schreiben.")

    # Fenster mit Text anzeigen
    win = tk.Toplevel(root)
    win.title("Auswertung")
    win.geometry("800x600")

    # Text-Widget
    txt = tk.Text(win, wrap="word")
    txt.pack(fill="both", expand=True, padx=8, pady=8)
    txt.insert("1.0", text)
    txt.configure(state="normal")  # erlaubt Kopieren/Markieren

    # Button-Frame
    btn_frame = tk.Frame(win)
    btn_frame.pack(fill="x", padx=8, pady=(0, 8))

    def _kopieren():
        try:
            root.clipboard_clear()
            root.clipboard_append(text)
            root.update()
            messagebox.showinfo("Kopiert", "Auswertung in die Zwischenablage kopiert.")
        except Exception:
            messagebox.showwarning("Fehler", "Kopieren in Zwischenablage fehlgeschlagen.")

    def _speichern():
        # Speicherdialog, Standard-Dateiname vorschlagen
        default_name = f"auswertung_{gruppe.get('wochentag','gruppe')}.txt"
        fp = filedialog.asksaveasfilename(parent=win, defaultextension=".txt",
                                          initialfile=default_name,
                                          filetypes=[("Textdatei", "*.txt"), ("Alle Dateien", "*.*")])
        if not fp:
            return
        try:
            Path(fp).write_text(text, encoding="utf-8")
            messagebox.showinfo("Gespeichert", f"Auswertung gespeichert: {fp}")
        except Exception as e:
            messagebox.showerror("Fehler", f"Speichern fehlgeschlagen:\n{e}")

    def _schliessen():
        win.destroy()

    tk.Button(btn_frame, text="Kopieren", command=_kopieren).pack(side="left", padx=4)
    tk.Button(btn_frame, text="Speichern...", command=_speichern).pack(side="left", padx=4)
    tk.Button(btn_frame, text="Schließen", command=_schliessen).pack(side="right", padx=4)

    # Focus auf Fenster, Modal-ähnlich (nicht strikt modal)
    win.transient(root)
    win.grab_set()
    win.focus_set()
