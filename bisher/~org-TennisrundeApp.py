import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime, timedelta
import calendar
import json
import os
from rundenspieler import Rundenspieler, SpielerDialog
from VerfuegbareTermineDialog import VerfuegbareTermineDialog


class TennisrundeApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Tennisrunde Initialisierung")
        self.root.geometry("790x600")  # Vergrößerte Fenstergröße
        self.root.bind('<Configure>', self.update_title_with_size)

        self.label_font = ("Helvetica", 12)
        self.entry_font = ("Helvetica", 12)
        self.button_font = ("Helvetica", 12)
        self.listbox_font = ("Helvetica", 12)

        self.wochentage = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"]

        tk.Label(root, text="Wochentag auswählen:", font=self.label_font).grid(row=0, column=0, sticky="E", padx=10,
                                                                               pady=10)
        self.wochentag_combobox = ttk.Combobox(root, values=self.wochentage, state="readonly", font=self.entry_font,
                                               justify="center")
        self.wochentag_combobox.grid(row=0, column=1, padx=10, pady=10)
        self.wochentag_combobox.bind("<<ComboboxSelected>>", self.update_dates)

        tk.Label(root, text="oder", font=self.label_font).grid(row=0, column=2, padx=5, pady=10)
        self.load_button = tk.Button(root, text="Laden", font=self.button_font, command=self.load_data)
        self.load_button.grid(row=0, column=3, padx=10, pady=10)

        tk.Label(root, text="Startdatum:", font=self.label_font).grid(row=1, column=0, sticky="E", padx=10, pady=10)
        self.start_date_label = tk.Label(root, text="", font=self.entry_font, anchor="center", width=12)
        self.start_date_label.grid(row=1, column=1, padx=10, pady=10)

        tk.Label(root, text="Enddatum:", font=self.label_font).grid(row=2, column=0, sticky="E", padx=10, pady=10)
        self.end_date_label = tk.Label(root, text="", font=self.entry_font, anchor="center", width=12)
        self.end_date_label.grid(row=2, column=1, padx=10, pady=10)

        self.start_plus_button = tk.Button(root, text="+", font=self.button_font,
                                           command=lambda: self.change_week("start", 1))
        self.start_minus_button = tk.Button(root, text="-", font=self.button_font,
                                            command=lambda: self.change_week("start", -1))
        self.start_plus_button.grid(row=1, column=2, padx=10, pady=10)
        self.start_minus_button.grid(row=1, column=3, padx=10, pady=10)

        self.end_plus_button = tk.Button(root, text="+", font=self.button_font,
                                         command=lambda: self.change_week("end", 1))
        self.end_minus_button = tk.Button(root, text="-", font=self.button_font,
                                          command=lambda: self.change_week("end", -1))
        self.end_plus_button.grid(row=2, column=2, padx=10, pady=10)
        self.end_minus_button.grid(row=2, column=3, padx=10, pady=10)

        tk.Label(root, text="Anzahl der Spieler:", font=self.label_font).grid(row=3, column=0, sticky="E", padx=10,
                                                                              pady=10)
        self.player_count_entry = tk.Entry(root, font=self.entry_font, justify="center", width=5)
        self.player_count_entry.grid(row=3, column=1, padx=10, pady=10)
        self.player_count_entry.bind("<Return>", self.generate_players)

        self.player_listbox = tk.Listbox(root, font=self.listbox_font, justify="center", width=20, height=10)
        self.player_listbox.grid(row=0, column=4, rowspan=4, padx=20, pady=10)
        self.player_listbox.bind("<Double-1>", self.edit_player)

        self.save_button = tk.Button(root, text="Speichern", font=self.button_font, command=self.save_data)
        self.save_button.grid(row=4, column=4, padx=20, pady=10)

        self.verfuegbare_termine_button = tk.Button(root, text="Verfügbare Termine", font=self.button_font,
                                                    command=self.open_verfuegbare_termine_dialog)
        self.verfuegbare_termine_button.grid(row=4, column=1, padx=10, pady=10)

        self.start_date = None
        self.end_date = None
        self.players = []
        self.verfuegbare_termine = []
        self.verteilung = {}

        # Frame für die Verteilungstabelle
        self.verteilung_frame = tk.Frame(root)
        self.verteilung_frame.grid(row=5, column=0, columnspan=5, padx=20, pady=10, sticky="nsew")

        # Scrollbare Tabelle für die Verteilung
        self.verteilung_tree = ttk.Treeview(self.verteilung_frame, columns=("Datum", "Spieler"), show="headings")
        self.verteilung_tree.heading("Datum", text="Datum")
        self.verteilung_tree.heading("Spieler", text="Spieler")
        self.verteilung_tree.column("Datum", width=100)
        self.verteilung_tree.column("Spieler", width=300)
        self.verteilung_tree.pack(side="left", fill="both", expand=True)

        # Scrollbar für die Tabelle
        verteilung_scrollbar = ttk.Scrollbar(self.verteilung_frame, orient="vertical",
                                             command=self.verteilung_tree.yview)
        verteilung_scrollbar.pack(side="right", fill="y")
        self.verteilung_tree.configure(yscrollcommand=verteilung_scrollbar.set)

    def update_title_with_size(self, event):
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        self.root.title(f"Tennisrunde Initialisierung ({width}x{height})")

    def update_dates(self, event):
        selected_day = self.wochentage.index(self.wochentag_combobox.get())
        current_year = datetime.now().year

        first_october = datetime(current_year, 10, 1)
        self.start_date = first_october + timedelta((selected_day - first_october.weekday() + 7) % 7)

        last_april = datetime(current_year + 1, 4, calendar.monthrange(current_year + 1, 4)[1])
        self.end_date = last_april - timedelta((last_april.weekday() - selected_day + 7) % 7)

        self.start_date_label.config(text=self.start_date.strftime("%d.%m.%Y"))
        self.end_date_label.config(text=self.end_date.strftime("%d.%m.%Y"))

    def change_week(self, date_type, weeks):
        if date_type == "start" and self.start_date:
            self.start_date += timedelta(weeks=weeks)
            self.start_date_label.config(text=self.start_date.strftime("%d.%m.%Y"))
        elif date_type == "end" and self.end_date:
            self.end_date += timedelta(weeks=weeks)
            self.end_date_label.config(text=self.end_date.strftime("%d.%m.%Y"))

    def generate_players(self, event):
        try:
            num_players = int(self.player_count_entry.get())
            if num_players < 1:
                raise ValueError("Die Anzahl der Spieler muss mindestens 1 sein.")

            self.players = [Rundenspieler(f"Spieler {i + 1}") for i in range(num_players)]

            self.update_player_listbox()

        except ValueError as e:
            tk.messagebox.showerror("Fehler", str(e))

    def update_player_listbox(self):
        self.player_listbox.delete(0, tk.END)
        for player in self.players:
            display_name = player.name if player.name else player.dummyname
            self.player_listbox.insert(tk.END, display_name)

    def edit_player(self, event):
        selected_index = self.player_listbox.curselection()
        if selected_index:
            index = selected_index[0]
            selected_player = self.players[index]

            self.root.grab_set()

            dialog = SpielerDialog(self.root, selected_player, self.start_date, self.end_date,
                                   self.update_player_listbox)

            self.root.wait_window(dialog.dialog)

            self.root.grab_release()

    def save_data(self):
        if not self.start_date or not self.end_date:
            messagebox.showerror("Fehler", "Bitte wählen Sie zuerst ein Start- und Enddatum aus.")
            return

        # Datenstruktur vorbereiten
        data = {
            "start_date": self.start_date.strftime("%Y-%m-%d"),
            "end_date": self.end_date.strftime("%Y-%m-%d"),
            "verfuegbare_termine": self.verfuegbare_termine,
            "players": [
                {
                    "dummyname": player.dummyname,
                    "name": player.name,
                    "telefon": player.telefon,
                    "mobil": player.mobil,
                    "nicht_verfuegbare_termine": player.nicht_verfuegbare_termine
                }
                for player in self.players
            ],
            "verteilung": self.verteilung
        }

        # Automatische Dateinamengenerierung: 'YY-Wochentag.json'
        current_year = datetime.now().strftime("%y")
        selected_day = self.wochentag_combobox.get()
        file_name = f"{current_year}-{selected_day}.json"

        # Projektverzeichnis bestimmen
        project_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(project_dir, file_name)

        # Speichern im Projektverzeichnis
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        messagebox.showinfo("Erfolg", f"Daten wurden erfolgreich in {file_name} gespeichert.")

    def load_data(self):
        # Projektverzeichnis bestimmen
        project_dir = os.path.dirname(os.path.abspath(__file__))

        file_path = filedialog.askopenfilename(initialdir=project_dir, filetypes=[("JSON files", "*.json")])
        if file_path:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            self.start_date = datetime.strptime(data["start_date"], "%Y-%m-%d")
            self.end_date = datetime.strptime(data["end_date"], "%Y-%m-%d")

            self.start_date_label.config(text=self.start_date.strftime("%d.%m.%Y"))
            self.end_date_label.config(text=self.end_date.strftime("%d.%m.%Y"))

            selected_day = self.start_date.weekday()
            self.wochentag_combobox.set(self.wochentage[selected_day])

            self.players = [
                Rundenspieler(
                    player["dummyname"],
                    player["name"],
                    player["telefon"],
                    player["mobil"],
                    player["nicht_verfuegbare_termine"]
                )
                for player in data["players"]
            ]

            self.verfuegbare_termine = data.get("verfuegbare_termine", [])
            self.verteilung = data.get("verteilung", {})

            self.update_player_listbox()
            self.update_verteilung_ansicht()
            messagebox.showinfo("Erfolg", "Daten wurden erfolgreich geladen.")

    def open_verfuegbare_termine_dialog(self):
        dialog = VerfuegbareTermineDialog(self.root, self.start_date, self.end_date, self.verfuegbare_termine,
                                          self.update_verfuegbare_termine)
        self.root.wait_window(dialog.dialog)

    def update_verfuegbare_termine(self):
        pass

    def update_verteilung_ansicht(self):
        # Lösche bestehende Einträge
        for item in self.verteilung_tree.get_children():
            self.verteilung_tree.delete(item)

        # Füge neue Einträge hinzu
        for datum, spieler in self.verteilung.items():
            self.verteilung_tree.insert("", "end", values=(datum, ", ".join(spieler)))


if __name__ == "__main__":
    root = tk.Tk()
    app = TennisrundeApp(root)
    root.mainloop()