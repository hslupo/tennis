import tkinter as tk
from tkinter import messagebox

import legacy_adapter


class Tennisspieler:
    def __init__(self, root):
        self.root = root
        self.root.title("Spielerliste verwalten")

        # Daten laden
        self.spieler = legacy_adapter.spieler_alle()

        # GUI
        frame = tk.Frame(root, padx=10, pady=10)
        frame.pack(fill="both", expand=True)

        tk.Button(frame, text="Neuer Spieler", command=self.hinzufuegen).pack(anchor="w")

        # Liste
        self.listbox = tk.Listbox(frame, height=15, activestyle="dotbox")
        self.listbox.pack(fill="both", expand=True, pady=5)
        self.listbox.bind("<Double-Button-1>", self.bearbeiten)
        self.listbox.bind("<Button-3>", self.loeschen_rechtsklick)

        self.aktualisiere_liste()

    # --- GUI-Logik ---
    def aktualisiere_liste(self):
        self.spieler = legacy_adapter.spieler_alle()
        self.listbox.delete(0, tk.END)
        for sp in self.spieler:
            if sp["name"] and sp["name"] != sp["spitzname"]:
                text = f"{sp['spitzname']} ({sp['name']})"
            else:
                text = sp["spitzname"] or "(ohne Spitznamen)"
            self.listbox.insert(tk.END, text)

    def hinzufuegen(self):
        neue_id = legacy_adapter.spieler_erstellen(name="", spitzname="", telefon="", mobil="")
        self.aktualisiere_liste()
        neuer_spieler = next(sp for sp in self.spieler if sp["id"] == neue_id)
        self.bearbeiten_dialog(neuer_spieler)

    def bearbeiten(self, event):
        index = self.listbox.curselection()
        if not index:
            return
        spieler = self.spieler[index[0]]
        self.bearbeiten_dialog(spieler)

    def bearbeiten_dialog(self, spieler: dict):
        top = tk.Toplevel(self.root)
        top.title(f"Spieler bearbeiten")

        tk.Label(top, text="Vollständiger Name:").grid(row=0, column=0, sticky="w", padx=5, pady=3)
        name_entry = tk.Entry(top, width=30)
        name_entry.insert(0, spieler["name"])
        name_entry.grid(row=0, column=1, padx=5, pady=3)

        tk.Label(top, text="Spitzname:").grid(row=1, column=0, sticky="w", padx=5, pady=3)
        spitzname_entry = tk.Entry(top, width=30)
        spitzname_entry.insert(0, spieler["spitzname"])
        spitzname_entry.grid(row=1, column=1, padx=5, pady=3)

        tk.Label(top, text="Telefon:").grid(row=2, column=0, sticky="w", padx=5, pady=3)
        tel_entry = tk.Entry(top, width=30)
        tel_entry.insert(0, spieler["telefon"])
        tel_entry.grid(row=2, column=1, padx=5, pady=3)

        tk.Label(top, text="Mobil:").grid(row=3, column=0, sticky="w", padx=5, pady=3)
        mob_entry = tk.Entry(top, width=30)
        mob_entry.insert(0, spieler["mobil"])
        mob_entry.grid(row=3, column=1, padx=5, pady=3)

        def speichern_und_schliessen():
            spitzname = spitzname_entry.get().strip()
            if not spitzname:
                messagebox.showwarning("Fehler", "Bitte einen Spitznamen angeben.")
                return
            legacy_adapter.spieler_aktualisieren(
                spieler["id"],
                name=name_entry.get().strip(),
                spitzname=spitzname,
                telefon=tel_entry.get().strip(),
                mobil=mob_entry.get().strip(),
            )
            self.aktualisiere_liste()
            top.destroy()

        tk.Button(top, text="Speichern", command=speichern_und_schliessen).grid(row=4, column=0, columnspan=2, pady=8)

    def loeschen_rechtsklick(self, event):
        index = self.listbox.nearest(event.y)
        if index < 0 or index >= len(self.spieler):
            return
        spieler = self.spieler[index]
        anzeige = spieler["spitzname"] or spieler["name"] or f"#{spieler['id']}"
        if messagebox.askyesno(
            "Löschen",
            f"Soll Spieler '{anzeige}' wirklich gelöscht werden?\n"
            "Er wird dabei auch aus allen Gruppen entfernt.",
        ):
            legacy_adapter.spieler_loeschen(spieler["id"])
            self.aktualisiere_liste()


if __name__ == "__main__":
    root = tk.Tk()
    root.option_add("*Font", "Arial 12")
    root.minsize(500, 400)
    Tennisspieler(root)
    root.mainloop()
