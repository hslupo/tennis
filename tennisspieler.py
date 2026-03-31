import tkinter as tk
from tkinter import messagebox, simpledialog
import json
from pathlib import Path


DATEI = Path("spieler.json")


def lade_spieler() -> list[dict]:
    if not DATEI.exists():
        return []
    return json.loads(DATEI.read_text(encoding="utf-8"))


def speichere_spieler(spieler: list[dict]):
    DATEI.write_text(json.dumps(spieler, indent=2, ensure_ascii=False), encoding="utf-8")


class Tennisspieler:
    def __init__(self, root):
        self.root = root
        self.root.title("Spielerliste verwalten")

        # Daten laden
        self.spieler = lade_spieler()

        # GUI
        frame = tk.Frame(root, padx=10, pady=10)
        frame.pack(fill="both", expand=True)

        # ID-Eingabe
        tk.Label(frame, text="Spieler-ID (Rufname):").grid(row=0, column=0, sticky="w")
        self.id_entry = tk.Entry(frame)
        self.id_entry.grid(row=0, column=1, sticky="ew")
        tk.Button(frame, text="Hinzufügen", command=self.hinzufuegen).grid(row=0, column=2, padx=5)

        # Liste
        self.listbox = tk.Listbox(frame, height=15, activestyle="dotbox")
        self.listbox.grid(row=1, column=0, columnspan=3, sticky="nsew", pady=5, padx=(2,2))
        self.listbox.bind("<Double-Button-1>", self.bearbeiten)
        self.listbox.bind("<Button-3>", self.loeschen_rechtsklick)

        frame.columnconfigure(1, weight=1)
        frame.rowconfigure(1, weight=1)

        self.aktualisiere_liste()

    # --- GUI-Logik ---
    def aktualisiere_liste(self):
        self.listbox.delete(0, tk.END)
        for sp in sorted(self.spieler, key=lambda x: x["id"].lower()):
            self.listbox.insert(tk.END, f"{sp['id']} - {sp['name']}")

    def hinzufuegen(self):
        sp_id = self.id_entry.get().strip()
        if not sp_id:
            messagebox.showwarning("Fehler", "Bitte eine Spieler-ID eingeben.")
            return
        if any(sp["id"] == sp_id for sp in self.spieler):
            messagebox.showwarning("Fehler", f"Spieler-ID '{sp_id}' existiert bereits.")
            return

        neuer_spieler = {"id": sp_id, "name": "", "telefon": "", "mobil": ""}
        self.spieler.append(neuer_spieler)
        self.speichern()
        self.id_entry.delete(0, tk.END)
        self.bearbeiten_dialog(neuer_spieler)

    def bearbeiten(self, event):
        index = self.listbox.curselection()
        if not index:
            return
        sp_id = self.listbox.get(index[0]).split(" - ")[0]
        spieler = next(sp for sp in self.spieler if sp["id"] == sp_id)
        self.bearbeiten_dialog(spieler)

    def bearbeiten_dialog(self, spieler: dict):
        top = tk.Toplevel(self.root)
        top.title(f"Bearbeite Spieler {spieler['id']}")

        tk.Label(top, text="Name:").grid(row=0, column=0, sticky="w")
        name_entry = tk.Entry(top)
        name_entry.insert(0, spieler["name"])
        name_entry.grid(row=0, column=1)

        tk.Label(top, text="Telefon:").grid(row=1, column=0, sticky="w")
        tel_entry = tk.Entry(top)
        tel_entry.insert(0, spieler["telefon"])
        tel_entry.grid(row=1, column=1)

        tk.Label(top, text="Mobil:").grid(row=2, column=0, sticky="w")
        mob_entry = tk.Entry(top)
        mob_entry.insert(0, spieler["mobil"])
        mob_entry.grid(row=2, column=1)

        def speichern_und_schliessen():
            spieler["name"] = name_entry.get().strip()
            spieler["telefon"] = tel_entry.get().strip()
            spieler["mobil"] = mob_entry.get().strip()
            self.speichern()
            top.destroy()

        tk.Button(top, text="Speichern", command=speichern_und_schliessen).grid(row=3, column=0, columnspan=2, pady=5)

    def loeschen_rechtsklick(self, event):
        index = self.listbox.nearest(event.y)
        if index < 0:
            return
        sp_id = self.listbox.get(index).split(" - ")[0]
        if messagebox.askyesno("Löschen", f"Soll Spieler '{sp_id}' wirklich gelöscht werden?"):
            self.spieler = [sp for sp in self.spieler if sp["id"] != sp_id]
            self.speichern()

    def speichern(self):
        speichere_spieler(self.spieler)
        self.aktualisiere_liste()


if __name__ == "__main__":
    root = tk.Tk()
    root.option_add("*Font", "Arial 12")
    root.minsize(500, 400)
    Tennisspieler(root)
    root.mainloop()
