import tkinter as tk
from tkinter import messagebox
import datetime
import json
from pathlib import Path

from tennisspieler import Tennisspieler
from neue_saison_dialog import NeueSaisonDialog
from neue_gruppe_dialog import NeueGruppeDialog
from utils import ermittle_state

WOCHENTAGE = [
    "Montag", "Dienstag", "Mittwoch",
    "Donnerstag", "Freitag", "Samstag", "Sonntag"
]


def generiere_termine(start_iso: str, end_iso: str, wochentag_name: str) -> list[str]:
    """Alle Termine zwischen Start/Ende, die auf den Wochentag fallen (TT.MM.JJJJ)."""
    WTAG = {"Montag": 0, "Dienstag": 1, "Mittwoch": 2,
            "Donnerstag": 3, "Freitag": 4, "Samstag": 5, "Sonntag": 6}
    start_d = datetime.date.fromisoformat(start_iso)
    end_d = datetime.date.fromisoformat(end_iso)
    tag_idx = WTAG[wochentag_name]
    diff = (tag_idx - start_d.weekday()) % 7
    cur = start_d + datetime.timedelta(days=diff)
    out = []
    while cur <= end_d:
        out.append(cur.strftime("%d.%m.%Y"))
        cur += datetime.timedelta(days=7)
    return out


class TennisRundenApp:
    def __init__(self, root):
        self.root = root
        self.jahr = datetime.date.today().year
        self.spieler_namen = self.lade_spieler_namen()

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

    def lade_spieler_namen(self) -> dict:
        """Lädt spieler.json und gibt dict id->name zurück."""
        try:
            data = json.loads(Path("spieler.json").read_text(encoding="utf-8"))
            return {sp["id"]: sp["name"] for sp in data}
        except Exception:
            return {}

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

        # last_group speichern
        if saison.get("last_group") != wochentag_key:
            saison["last_group"] = wochentag_key
            Path(f"{self.jahr}.json").write_text(json.dumps(saison, indent=2, ensure_ascii=False), encoding="utf-8")

        # Spieler eintragen mit Namen
        for pid in gruppe["players"].keys():
            name = self.spieler_namen.get(pid, pid)
            self.spieler_listbox.insert(tk.END, f"{name} ({pid})")

        self.spieler_listbox.bind("<<ListboxSelect>>", self.spieler_gewaehlt)

        if gruppe["players"]:
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
        eintrag = self.spieler_listbox.get(auswahl[0])
        pid = eintrag.split("(")[-1].rstrip(")")

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
        Path(f"{self.jahr}.json").write_text(json.dumps(self.saison, indent=2, ensure_ascii=False), encoding="utf-8")


    def spieler_verwalten(self):
        from spieler_verwalten_dialog import SpielerVerwaltenDialog
        top = tk.Toplevel(self.root)

        def on_change():
            # JSON neu laden und Gruppe anzeigen
            datei = Path(f"{self.jahr}.json")
            if datei.exists():
                self.saison = json.loads(datei.read_text(encoding="utf-8"))
                self.zeige_gruppe(self.wochentag_key, self.saison)

        SpielerVerwaltenDialog(top, self.jahr, self.wochentag_key, self.saison, self.spieler_namen, on_change)

        # falls Fenster einfach geschlossen wird → Refresh ebenfalls
        top.protocol("WM_DELETE_WINDOW", on_change)

    def auswertung_anzeigen(self):
        from auswertung import kopiere_auswertung
        gruppe = self.saison["groups"][self.wochentag_key]
        kopiere_auswertung(self.root, self.saison, gruppe, self.spieler_namen)


if __name__ == "__main__":
    root = tk.Tk()
    root.title("Tennisrunden Verwaltung")
    root.geometry("1000x700")
    app = TennisRundenApp(root)
    root.mainloop()
