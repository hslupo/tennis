import tkinter as tk
from tkinter import messagebox
import json
from pathlib import Path

# Hilfsfunktion Spieler laden
def lade_spieler() -> list[dict]:
    datei = Path("../spieler.json")
    if not datei.exists():
        return []
    return json.loads(datei.read_text(encoding="utf-8"))


class NeueGruppeDialog:
    def __init__(self, root, jahr: int):
        self.root = root
        self.jahr = jahr
        self.spieler = lade_spieler()
        self.selected = {}

        frame = tk.Frame(root, padx=10, pady=10)
        frame.pack(fill="both", expand=True)

        # --- Wochentag ---
        tk.Label(frame, text="Wochentag:").grid(row=0, column=0, sticky="w")
        self.wochentage = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"]
        self.wochentag_var = tk.StringVar(value=self.wochentage[0])
        tk.OptionMenu(frame, self.wochentag_var, *self.wochentage).grid(row=0, column=1, columnspan=2, sticky="ew")

        # --- Platz ---
        tk.Label(frame, text="Platz:").grid(row=1, column=0, sticky="w")
        self.platz_entry = tk.Entry(frame)
        self.platz_entry.grid(row=1, column=1, columnspan=2, sticky="ew")

        # --- Startzeit ---
        tk.Label(frame, text="Startzeit (HH:MM):").grid(row=2, column=0, sticky="w")
        self.startzeit_entry = tk.Entry(frame)
        self.startzeit_entry.insert(0, "18:00")
        self.startzeit_entry.grid(row=2, column=1, columnspan=2, sticky="ew")

        # --- Endzeit ---
        tk.Label(frame, text="Endzeit (HH:MM):").grid(row=3, column=0, sticky="w")
        self.endzeit_entry = tk.Entry(frame)
        self.endzeit_entry.insert(0, "20:00")
        self.endzeit_entry.grid(row=3, column=1, columnspan=2, sticky="ew")

        # --- Spieler-Auswahl ---
        row = 4
        tk.Label(frame, text="Spieler auswählen:").grid(row=row, column=0, sticky="w", pady=(10,0))
        row += 1
        for sp in self.spieler:
            var = tk.BooleanVar(value=False)
            chk = tk.Checkbutton(frame, text=f"{sp['name']} ({sp['id']})", variable=var, anchor="w", padx=5)
            chk.grid(row=row, column=0, columnspan=3, sticky="w")
            self.selected[sp["id"]] = var
            row += 1

        # --- Button ---
        tk.Button(frame, text="Gruppe speichern", command=self.speichern).grid(row=row, column=0, columnspan=3, pady=10)

    def speichern(self):
        wochentag = self.wochentag_var.get()
        platz = self.platz_entry.get().strip()
        startzeit = self.startzeit_entry.get().strip()
        endzeit = self.endzeit_entry.get().strip()

        ausgewaehlt = [sp_id for sp_id, var in self.selected.items() if var.get()]
        if len(ausgewaehlt) < 4:
            messagebox.showwarning("Warnung", "Mindestens 4 Spieler erforderlich.")
            return

        # players-Dict erzeugen
        players_dict = {sp_id: {"nicht_moeglich": []} for sp_id in ausgewaehlt}

        neue_gruppe = {
            "wochentag": wochentag,
            "platz": platz,
            "startzeit": startzeit,
            "endzeit": endzeit,
            "players": players_dict,
            "verteilung": {}
        }

        # Saison laden oder neu anlegen
        datei = Path(f"{self.jahr}.json")
        if datei.exists():
            saison = json.loads(datei.read_text(encoding="utf-8"))
        else:
            saison = {"jahr": self.jahr, "groups": []}

        saison["groups"].append(neue_gruppe)

        datei.write_text(json.dumps(saison, indent=2, ensure_ascii=False), encoding="utf-8")

        messagebox.showinfo("Gespeichert", f"Gruppe {wochentag} gespeichert.")
        self.root.destroy()


# --- Test ---
if __name__ == "__main__":
    root = tk.Tk()
    NeueGruppeDialog(root, 2024)
    root.mainloop()
