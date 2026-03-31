import tkinter as tk
from tkinter import messagebox
import datetime
import json
from pathlib import Path
from saison import Saison

def letzter_montag_september(jahr: int) -> datetime.date:
    datum = datetime.date(jahr, 9, 30)
    return datum - datetime.timedelta(days=(datum.weekday() - 0) % 7)

def letzter_sonntag_april(jahr: int) -> datetime.date:
    datum = datetime.date(jahr, 4, 30)
    return datum - datetime.timedelta(days=(datum.weekday() - 6) % 7)

class NeueSaisonDialog:
    def __init__(self, root, jahr: int):
        self.root = root
        self.jahr = jahr
        self.start_date = letzter_montag_september(jahr)
        self.end_date = letzter_sonntag_april(jahr + 1)

        frame = tk.Frame(root, padx=10, pady=10)
        frame.pack()

        self.start_var = tk.StringVar(value=str(self.start_date))
        tk.Label(frame, text="Startdatum:").grid(row=0, column=0)
        tk.Label(frame, textvariable=self.start_var).grid(row=0, column=1)
        tk.Button(frame, text="-1 Woche", command=lambda: self.shift("start", -7)).grid(row=0, column=2)
        tk.Button(frame, text="+1 Woche", command=lambda: self.shift("start", 7)).grid(row=0, column=3)

        self.end_var = tk.StringVar(value=str(self.end_date))
        tk.Label(frame, text="Enddatum:").grid(row=1, column=0)
        tk.Label(frame, textvariable=self.end_var).grid(row=1, column=1)
        tk.Button(frame, text="-1 Woche", command=lambda: self.shift("end", -7)).grid(row=1, column=2)
        tk.Button(frame, text="+1 Woche", command=lambda: self.shift("end", 7)).grid(row=1, column=3)

        tk.Button(frame, text="Neue Saison speichern", command=self.speichern).grid(row=2, column=0, columnspan=4, pady=10)

    def shift(self, feld, tage):
        import datetime
        if feld == "start":
            self.start_date += datetime.timedelta(days=tage)
            self.start_var.set(str(self.start_date))
        else:
            self.end_date += datetime.timedelta(days=tage)
            self.end_var.set(str(self.end_date))

    def speichern(self):
        s = {
            "jahr": self.jahr,
            "start_date": self.start_date.isoformat(),
            "end_date": self.end_date.isoformat(),
            "last_group": "",
            "groups": {}
        }
        Path(f"{self.jahr}.json").write_text(json.dumps(s, indent=2, ensure_ascii=False), encoding="utf-8")
        messagebox.showinfo("Gespeichert", f"Saison {self.jahr} gespeichert.")

        # Fenster schließen
        self.root.destroy()

        # Falls parent App ein refresh() hat → neu laden
        if hasattr(self.root.master, "refresh"):
            self.root.master.refresh()
