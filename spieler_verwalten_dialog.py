import tkinter as tk
from tkinter import messagebox, simpledialog

import legacy_adapter


class SpielerVerwaltenDialog:
    def __init__(self, root, jahr, wochentag_key, saison, spieler_namen, callback):
        self.root = root
        self.jahr = jahr
        self.wochentag_key = wochentag_key
        self.saison = saison
        self.spieler_namen = spieler_namen
        self.callback = callback

        self.root.title("Gruppenspieler verwalten")
        self.root.geometry("400x500")

        self.gruppe = self.saison["groups"][wochentag_key]

        # Liste aller Spieler laden (nach Namen sortiert)
        self.alle_spieler = sorted(
            spieler_namen.keys(),
            key=lambda pid: self.spieler_namen.get(pid, str(pid)).lower()
        )

        # UI aufbauen
        tk.Label(root, text=f"Gruppe {self.gruppe['wochentag']}",
                 font=("Arial", 12, "bold")).pack(pady=5)

        self.spieler_listbox = tk.Listbox(root, width=40, height=15)
        self.spieler_listbox.pack(padx=10, pady=10, fill="both", expand=True)
        self.spieler_listbox.bind("<Double-Button-1>", self.spitzname_anpassen)

        tk.Label(root, text="Doppelklick auf einen Spieler, um seinen Spitznamen\n"
                             "nur für diese Gruppe anzupassen.", fg="#555",
                 justify="left").pack(anchor="w", padx=10)

        self.refresh_list()

        btn_frame = tk.Frame(root)
        btn_frame.pack(fill="x", pady=10)

        tk.Button(btn_frame, text="Hinzufügen", command=self.hinzufuegen).pack(side="left", expand=True, padx=5)
        tk.Button(btn_frame, text="Löschen", command=self.loeschen).pack(side="right", expand=True, padx=5)

    def refresh_list(self):
        """Listbox mit Spielern der Gruppe füllen"""
        self.spieler_listbox.delete(0, tk.END)
        self._gruppen_spieler_ids = sorted(
            self.gruppe["players"].keys(),
            key=lambda pid: self.gruppe["players"][pid]["anzeige_name"].lower(),
        )
        for pid in self._gruppen_spieler_ids:
            self.spieler_listbox.insert(tk.END, self.gruppe["players"][pid]["anzeige_name"])

    def hinzufuegen(self):
        """Spieler aus Gesamtliste auswählen und hinzufügen"""
        verfuegbare_spieler = [pid for pid in self.alle_spieler if pid not in self.gruppe["players"]]
        if not verfuegbare_spieler:
            messagebox.showinfo("Hinweis", "Alle Spieler sind bereits in dieser Gruppe.")
            return

        auswahl = self.auswahl_dialog("Spieler hinzufügen", "Wähle einen Spieler:", verfuegbare_spieler)
        if not auswahl:
            return

        if auswahl in self.gruppe["players"]:
            messagebox.showwarning("Hinweis", "Dieser Spieler ist bereits in der Gruppe.")
            return

        # Spieler hinzufügen (anzeige_name als Platzhalter, wird beim Neuladen aus der DB ersetzt)
        self.gruppe["players"][auswahl] = {
            "nicht_moeglich": [],
            "anzeige_name": self.spieler_namen.get(auswahl, str(auswahl)),
            "spitzname_override": None,
        }
        self.speichern_und_neu_laden()
        self.callback()

    def loeschen(self):
        """Ausgewählten Spieler löschen (mit Nachfrage)"""
        auswahl = self.spieler_listbox.curselection()
        if not auswahl:
            messagebox.showwarning("Hinweis", "Bitte einen Spieler auswählen.")
            return

        pid = self._gruppen_spieler_ids[auswahl[0]]
        anzeige_name = self.gruppe["players"][pid]["anzeige_name"]

        if messagebox.askyesno("Bestätigen", f"Soll Spieler {anzeige_name} wirklich entfernt werden?"):
            del self.gruppe["players"][pid]
            self.speichern_und_neu_laden()
            self.callback()

    def spitzname_anpassen(self, event=None):
        """Spitzname nur für diese Gruppe überschreiben (z.B. zur Unterscheidung Gleichnamiger)."""
        auswahl = self.spieler_listbox.curselection()
        if not auswahl:
            return
        pid = self._gruppen_spieler_ids[auswahl[0]]
        eintrag = self.gruppe["players"][pid]
        global_spitzname = self.spieler_namen.get(pid, str(pid))

        neuer_wert = simpledialog.askstring(
            "Spitzname für diese Gruppe",
            f"Anzeigename in dieser Gruppe (leer = Standard '{global_spitzname}'):",
            initialvalue=eintrag.get("spitzname_override") or "",
            parent=self.root,
        )
        if neuer_wert is None:
            return  # abgebrochen

        eintrag["spitzname_override"] = neuer_wert.strip() or None
        self.speichern_und_neu_laden()
        self.callback()

    def speichern_und_neu_laden(self):
        """Saison speichern und anschließend frisch aus der DB laden (u.a. für aktuelle anzeige_name-Werte)."""
        legacy_adapter.speichere_saison(self.saison)
        self.saison = legacy_adapter.lade_saison(self.jahr)
        self.gruppe = self.saison["groups"][self.wochentag_key]
        self.refresh_list()

    def auswahl_dialog(self, title, prompt, items):
        """Einfaches Auswahl-Dialogfenster"""
        dlg = tk.Toplevel(self.root)
        dlg.title(title)
        dlg.grab_set()

        tk.Label(dlg, text=prompt).pack(pady=5)

        such_frame = tk.Frame(dlg)
        such_frame.pack(fill="x", padx=10)
        tk.Label(such_frame, text="Suche:").pack(side="left")

        such_var = tk.StringVar()
        such_entry = tk.Entry(such_frame, textvariable=such_var)
        such_entry.pack(side="left", fill="x", expand=True, padx=(6, 0))

        lb = tk.Listbox(dlg, width=30, height=15)
        lb.pack(padx=10, pady=10, fill="both", expand=True)

        selected = {"value": None}
        sichtbare_items = []

        def liste_aktualisieren(*_):
            suche = such_var.get().strip().lower()
            lb.delete(0, tk.END)
            sichtbare_items.clear()

            for item in items:
                name = self.spieler_namen.get(item, str(item))
                if suche and suche not in name.lower():
                    continue
                sichtbare_items.append(item)
                lb.insert(tk.END, name)

            if sichtbare_items:
                lb.selection_set(0)

        def ok(event=None):
            sel = lb.curselection()
            if sel:
                selected["value"] = sichtbare_items[sel[0]]
            dlg.destroy()

        def abbrechen(event=None):
            dlg.destroy()

        btn_frame = tk.Frame(dlg)
        btn_frame.pack(fill="x", padx=10, pady=(0, 8))

        tk.Button(btn_frame, text="OK", command=ok).pack(side="left")
        tk.Button(btn_frame, text="Abbrechen", command=abbrechen).pack(side="right")

        such_var.trace_add("write", liste_aktualisieren)
        lb.bind("<Double-Button-1>", ok)
        lb.bind("<Return>", ok)
        dlg.bind("<Escape>", abbrechen)

        liste_aktualisieren()
        such_entry.focus_set()

        dlg.wait_window()
        return selected["value"]
