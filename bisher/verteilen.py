# verteilen.py
import os
import sys
import tkinter as tk
from tkinter import messagebox

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import legacy_adapter
from services.verteilung_service import plane_verteilung, verteile_gruppe


class PlanungsDialog:
    def __init__(self, root, gruppe, saison):
        self.root = root
        self.gruppe = gruppe
        self.saison = saison
        self.root.title("Planungsmodus")

        seeds = (2, 7, 9, 16, 54, 61)
        termine, vorschlaege = plane_verteilung(gruppe, saison, seeds)

        # Tabelle
        header = tk.Frame(root)
        header.pack(fill="x")
        tk.Label(header, text="Termin", width=12, relief="solid").pack(side="left")
        for s in seeds:
            tk.Label(header, text=f"Seed {s}", width=25, relief="solid").pack(side="left")

        for termin in termine:
            row = tk.Frame(root)
            row.pack(fill="x")
            tk.Label(row, text=termin, width=12, relief="solid").pack(side="left")
            for s in seeds:
                text = ", ".join(str(sp) for sp in vorschlaege[s][termin])
                tk.Label(row, text=text, width=25, relief="solid", anchor="w").pack(side="left")

        # Auswahl
        self.var = tk.IntVar(value=seeds[0])
        for s in seeds:
            tk.Radiobutton(root, text=f"Seed {s}", variable=self.var, value=s).pack(anchor="w")

        tk.Button(root, text="Seed übernehmen", command=self.save_seed).pack(pady=10)

    def save_seed(self):
        chosen_seed = self.var.get()

        verteilung = verteile_gruppe(
            self.gruppe,
            self.saison["start_date"],
            self.saison["end_date"],
            seed=chosen_seed,
        )

        self.gruppe["seed"] = chosen_seed
        self.gruppe["verteilung"] = verteilung
        wochentag_key = self.gruppe["wochentag"].lower()
        self.saison["groups"][wochentag_key] = self.gruppe

        legacy_adapter.speichere_saison(self.saison)

        messagebox.showinfo(
            "Gespeichert",
            f"Seed {chosen_seed} wurde übernommen und Verteilung gespeichert."
        )
        self.root.destroy()


if __name__ == "__main__":
    # Test: Gruppe Freitag aus der Saison 2025 laden
    saison = legacy_adapter.lade_saison(2025)
    if saison is None or "freitag" not in saison["groups"]:
        print("⚠️ Saison 2025 / Gruppe 'freitag' nicht gefunden")
    else:
        gruppe = saison["groups"]["freitag"]

        # root = tk.Tk()
        # PlanungsDialog(root, gruppe, saison)
        # root.mainloop()
        verteilung = gruppe["verteilung"]
        for termin, spieler in verteilung.items():
            print(f"{termin}: {', '.join(str(s) for s in sorted(spieler))}")

        print("\nTermine mit Spielern die nicht können")

        for termin, liste in gruppe["players"].items():
            print(f"{termin}: {', '.join(liste['nicht_moeglich'])}")

        print("\nZusätzliche Statistiken:")
        print(f"Gesamtzahl der Termine: {len(verteilung)}")
        print(
            f"Durchschnittliche Anzahl von Spielern pro Termin: {sum(len(sl) for sl in verteilung.values()) / len(verteilung):.2f}")
