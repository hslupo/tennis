import os
import sys
import tkinter as tk
from tkinter import messagebox
import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import legacy_adapter
from tennisspieler import Tennisspieler
from neue_saison_dialog import NeueSaisonDialog
from neue_gruppe_dialog import NeueGruppeDialog
from utils import ermittle_state
from services.termine_service import generiere_termine

WOCHENTAGE = [
    "Montag", "Dienstag", "Mittwoch",
    "Donnerstag", "Freitag", "Samstag", "Sonntag"
]


class TennisRundenApp:
    def __init__(self, root):
        self.root = root
        self.jahr = datetime.date.today().year
        self.spieler_namen = legacy_adapter.lade_spieler_namen()

        container = tk.Frame(root)
        container.pack(fill="both", expand=True)

        # Linkes Menü
        self.menu_frame = tk.Frame(container, width=220, bg="#f0f0f0", padx=5, pady=5)
        self.menu_frame.pack(side="left", fill="y")

        # Hauptbereich
        self.main_frame = tk.Frame(container, padx=10, pady=10)
        self.main_frame.pack(side="right", fill="both", expand=True)

        # Menü aufbauen
        self.baue_menue()

        # Inhalt anzeigen
        self.refresh()

    def baue_menue(self):
        tk.Label(self.menu_frame, text="Verwalten", bg="#f0f0f0",
                 font=("Arial", 12, "bold")).pack(anchor="w", pady=(0, 10))

        tk.Button(self.menu_frame, text="Spieler", width=20,
                  command=self.oeffne_spielerliste).pack(anchor="w", pady=2)

        tk.Label(self.menu_frame, text="Gruppen:", bg="#f0f0f0",
                 font=("Arial", 11, "bold")).pack(anchor="w", pady=(15, 2))

        self.gruppen_listbox = tk.Listbox(self.menu_frame, height=7)
        self.gruppen_listbox.pack(fill="x", pady=2)

        self.btn_gruppe_neu = tk.Button(self.menu_frame, text="Gruppe NEU",
                                        command=self.neue_gruppe)
        self.btn_gruppe_neu.pack(fill="x", pady=(5, 10))

        tk.Button(self.menu_frame, text="Saison", width=20,
                  command=self.oeffne_saisons).pack(anchor="w", pady=2)

    def refresh(self):
        for w in self.main_frame.winfo_children():
            w.destroy()

        state, saison = ermittle_state(self.jahr)

        # Menü-Liste aktualisieren
        self.gruppen_listbox.delete(0, tk.END)
        if state == "NO_SAISON":
            self.gruppen_listbox.configure(state="disabled")
            self.btn_gruppe_neu.configure(state="disabled")
        else:
            self.gruppen_listbox.configure(state="normal")
            self.btn_gruppe_neu.configure(state="normal")

        vorhandene_keys = []
        if saison and "groups" in saison:
            vorhandene_keys = list(saison["groups"].keys())

        for tag in WOCHENTAGE:
            if tag.lower() not in vorhandene_keys:
                self.gruppen_listbox.insert(tk.END, tag)

        # Hauptbereich
        if state == "NO_SAISON":
            tk.Label(self.main_frame, text="Noch keine Saison angelegt").pack(anchor="w", pady=(0, 8))
            return
        if state == "NO_GROUP":
            tk.Label(self.main_frame, text="Noch keine Gruppen vorhanden").pack(anchor="w", pady=(0, 8))
            return

        # SHOW_GROUP
        key = saison.get("last_group") or (vorhandene_keys[0] if vorhandene_keys else "")
        if key and key in saison["groups"]:
            self.zeige_gruppe(key, saison)
        else:
            tk.Label(self.main_frame, text="Keine Gruppen vorhanden").pack(anchor="w", pady=(0, 8))

    def oeffne_spielerliste(self):
        top = tk.Toplevel(self.root)
        Tennisspieler(top)
        top.protocol("WM_DELETE_WINDOW", lambda: (self._spieler_namen_neu_laden(), top.destroy()))

    def _spieler_namen_neu_laden(self):
        self.spieler_namen = legacy_adapter.lade_spieler_namen()

    def neue_gruppe(self):
        auswahl = self.gruppen_listbox.curselection()
        if not auswahl:
            messagebox.showwarning("Hinweis", "Bitte zuerst einen Wochentag aus der Liste auswählen.")
            return
        tag = self.gruppen_listbox.get(auswahl[0])
        top = tk.Toplevel(self.root)
        NeueGruppeDialog(top, self.jahr, tag)
        top.protocol("WM_DELETE_WINDOW", self.refresh)

    def oeffne_saisons(self):
        top = tk.Toplevel(self.root)
        NeueSaisonDialog(top, self.jahr)
        top.protocol("WM_DELETE_WINDOW", self.refresh)

    def zeige_gruppe(self, wochentag_key: str, saison: dict):
        for w in self.main_frame.winfo_children():
            w.destroy()

        gruppe = saison["groups"][wochentag_key]

        # Dropdown
        keys = list(saison["groups"].keys())
        display_names = [saison["groups"][k]["wochentag"] for k in keys]
        self._anzeige2key = {saison["groups"][k]["wochentag"]: k for k in keys}
        auswahl_var = tk.StringVar(value=gruppe["wochentag"])
        optionen = display_names + ["* neue Gruppe *"]
        tk.OptionMenu(self.main_frame, auswahl_var, *optionen,
                      command=lambda val: self.gruppen_wechsel(val, saison)).pack(anchor="w")

        # Platz/Uhrzeit
        tk.Label(self.main_frame,
                 text=f"Platz {gruppe['platz']} – {gruppe['startzeit']} bis {gruppe['endzeit']}",
                 font=("Arial", 12, "bold")).pack(anchor="w", pady=(5, 10))

        container = tk.Frame(self.main_frame)
        container.pack(fill="both", expand=True)

        # Spielerbereich links mit Buttons
        links = tk.Frame(container)
        links.pack(side="left", fill="y", padx=6, pady=6)

        self.spieler_listbox = tk.Listbox(links, width=28, height=10)
        self.spieler_listbox.pack(fill="y", pady=(0, 6))

        tk.Button(links, text="Spieler verwalten", command=self.spieler_verwalten).pack(fill="x", pady=2)
        tk.Button(links, text="Auswertung", command=self.auswertung_anzeigen).pack(fill="x", pady=(10, 2))

        # Termine rechts
        self.termine_frame = tk.Frame(container)
        self.termine_frame.pack(side="right", fill="both", expand=True, padx=6, pady=6)

        self.saison = saison
        self.wochentag_key = wochentag_key

        # last_group merken
        if saison.get("last_group") != wochentag_key:
            saison["last_group"] = wochentag_key
            legacy_adapter.set_last_group(self.jahr, wochentag_key)

        # Spieler eintragen, sortiert nach effektivem Anzeigenamen; Reihenfolge merken
        # für die Zuordnung Listbox-Index -> Spieler-ID (kein Text-Parsing mehr nötig).
        self._gruppen_spieler_ids = sorted(
            gruppe["players"].keys(),
            key=lambda pid: gruppe["players"][pid]["anzeige_name"].lower(),
        )
        for pid in self._gruppen_spieler_ids:
            self.spieler_listbox.insert(tk.END, gruppe["players"][pid]["anzeige_name"])

        self.spieler_listbox.bind("<<ListboxSelect>>", self.spieler_gewaehlt)

        if self._gruppen_spieler_ids:
            self.spieler_listbox.selection_set(0)
            self.spieler_gewaehlt()

    def gruppen_wechsel(self, val, saison):
        if val == "* neue Gruppe *":
            messagebox.showinfo("Neue Gruppe", "Bitte im linken Menü 'Gruppe NEU' anlegen.")
            return
        key = self._anzeige2key.get(val)
        if key:
            self.zeige_gruppe(key, saison)

    def spieler_gewaehlt(self, event=None):
        auswahl = self.spieler_listbox.curselection()
        if not auswahl:
            return
        pid = self._gruppen_spieler_ids[auswahl[0]]

        for w in self.termine_frame.winfo_children():
            w.destroy()

        gruppe = self.saison["groups"][self.wochentag_key]
        nm_liste = gruppe["players"][pid]["nicht_moeglich"]
        termine = generiere_termine(self.saison["start_date"], self.saison["end_date"], gruppe["wochentag"])

        # Termine nach Jahr gruppieren
        jahre = {}
        for t in termine:
            jahr = t.split(".")[2]
            jahre.setdefault(jahr, []).append(t)

        frame_spalten = tk.Frame(self.termine_frame)
        frame_spalten.pack(fill="both", expand=True)

        for jahr, liste in sorted(jahre.items()):
            col = tk.Frame(frame_spalten, padx=10)
            col.pack(side="left", fill="y")

            tk.Label(col, text=jahr, font=("Arial", 11, "bold")).pack(anchor="w")

            for t in liste:
                var = tk.BooleanVar(value=t in nm_liste)
                cb = tk.Checkbutton(col, text=t, variable=var,
                                    command=lambda tt=t, v=var, player=pid: self.toggle_termin(player, tt, v))
                cb.pack(anchor="w")

    def toggle_termin(self, spieler_id, termin, var):
        nm = self.saison["groups"][self.wochentag_key]["players"][spieler_id]["nicht_moeglich"]
        if var.get():
            if termin not in nm:
                nm.append(termin)
        else:
            if termin in nm:
                nm.remove(termin)
        legacy_adapter.speichere_saison(self.saison)

    def spieler_verwalten(self):
        from spieler_verwalten_dialog import SpielerVerwaltenDialog
        top = tk.Toplevel(self.root)

        def on_change():
            self.saison = legacy_adapter.lade_saison(self.jahr)
            self.zeige_gruppe(self.wochentag_key, self.saison)

        SpielerVerwaltenDialog(top, self.jahr, self.wochentag_key, self.saison, self.spieler_namen, on_change)

        # falls Fenster einfach geschlossen wird → Refresh ebenfalls
        top.protocol("WM_DELETE_WINDOW", on_change)

    def auswertung_anzeigen(self):
        from auswertung import kopiere_auswertung
        gruppe = self.saison["groups"][self.wochentag_key]
        anzeige_namen = {pid: eintrag["anzeige_name"] for pid, eintrag in gruppe["players"].items()}
        kopiere_auswertung(self.root, self.saison, gruppe, anzeige_namen)


if __name__ == "__main__":
    root = tk.Tk()
    root.title("Tennisrunden Verwaltung")
    root.geometry("1000x700")
    app = TennisRundenApp(root)
    root.mainloop()
