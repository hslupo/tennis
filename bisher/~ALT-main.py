import tkinter as tk
from tkinter import messagebox
from tkcalendar import Calendar
from datetime import datetime, timedelta, date
import locale
import calendar

# Setze das Datumslayout auf Deutsch
locale.setlocale(locale.LC_TIME, "de_DE")

class Person:
    def __init__(self, name, unavailable_dates=None):
        self.name = name
        self.unavailable_dates = unavailable_dates or []

    def is_available(self, date):
        return date not in self.unavailable_dates

class Termin:
    def __init__(self, date, start_time, end_time, platznummer, gesperrt=False):
        self.date = date
        self.start_time = start_time
        self.end_time = end_time
        self.platznummer = platznummer
        self.gesperrt = gesperrt
        self.teilnehmer = []

    def add_person(self, person):
        if not self.gesperrt and len(self.teilnehmer) < 4 and person.is_available(self.date):
            self.teilnehmer.append(person)
            return True
        return False

class Tennisrunde:
    def __init__(self, personen, start_date, end_date, start_time, end_time, platznummer):
        self.personen = personen
        self.start_time = start_time
        self.end_time = end_time
        self.platznummer = platznummer
        self.termine = self.generate_termine(start_date, end_date)

    def generate_termine(self, start_date, end_date):
        termine = []
        current_date = start_date
        while current_date <= end_date:
            termine.append(Termin(current_date, self.start_time, self.end_time, self.platznummer))
            current_date += timedelta(weeks=1)
        return termine

    def zuweisen(self):
        for termin in self.termine:
            for person in self.personen:
                if termin.add_person(person):
                    print(f'{person.name} wurde zu Termin am {termin.date} zugewiesen.')
            if not termin.teilnehmer:
                print(f'Kein Teilnehmer für den Termin am {termin.date} gefunden.')

class TennisrundeApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Tennisrunde Initialisierung")

        # Startdatum mit Kalender
        tk.Label(root, text="Startdatum:").grid(row=0, column=0)
        self.start_cal = Calendar(root, date_pattern="dd.mm.yyyy", locale="de_DE")
        self.start_cal.grid(row=0, column=1)
        self.start_cal.bind("<<CalendarSelected>>", self.update_end_date)

        # Enddatum mit Kalender
        tk.Label(root, text="Enddatum:").grid(row=1, column=0)
        self.end_cal = Calendar(root, date_pattern="dd.mm.yyyy", locale="de_DE")
        self.end_cal.grid(row=1, column=1)

        # Anzahl der Personen
        tk.Label(root, text="Anzahl der Personen:").grid(row=2, column=0)
        self.num_persons_entry = tk.Entry(root)
        self.num_persons_entry.grid(row=2, column=1)

        # Platznummer
        tk.Label(root, text="Platznummer:").grid(row=3, column=0)
        self.platznummer_entry = tk.Entry(root)
        self.platznummer_entry.grid(row=3, column=1)

        # Startzeit
        tk.Label(root, text="Startzeit (HH:MM):").grid(row=4, column=0)
        self.start_time_entry = tk.Entry(root)
        self.start_time_entry.grid(row=4, column=1)

        # Endzeit
        tk.Label(root, text="Endzeit (HH:MM):").grid(row=5, column=0)
        self.end_time_entry = tk.Entry(root)
        self.end_time_entry.grid(row=5, column=1)

        # Initialisierungsbutton
        self.init_button = tk.Button(root, text="Tennisrunde Initialisieren", command=self.init_tennisrunde)
        self.init_button.grid(row=6, column=0, columnspan=2)

        # Personenliste
        self.person_list_label = tk.Label(root, text="Personenliste:")
        self.person_list_label.grid(row=7, column=0, columnspan=2)
        self.person_listbox = tk.Listbox(root)
        self.person_listbox.grid(row=8, column=0, columnspan=2)

    def update_end_date(self, event):
        # Hole das Startdatum aus dem Kalender
        start_date = datetime.strptime(self.start_cal.get_date(), "%d.%m.%Y").date()

        # Berechne das Jahr des Folgejahres
        next_year = start_date.year + 1

        # Setze das Enddatum auf den letzten gewählten Wochentag im April des Folgejahres
        end_date = self.get_last_weekday_of_month(next_year, 4, start_date.weekday())

        # Setze das berechnete Datum im Enddatum-Kalender
        self.end_cal.set_date(end_date)

    def get_last_weekday_of_month(self, year, month, weekday):
        # Bestimme den letzten Tag des Monats
        last_day_of_month = calendar.monthrange(year, month)[1]
        last_date_of_month = date(year, month, last_day_of_month)

        # Berechne das Enddatum (letzter gewählter Wochentag im April des Folgejahres)
        while last_date_of_month.weekday() != weekday:
            last_date_of_month -= timedelta(days=1)

        return last_date_of_month

    def init_tennisrunde(self):
        try:
            start_date = datetime.strptime(self.start_cal.get_date(), "%d.%m.%Y").date()
            end_date = datetime.strptime(self.end_cal.get_date(), "%d.%m.%Y").date()
            num_persons = int(self.num_persons_entry.get())
            platznummer = int(self.platznummer_entry.get())
            start_time = self.start_time_entry.get()
            end_time = self.end_time_entry.get()

            if start_date > end_date:
                messagebox.showerror("Fehler", "Das Enddatum muss nach dem Startdatum liegen.")
                return

            # Generiere symbolische Namen für Personen
            personen = [Person(f"Person{i+1}") for i in range(num_persons)]

            # Initialisiere die Tennisrunde
            self.runde = Tennisrunde(personen, start_date, end_date, start_time, end_time, platznummer)

            # Runde-Name generieren (Wochentag und Jahr auf Deutsch)
            runde_name = f"Tennisrunde_{start_date.strftime('%A_%Y')}"
            messagebox.showinfo("Erfolg", f"Die Tennisrunde '{runde_name}' wurde erfolgreich initialisiert.")

            # Personen in die Liste eintragen
            self.person_listbox.delete(0, tk.END)
            for person in personen:
                self.person_listbox.insert(tk.END, person.name)

            # Zeige den generierten Namen der Runde im Dialog an
            tk.Label(self.root, text=f"Rundenname: {runde_name}").grid(row=9, column=0, columnspan=2)

        except ValueError as e:
            messagebox.showerror("Fehler", f"Ungültige Eingabe: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = TennisrundeApp(root)
    root.mainloop()
