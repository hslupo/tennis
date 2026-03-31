# TennisrundeApp.py
import tkinter as tk
from tkinter import messagebox, simpledialog
from pathlib import Path
from tennis_model import Spieler, save_json, load_json


FONT = ("Arial", 12)


class BearbeiteSpielerDialog(simpledialog.Dialog):
    def __init__(self, parent, spieler: Spieler):
        self.spieler = spieler
        super().__init__(parent, title=f"Bearbeite {spieler.id}")

    def body(self, master):
        tk.Label(master, text="Name:", font=FONT).grid(row=0, column=0, sticky="w", pady=5)
        self.name_var = tk.StringVar(value=self.spieler.name)
        tk.Entry(master, textvariable=self.name_var, font=FONT, width=25).grid(row=0, column=1, padx=5)

        tk.Label(master, text="Telefon:", font=FONT).grid(row=1, column=0, sticky="w", pady=5)
        self.tel_var = tk.StringVar(value=self.spieler.telefon)
        tk.Entry(master, textvariable=self.tel_var, font=FONT, width=25).grid(row=1, column=1, padx=5)

        tk.Label(master, text="Mobil:", font=FONT).grid(row=2, column=0, sticky="w", pady=5)
        self.mobil_var = tk.StringVar(value=self.spieler.mobil)
        tk.Entry(master, textvariable=self.mobil_var, font=FONT, width=25).grid(row=2, column=1, padx=5)

    def apply(self):
        self.spieler.name = self.name_var.get().strip()
        self.spieler.telefon = self.tel_var.get().strip()
        self.spieler.mobil = self.mobil_var.get().strip()


class TennisSpielerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Spielerverwaltung")

        self.spieler: list[Spieler] = []

        frame = tk.Frame(root, padx=15, pady=15)
        frame.pack(fill=tk.BOTH, expand=True)

        # Eingabefeld für Spieler-ID (Rufname)
        tk.Label(frame, text="Rufname:", font=FONT).grid(row=0, column=0, sticky="w")
        self.id_entry = tk.Entry(frame, font=FONT, width=25)
        self.id_entry.grid(row=0, column=1, sticky="ew", padx=5)

        self.add_button = tk.Button(frame, text="Hinzufügen", font=FONT, command=self.add_spieler)
        self.add_button.grid(row=0, column=2, padx=5)

        # Spieler-Liste
        self.spieler_listbox = tk.Listbox(
            frame, height=12, font=FONT, selectmode=tk.SINGLE,
            borderwidth=2, relief="groove"
        )
        self.spieler_listbox.grid(row=1, column=0, columnspan=3, sticky="nsew", pady=10)
        self.spieler_listbox.bind("<Double-Button-1>", self.bearbeite_spieler)
        self.spieler_listbox.bind("<Button-3>", self.kontextmenue)  # Rechtsklick

        frame.rowconfigure(1, weight=1)
        frame.columnconfigure(1, weight=1)

        # Kontextmenü (Rechtsklick)
        self.menu = tk.Menu(self.root, tearoff=0, font=FONT)
        self.menu.add_command(label="Löschen", command=self.loesche_spieler)

        # Spieler laden beim Start
        self.laden()

    # --- GUI Logik ---
    def refresh_list(self):
        self.spieler.sort(key=lambda s: s.id.lower())  # alphabetisch sortieren
        self.spieler_listbox.delete(0, tk.END)
        for s in self.spieler:
            self.spieler_listbox.insert(tk.END, f"  {s.id} - {s.name}")  # Abstand links

    def add_spieler(self):
        spieler_id = self.id_entry.get().strip().lower()
        if not spieler_id:
            messagebox.showwarning("Warnung", "Bitte einen Rufnamen eingeben.")
            return

        if any(s.id == spieler_id for s in self.spieler):
            messagebox.showwarning("Warnung", f"Spieler-ID '{spieler_id}' existiert bereits.")
            return

        neuer = Spieler(id=spieler_id, name="")
        self.spieler.append(neuer)
        self.id_entry.delete(0, tk.END)

        # Direkt Bearbeiten-Dialog öffnen
        BearbeiteSpielerDialog(self.root, neuer)

        self.refresh_list()
        self.speichern()

    def bearbeite_spieler(self, event):
        sel = self.spieler_listbox.curselection()
        if not sel:
            return
        index = sel[0]
        spieler = self.spieler[index]
        BearbeiteSpielerDialog(self.root, spieler)
        self.refresh_list()
        self.speichern()

    def kontextmenue(self, event):
        try:
            index = self.spieler_listbox.nearest(event.y)
            self.spieler_listbox.selection_clear(0, tk.END)
            self.spieler_listbox.selection_set(index)
            self.menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.menu.grab_release()

    def loesche_spieler(self):
        sel = self.spieler_listbox.curselection()
        if not sel:
            return
        index = sel[0]
        spieler = self.spieler[index]
        if messagebox.askyesno("Löschen", f"Soll Spieler '{spieler.id}' wirklich gelöscht werden?"):
            self.spieler.pop(index)
            self.refresh_list()
            self.speichern()

    # --- Datei IO ---
    def speichern(self):
        save_json(Path("../spieler.json"), {"players": [s.to_dict() for s in self.spieler]})

    def laden(self):
        path = Path("../spieler.json")
        if path.exists():
            data = load_json(path)
            self.spieler = data #[Spieler.from_dict(p)]
        else:
            self.spieler = []
        self.refresh_list()


if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("520x420")  # etwas mehr Platz für größere Schrift
    app = TennisSpielerApp(root)
    root.mainloop()
