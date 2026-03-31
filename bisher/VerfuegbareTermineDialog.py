import tkinter as tk
from datetime import timedelta


class VerfuegbareTermineDialog:
    def __init__(self, parent, start_date, end_date, verfuegbare_termine, update_callback):
        self.start_date = start_date
        self.end_date = end_date
        self.verfuegbare_termine = verfuegbare_termine
        self.update_callback = update_callback

        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Verfügbare Termine verwalten")
        self.dialog.geometry("440x410")
        self.dialog.configure(bg="lightblue")

        self.terminliste = self.generate_terminliste()

        tk.Label(self.dialog, text="Verfügbare Termine:", font=("Helvetica", 12), bg="lightblue").grid(row=0, column=0, padx=10, pady=10)

        self.termin_listbox = tk.Listbox(self.dialog, selectmode="multiple", font=("Helvetica", 12), height=10)
        self.termin_listbox.grid(row=1, column=0, padx=10, pady=10)

        for i, termin in enumerate(self.terminliste):
            self.termin_listbox.insert(tk.END, termin)
            if termin in self.verfuegbare_termine:
                self.termin_listbox.selection_set(i)

        self.save_button = tk.Button(self.dialog, text="Speichern", font=("Helvetica", 12), command=self.save_data)
        self.save_button.grid(row=2, column=0, pady=10)

    def generate_terminliste(self):
        termine = []
        current_date = self.start_date
        while current_date <= self.end_date:
            termine.append(current_date.strftime("%d.%m.%Y"))
            current_date += timedelta(weeks=1)
        return termine

    def save_data(self):
        selected_indices = self.termin_listbox.curselection()
        self.verfuegbare_termine.clear()
        self.verfuegbare_termine.extend([self.termin_listbox.get(i) for i in selected_indices])

        self.update_callback()
        self.dialog.destroy()
