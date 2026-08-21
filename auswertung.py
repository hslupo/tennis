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

from pathlib import Path
import tkinter as tk
from tkinter import messagebox, filedialog
from typing import Dict

from services.auswertung_service import erstelle_auswertungstext


def kopiere_auswertung(root: tk.Tk, saison: Dict, gruppe: Dict, spieler_namen: Dict):
    """
    Erstellt Auswertungstext, kopiert ihn in die Zwischenablage und zeigt ein Fenster mit dem Text.
    root: Haupt-Tkinter-Fenster (wird für Clipboard genutzt).
    """
    # Text erstellen
    text = erstelle_auswertungstext(saison, gruppe, spieler_namen)

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
