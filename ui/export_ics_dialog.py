from pathlib import Path

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QRadioButton,
    QButtonGroup, QPushButton, QFileDialog, QMessageBox,
)

from services.export_ics_service import erstelle_ics_fuer_gruppe, erstelle_ics_fuer_spieler


class ExportIcsDialog(QDialog):
    """Kleiner Dialog zum Export eines ICS-Kalenders: entweder für die aktuelle
    Gruppe oder für einen ausgewählten Spieler (Gruppen- oder Saisonkalender)."""

    def __init__(self, parent, saison: dict, gruppe_key: str, spieler_namen: dict):
        super().__init__(parent)
        self.saison = saison
        self.gruppe_key = gruppe_key
        self.spieler_namen = spieler_namen

        self.setWindowTitle("ICS-Export")

        layout = QVBoxLayout(self)

        self.radio_gruppe = QRadioButton("Aktuelle Gruppe")
        self.radio_gruppe.setChecked(True)
        self.radio_spieler = QRadioButton("Spieler auswählen")
        modus_gruppe = QButtonGroup(self)
        modus_gruppe.addButton(self.radio_gruppe)
        modus_gruppe.addButton(self.radio_spieler)
        layout.addWidget(self.radio_gruppe)
        layout.addWidget(self.radio_spieler)

        spieler_layout = QHBoxLayout()
        spieler_layout.addWidget(QLabel("Spieler:"))
        self.spieler_combo = QComboBox()
        for pid, name in sorted(spieler_namen.items(), key=lambda kv: kv[1].lower()):
            self.spieler_combo.addItem(name, pid)
        spieler_layout.addWidget(self.spieler_combo, stretch=1)
        layout.addLayout(spieler_layout)

        kalender_layout = QHBoxLayout()
        self.radio_gruppenkalender = QRadioButton("Gruppenkalender")
        self.radio_gruppenkalender.setChecked(True)
        self.radio_saisonkalender = QRadioButton("Saisonkalender")
        kalender_gruppe = QButtonGroup(self)
        kalender_gruppe.addButton(self.radio_gruppenkalender)
        kalender_gruppe.addButton(self.radio_saisonkalender)
        kalender_layout.addWidget(self.radio_gruppenkalender)
        kalender_layout.addWidget(self.radio_saisonkalender)
        layout.addLayout(kalender_layout)

        self.radio_gruppe.toggled.connect(self._aktualisiere_aktivierung)
        self._aktualisiere_aktivierung()

        btn_row = QHBoxLayout()
        btn_abbrechen = QPushButton("Abbrechen")
        btn_abbrechen.clicked.connect(self.reject)
        btn_row.addWidget(btn_abbrechen)
        btn_exportieren = QPushButton("Exportieren...")
        btn_exportieren.clicked.connect(self._exportieren)
        btn_row.addWidget(btn_exportieren)
        layout.addLayout(btn_row)

    def _aktualisiere_aktivierung(self):
        spieler_modus = self.radio_spieler.isChecked()
        self.spieler_combo.setEnabled(spieler_modus)
        self.radio_gruppenkalender.setEnabled(spieler_modus)
        self.radio_saisonkalender.setEnabled(spieler_modus)

    def _exportieren(self):
        gruppe = self.saison["groups"][self.gruppe_key]
        if self.radio_gruppe.isChecked():
            text = erstelle_ics_fuer_gruppe(gruppe, self.spieler_namen)
            default_name = f"tennis_{gruppe.get('wochentag', 'gruppe')}.ics"
        else:
            spieler_id = self.spieler_combo.currentData()
            if spieler_id is None:
                QMessageBox.warning(self, "Kein Spieler", "Bitte einen Spieler auswählen.")
                return
            ziel_gruppe_key = self.gruppe_key if self.radio_gruppenkalender.isChecked() else None
            text = erstelle_ics_fuer_spieler(self.saison, spieler_id, self.spieler_namen, gruppe_key=ziel_gruppe_key)
            spieler_name = self.spieler_combo.currentText()
            default_name = f"tennis_{spieler_name}.ics"

        fp, _ = QFileDialog.getSaveFileName(self, "ICS-Kalender speichern", default_name, "Kalenderdatei (*.ics)")
        if not fp:
            return
        try:
            Path(fp).write_text(text, encoding="utf-8")
            QMessageBox.information(self, "Exportiert", f"ICS-Kalender gespeichert: {fp}")
            self.accept()
        except OSError as e:
            QMessageBox.critical(self, "Fehler", f"Speichern fehlgeschlagen:\n{e}")
