import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from datetime import timedelta


class Rundenspieler:
    def __init__(self, dummyname, name="", telefon="", mobil="", nicht_verfuegbare_termine=None):
        self.dummyname = dummyname
        self.name = name
        self.telefon = telefon
        self.mobil = mobil
        self.nicht_verfuegbare_termine = nicht_verfuegbare_termine or []


class SpielerDialog:
    def __init__(self, parent, spieler, start_date, end_date, update_listbox_callback):
        self.spieler = spieler
        self.start_date = start_date
        self.end_date = end_date
        self.update_listbox_callback = update_listbox_callback
        self.terminliste = self.generate_terminliste()

        self.dialog = tk.Toplevel(parent)
        self.dialog.title(f"Bearbeite Daten für {spieler.dummyname}")
        self.dialog.geometry("440x410")  # Geometrie auf 440x410 festlegen
        self.dialog.configure(bg="lightblue")  # Hintergrundfarbe auf hellblau setzen
        self.dialog.transient(parent)  # Make dialog modal
        self.dialog.grab_set()  # Prevent interaction with the main window

        # Event binden, um die Geometrie bei Änderungen im Titel anzuzeigen
        self.dialog.bind('<Configure>', self.update_title_with_size)

        # Schriftgröße 12 für den Dialog
        self.label_font = ("Helvetica", 12)
        self.entry_font = ("Helvetica", 12)

        tk.Label(self.dialog, text="Name:", font=self.label_font, bg="lightblue").grid(row=0, column=0, sticky="E", padx=10, pady=10)
        self.name_entry = tk.Entry(self.dialog, font=self.entry_font)
        self.name_entry.grid(row=0, column=1, padx=10, pady=10)
        self.name_entry.insert(0, spieler.name)

        tk.Label(self.dialog, text="Telefon:", font=self.label_font, bg="lightblue").grid(row=1, column=0, sticky="E", padx=10, pady=10)
        self.telefon_entry = tk.Entry(self.dialog, font=self.entry_font)
        self.telefon_entry.grid(row=1, column=1, padx=10, pady=10)
        self.telefon_entry.insert(0, spieler.telefon)

        tk.Label(self.dialog, text="Mobil:", font=self.label_font, bg="lightblue").grid(row=2, column=0, sticky="E", padx=10, pady=10)
        self.mobil_entry = tk.Entry(self.dialog, font=self.entry_font)
        self.mobil_entry.grid(row=2, column=1, padx=10, pady=10)
        self.mobil_entry.insert(0, spieler.mobil)

        tk.Label(self.dialog, text="Nicht verfügbare Termine:", font=self.label_font, bg="lightblue").grid(row=3, column=0, sticky="N",
                                                                                           padx=10, pady=10)
        self.termin_listbox = tk.Listbox(self.dialog, selectmode="multiple", font=self.entry_font, height=10)
        self.termin_listbox.grid(row=3, column=1, padx=10, pady=10)

        for i, termin in enumerate(self.terminliste):
            self.termin_listbox.insert(tk.END, termin)
            if termin in spieler.nicht_verfuegbare_termine:
                self.termin_listbox.selection_set(i)

        self.save_button = tk.Button(self.dialog, text="Speichern", font=self.label_font, command=self.save_data)
        self.save_button.grid(row=4, column=0, columnspan=2, pady=10)

    def update_title_with_size(self, event):
        width = self.dialog.winfo_width()
        height = self.dialog.winfo_height()
        self.dialog.title(f"Bearbeite Daten für {self.spieler.dummyname} ({width}x{height})")

    def generate_terminliste(self):
        termine = []
        current_date = self.start_date
        while current_date <= self.end_date:
            termine.append(current_date.strftime("%d.%m.%Y"))
            current_date += timedelta(weeks=1)
        return termine

    def save_data(self):
        self.spieler.name = self.name_entry.get()
        self.spieler.telefon = self.telefon_entry.get()
        self.spieler.mobil = self.mobil_entry.get()

        selected_indices = self.termin_listbox.curselection()
        self.spieler.nicht_verfuegbare_termine = [self.termin_listbox.get(i) for i in selected_indices]

        # Callback aufrufen, um die Listbox im Hauptfenster zu aktualisieren
        self.update_listbox_callback()

        messagebox.showinfo("Gespeichert", f"Daten für {self.spieler.dummyname} wurden gespeichert.")
        self.dialog.destroy()