import datetime

from PySide6.QtWidgets import (
    QDialog, QGridLayout, QLabel, QPushButton, QMessageBox, QVBoxLayout,
)

import legacy_adapter


def letzter_montag_september(jahr: int) -> datetime.date:
    datum = datetime.date(jahr, 9, 30)
    return datum - datetime.timedelta(days=(datum.weekday() - 0) % 7)


def letzter_sonntag_april(jahr: int) -> datetime.date:
    datum = datetime.date(jahr, 4, 30)
    return datum - datetime.timedelta(days=(datum.weekday() - 6) % 7)


class SaisonDialog(QDialog):
    def __init__(self, parent, jahr: int, on_saved=None):
        super().__init__(parent)
        self.jahr = jahr
        self.on_saved = on_saved
        self.start_date = letzter_montag_september(jahr)
        self.end_date = letzter_sonntag_april(jahr + 1)

        self.setWindowTitle(f"Saison {jahr} anlegen")

        layout = QVBoxLayout(self)
        grid = QGridLayout()
        layout.addLayout(grid)

        grid.addWidget(QLabel("Startdatum:"), 0, 0)
        self.start_label = QLabel()
        grid.addWidget(self.start_label, 0, 1)
        btn_start_minus = QPushButton("-1 Woche")
        btn_start_minus.clicked.connect(lambda: self._shift("start", -7))
        grid.addWidget(btn_start_minus, 0, 2)
        btn_start_plus = QPushButton("+1 Woche")
        btn_start_plus.clicked.connect(lambda: self._shift("start", 7))
        grid.addWidget(btn_start_plus, 0, 3)

        grid.addWidget(QLabel("Enddatum:"), 1, 0)
        self.end_label = QLabel()
        grid.addWidget(self.end_label, 1, 1)
        btn_end_minus = QPushButton("-1 Woche")
        btn_end_minus.clicked.connect(lambda: self._shift("end", -7))
        grid.addWidget(btn_end_minus, 1, 2)
        btn_end_plus = QPushButton("+1 Woche")
        btn_end_plus.clicked.connect(lambda: self._shift("end", 7))
        grid.addWidget(btn_end_plus, 1, 3)

        btn_speichern = QPushButton("Neue Saison speichern")
        btn_speichern.clicked.connect(self._speichern)
        layout.addWidget(btn_speichern)

        self._aktualisiere_labels()

    def _aktualisiere_labels(self):
        self.start_label.setText(self.start_date.isoformat())
        self.end_label.setText(self.end_date.isoformat())

    def _shift(self, feld, tage):
        if feld == "start":
            self.start_date += datetime.timedelta(days=tage)
        else:
            self.end_date += datetime.timedelta(days=tage)
        self._aktualisiere_labels()

    def _speichern(self):
        # Hinweis: speichere_saison ergänzt/aktualisiert nur die übergebenen Gruppen,
        # bestehende Gruppen einer Saison werden dadurch nie gelöscht.
        s = {
            "jahr": self.jahr,
            "start_date": self.start_date.isoformat(),
            "end_date": self.end_date.isoformat(),
            "last_group": "",
            "groups": {},
        }
        legacy_adapter.speichere_saison(s)
        QMessageBox.information(self, "Gespeichert", f"Saison {self.jahr} gespeichert.")
        self.accept()
        if self.on_saved:
            self.on_saved()
