import tkinter as tk
from tkinter import messagebox
import json
from pathlib import Path


class NeueGruppeDialog:
    def __init__(self, root, jahr: int, wochentag: str):
        self.root = root
        self.jahr = jahr
        self.wochentag = wochentag.lower()  # key im JSON klein
        self.anzeige_wochentag = wochentag  # Klartext

        root.title(f"Neue Gruppe anlegen – {wochentag}")

        tk.Label(root, text=f"Wochentag: {self.anzeige_wochentag}",
                 font=("Arial", 12, "bold")).pack(pady=(5, 10))

        frm = tk.Frame(root)
        frm.pack(padx=10, pady=10)

        # Platz
        tk.Label(frm, text="Platz:").grid(row=0, column=0, sticky="e", padx=5, pady=3)
        self.platz_entry = tk.Entry(frm, width=20)
        self.platz_entry.grid(row=0, column=1, padx=5, pady=3)
        self.platz_entry.insert(0, "1")

        # Startzeit
        tk.Label(frm, text="Startzeit (HH:MM):").grid(row=1, column=0, sticky="e", padx=5, pady=3)
        self.startzeit_entry = tk.Entry(frm, width=20)
        self.startzeit_entry.grid(row=1, column=1, padx=5, pady=3)
        self.startzeit_entry.insert(0, "18:00")

        # Endzeit
        tk.Label(frm, text="Endzeit (HH:MM):").grid(row=2, column=0, sticky="e", padx=5, pady=3)
        self.endzeit_entry = tk.Entry(frm, width=20)
        self.endzeit_entry.grid(row=2, column=1, padx=5, pady=3)
        self.endzeit_entry.insert(0, "20:00")

        # Buttons
        tk.Button(root, text="Speichern", command=self.speichern).pack(pady=10)
        tk.Button(root, text="Abbrechen", command=root.destroy).pack()

    def speichern(self):
        platz = self.platz_entry.get().strip()
        startzeit = self.startzeit_entry.get().strip()
        endzeit = self.endzeit_entry.get().strip()

        if not platz or not startzeit or not endzeit:
            messagebox.showwarning("Fehler", "Bitte alle Felder ausfüllen.")
            return

        datei = Path(f"{self.jahr}.json")
        if not datei.exists():
            messagebox.showerror("Fehler", f"Saison-Datei {self.jahr}.json nicht gefunden!")
            return

        saison = json.loads(datei.read_text(encoding="utf-8"))

        # Neue Gruppe einfügen oder überschreiben
        saison["groups"][self.wochentag] = {
            "wochentag": self.anzeige_wochentag,
            "platz": platz,
            "startzeit": startzeit,
            "endzeit": endzeit,
            "players": {},  # leer
            "verteilung": {}
        }

        # last_group auf diese setzen
        saison["last_group"] = self.wochentag

        datei.write_text(json.dumps(saison, indent=2, ensure_ascii=False), encoding="utf-8")

        messagebox.showinfo("Gespeichert", f"Gruppe {self.anzeige_wochentag} wurde gespeichert.")
        self.root.destroy()
