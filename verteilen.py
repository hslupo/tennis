# verteilen.py
import json
import random
from collections import defaultdict
from pathlib import Path
import tkinter as tk
from tkinter import messagebox
from utils import generiere_termine


def verteile_gruppe(
    gruppe: dict,
    start_date: str,
    end_date: str,
    *,
    ausgeschlossene_paarungen=None,
    spieler_pro_termin=4,
    bestehende_verteilung=None,
    ab_datum=None,
    neue_termine=0,
    seed=None,
    write_back=True
):
    """Verteilt Spieler auf Termine für eine Gruppe"""

    if ausgeschlossene_paarungen is None:
        ausgeschlossene_paarungen = set()
    else:
        ausgeschlossene_paarungen = set(tuple(sorted(paar)) for paar in ausgeschlossene_paarungen)

    termine = generiere_termine(start_date, end_date, gruppe["wochentag"])
    if neue_termine and neue_termine > 0:
        termine = termine[:neue_termine]

    ergebnis = {termin: [] for termin in termine}
    spieler_einsaetze = {s: 0 for s in gruppe["players"].keys()}
    paarungen = defaultdict(lambda: defaultdict(int))
    verpasst = {s: 0 for s in gruppe["players"].keys()}

    if seed is not None:
        random.seed(seed)

    def bewerte_spieler(kandidat, bereits_ausgewaehlt):
        einsatz_score = spieler_einsaetze[kandidat]
        paarung_score = sum(paarungen[kandidat][s] for s in bereits_ausgewaehlt)
        verpasst_score = -verpasst[kandidat]
        return (einsatz_score, paarung_score, verpasst_score)

    def ist_erlaubte_paarung(spieler1, spieler2):
        return tuple(sorted([spieler1, spieler2])) not in ausgeschlossene_paarungen

    for termin in termine:
        verfuegbare_spieler = [
            s for s in gruppe["players"].keys()
            if termin not in gruppe["players"][s].get("nicht_moeglich", [])
        ]
        ausgewaehlte_spieler = []

        while len(ausgewaehlte_spieler) < spieler_pro_termin and verfuegbare_spieler:
            erlaubte_kandidaten = [
                s for s in verfuegbare_spieler
                if all(ist_erlaubte_paarung(s, a) for a in ausgewaehlte_spieler)
            ]
            if not erlaubte_kandidaten:
                break

            kandidaten = sorted(erlaubte_kandidaten, key=lambda s: bewerte_spieler(s, ausgewaehlte_spieler))
            min_score = bewerte_spieler(kandidaten[0], ausgewaehlte_spieler)
            beste_kandidaten = [s for s in kandidaten if bewerte_spieler(s, ausgewaehlte_spieler) == min_score]

            gewaehlter = random.choice(beste_kandidaten)
            ausgewaehlte_spieler.append(gewaehlter)
            verfuegbare_spieler.remove(gewaehlter)

        ergebnis[termin] = ausgewaehlte_spieler

        for s in gruppe["players"].keys():
            if s in ausgewaehlte_spieler:
                spieler_einsaetze[s] += 1
                verpasst[s] = 0
                for other in ausgewaehlte_spieler:
                    if s != other:
                        paarungen[s][other] += 1
            else:
                verpasst[s] += 1

    if write_back:
        dateiname = Path(f"{start_date[:4]}.json")
        if dateiname.exists():
            data = json.loads(dateiname.read_text(encoding="utf-8"))
            if "groups" in data and gruppe["wochentag"].lower() in data["groups"]:
                data["groups"][gruppe["wochentag"].lower()]["verteilung"] = ergebnis
            dateiname.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    return ergebnis


def plane_verteilung(gruppe, saison, seeds=(9, 16, 54, 61)):
    start, ende = saison["start_date"], saison["end_date"]
    termine = generiere_termine(start, ende, gruppe["wochentag"])[:4]

    vorschlaege = {}
    for seed in seeds:
        v = verteile_gruppe(
            gruppe, start, ende,
            neue_termine=4, seed=seed, write_back=False
        )
        vorschlaege[seed] = v
    return termine, vorschlaege


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
                text = ", ".join(vorschlaege[s][termin])
                tk.Label(row, text=text, width=25, relief="solid", anchor="w").pack(side="left")

        # Auswahl
        self.var = tk.IntVar(value=seeds[0])
        for s in seeds:
            tk.Radiobutton(root, text=f"Seed {s}", variable=self.var, value=s).pack(anchor="w")

        tk.Button(root, text="Seed übernehmen", command=self.save_seed).pack(pady=10)

    def save_seed(self):
        chosen_seed = self.var.get()
        self.gruppe["seed"] = chosen_seed

        # Verteilung komplett neu rechnen
        verteilung = verteile_gruppe(
            self.gruppe,
            self.saison["start_date"],
            self.saison["end_date"],
            seed=chosen_seed,
            write_back=False
        )

        jahr = self.saison["start_date"][:4]
        datei = Path(f"{jahr}.json")
        if datei.exists():
            data = json.loads(datei.read_text(encoding="utf-8"))
            grp = data["groups"][self.gruppe["wochentag"].lower()]
            grp["seed"] = chosen_seed
            grp["verteilung"] = verteilung
            datei.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

            messagebox.showinfo(
                "Gespeichert",
                f"Seed {chosen_seed} wurde übernommen und Verteilung gespeichert."
            )
            self.root.destroy()


if __name__ == "__main__":
    # Test: Gruppe Freitag aus 2025.json laden
    datei = Path("2025.json")
    if not datei.exists():
        print("⚠️ 2025.json nicht gefunden")
    else:
        saison = json.loads(datei.read_text(encoding="utf-8"))
        gruppe = saison["groups"]["freitag"]

        # root = tk.Tk()
        # PlanungsDialog(root, gruppe, saison)
        # root.mainloop()
        verteilung = gruppe["verteilung"]
        for termin, spieler in verteilung.items():
            print(f"{termin}: {', '.join(sorted(spieler))}")

        print("\nTermine mit Spielern die nicht können")

        for termin, liste in gruppe["players"].items():
            print(f"{termin}: {', '.join(liste['nicht_moeglich'])}")

        # Analyse der Verteilung und Paarungen
        # analysiere_verteilung(verteilung, paarungen, ausgeschlossene_paarungen)

        # Zusätzliche Statistiken
        print("\nZusätzliche Statistiken:")
        print(f"Gesamtzahl der Termine: {len(verteilung)}")
        print(
            f"Durchschnittliche Anzahl von Spielern pro Termin: {sum(len(sl) for sl in verteilung.values()) / len(verteilung):.2f}")
        #print(f"Termine mit weniger als {spieler_pro_termin} Spielern: {sum(1 for sl in verteilung.values() if len(sl) < spieler_pro_termin)}")
