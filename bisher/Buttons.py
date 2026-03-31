import tkinter as tk
from datetime import date
from functools import partial

from datumsfunktionen import letzter_montag_september, letzter_sonntag_april, plus_eine_woche, minus_eine_woche

class NeueSaisonDialog:
    def __init__(self, root, jahr: int):
        self.root = root
        self.jahr = jahr

        # Vorbelegung
        self.start_date = letzter_montag_september(jahr)
        self.end_date = letzter_sonntag_april(jahr + 1)

        frame = tk.Frame(root, padx=10, pady=10)
        frame.pack()

        # Startdatum
        tk.Label(frame, text="Startdatum:").grid(row=0, column=0, sticky="w")
        self.start_var = tk.StringVar(value=str(self.start_date))
        tk.Label(frame, textvariable=self.start_var, width=12).grid(row=0, column=1)
        tk.Button(frame, text="-1 Woche", command=partial(self.shift_start, -1)).grid(row=0, column=2, padx=2)
        tk.Button(frame, text="+1 Woche", command=partial(self.shift_start, 1)).grid(row=0, column=3, padx=2)

        # Enddatum
        tk.Label(frame, text="Enddatum:").grid(row=1, column=0, sticky="w")
        self.end_var = tk.StringVar(value=str(self.end_date))
        tk.Label(frame, textvariable=self.end_var, width=12).grid(row=1, column=1)
        tk.Button(frame, text="-1 Woche", command=partial(self.shift_end, -1)).grid(row=1, column=2, padx=2)
        tk.Button(frame, text="+1 Woche", command=partial(self.shift_end, 1)).grid(row=1, column=3, padx=2)

        # Speichern
        tk.Button(frame, text="Neue Saison speichern", command=self.speichern).grid(row=2, column=0, columnspan=4, pady=10)

    def shift_start(self, richtung: int):
        if richtung > 0:
            self.start_date = plus_eine_woche(self.start_date)
        else:
            self.start_date = minus_eine_woche(self.start_date)
        self.start_var.set(str(self.start_date))

    def shift_end(self, richtung: int):
        if richtung > 0:
            self.end_date = plus_eine_woche(self.end_date)
        else:
            self.end_date = minus_eine_woche(self.end_date)
        self.end_var.set(str(self.end_date))

    def speichern(self):
        print(f"Saison {self.jahr}: {self.start_date} bis {self.end_date}")
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    NeueSaisonDialog(root, 2024)
    root.mainloop()
