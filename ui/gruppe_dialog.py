from PySide6.QtWidgets import (
    QDialog, QFormLayout, QLineEdit, QPushButton, QMessageBox, QVBoxLayout, QHBoxLayout,
)

import legacy_adapter


class GruppeDialog(QDialog):
    def __init__(self, parent, jahr: int, wochentag: str, on_saved=None):
        super().__init__(parent)
        self.jahr = jahr
        self.wochentag_key = wochentag.lower()
        self.anzeige_wochentag = wochentag
        self.on_saved = on_saved

        self.setWindowTitle(f"Neue Gruppe anlegen – {wochentag}")

        layout = QVBoxLayout(self)
        form = QFormLayout()
        layout.addLayout(form)

        self.platz_edit = QLineEdit("1")
        form.addRow("Platz:", self.platz_edit)

        self.startzeit_edit = QLineEdit("18:00")
        form.addRow("Startzeit (HH:MM):", self.startzeit_edit)

        self.endzeit_edit = QLineEdit("20:00")
        form.addRow("Endzeit (HH:MM):", self.endzeit_edit)

        btn_row = QHBoxLayout()
        btn_speichern = QPushButton("Speichern")
        btn_speichern.clicked.connect(self._speichern)
        btn_row.addWidget(btn_speichern)
        btn_abbrechen = QPushButton("Abbrechen")
        btn_abbrechen.clicked.connect(self.reject)
        btn_row.addWidget(btn_abbrechen)
        layout.addLayout(btn_row)

    def _speichern(self):
        platz = self.platz_edit.text().strip()
        startzeit = self.startzeit_edit.text().strip()
        endzeit = self.endzeit_edit.text().strip()

        if not platz or not startzeit or not endzeit:
            QMessageBox.warning(self, "Fehler", "Bitte alle Felder ausfüllen.")
            return

        saison = legacy_adapter.lade_saison(self.jahr)
        if saison is None:
            QMessageBox.critical(self, "Fehler", f"Saison {self.jahr} nicht gefunden!")
            return

        saison["groups"][self.wochentag_key] = {
            "wochentag": self.anzeige_wochentag,
            "platz": platz,
            "startzeit": startzeit,
            "endzeit": endzeit,
            "players": {},
            "verteilung": {},
        }
        saison["last_group"] = self.wochentag_key

        legacy_adapter.speichere_saison(saison)

        QMessageBox.information(self, "Gespeichert", f"Gruppe {self.anzeige_wochentag} wurde gespeichert.")
        self.accept()
        if self.on_saved:
            self.on_saved()
