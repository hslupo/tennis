# TennisrundeApp.py
import tkinter as tk
from tkinter import messagebox
from pathlib import Path
from tennis_model import Spieler, Saison, SaisonSpieler, save_json, load_json


class TennisRundenApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Tennis Runden App")

        # Datenhaltung
        self.spieler: list[Spieler] = []  # Stammdaten
        self.saison: Saison | None = None

        # GUI Layout
        frame = tk.Frame(root, padx=10, pady=10)
        frame.pack(fill=tk.BOTH, expand=True)

        self.name_label = tk.Label(frame, text="Spielername:")
        self.name_label.grid(row=0, column=0, sticky="w")

        self.name_entry = tk.Entry(frame)
        self.name_entry.grid(row=0, column=1, sticky="ew")

        self.add_button = tk.Button(frame, text="Hinzufügen", command=self.add_spieler)
        self.add_button.grid(row=0, column=2, padx=5)

        frame.columnconfigure(1, weight=1)

        self.spieler_listbox = tk.Listbox(frame, height=10)
        self.spieler_listbox.grid(row=1, column=0, columnspan=3, sticky="nsew", pady=5)

        frame.rowconfigure(1, weight=1)

        self.save_button = tk.Button(frame, text="Speichern", command=self.speichern)
        self.save_button.grid(row=2, column=0, pady=5)

        self.load_button = tk.Button(frame, text="Laden", command=self.laden)
        self.load_button.grid(row=2, column=1, pady=5)

        self.quit_button = tk.Button(frame, text="Beenden", command=root.quit)
        self.quit_button.grid(row=2, column=2, pady=5)

    # ---- Stammdaten Spieler ----
    def add_spieler(self):
        name = self.name_entry.get().strip()
        if not name:
            messagebox.showwarning("Warnung", "Bitte einen Spielernamen eingeben.")
            return

        if any(spieler.name == name for spieler in self.spieler):
            messagebox.showwarning("Warnung", "Spieler bereits vorhanden.")
            return

        spieler_id = name.lower()
        neuer_spieler = Spieler(spieler_id, name)
        self.spieler.append(neuer_spieler)
        self.spieler_listbox.insert(tk.END, name)
        self.name_entry.delete(0, tk.END)

    # ---- Saison speichern ----
    def speichern(self):
        if not self.spieler:
            messagebox.showwarning("Warnung", "Keine Spieler vorhanden zum Speichern.")
            return

        saison = Saison(
            jahr=2024,
            gruppe="Freitag",
            start_date="2024-10-04",
            end_date="2025-04-25",
            players=[SaisonSpieler(s.id, dummyname=s.name) for s in self.spieler],
        )

        save_json(Path("saison_freitag_2024.json"), saison.to_dict())
        save_json(Path("../spieler.json"), {"players": [s.to_dict() for s in self.spieler]})
        messagebox.showinfo("Info", "Daten gespeichert.")

    # ---- Saison laden ----
    def laden(self):
        path = Path("../spieler.json")
        if not path.exists():
            messagebox.showwarning("Warnung", "Keine gespeicherten Spieler gefunden.")
            return

        data = load_json(path)
        self.spieler = [Spieler.from_dict(p) for p in data["players"]]

        self.spieler_listbox.delete(0, tk.END)
        for s in self.spieler:
            self.spieler_listbox.insert(tk.END, s.name)

        messagebox.showinfo("Info", "Spieler geladen.")


if __name__ == "__main__":
    root = tk.Tk()
    app = TennisRundenApp(root)
    root.mainloop()
