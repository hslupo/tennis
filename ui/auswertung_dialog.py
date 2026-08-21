from pathlib import Path

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton, QFileDialog, QMessageBox, QApplication,
)

from services.auswertung_service import erstelle_auswertungstext


class AuswertungDialog(QDialog):
    def __init__(self, parent, saison: dict, gruppe: dict, anzeige_namen: dict):
        super().__init__(parent)
        self.text = erstelle_auswertungstext(saison, gruppe, anzeige_namen)
        self.gruppe = gruppe

        self.setWindowTitle("Auswertung")
        self.resize(800, 600)

        layout = QVBoxLayout(self)
        text_edit = QTextEdit()
        text_edit.setPlainText(self.text)
        text_edit.setReadOnly(True)
        layout.addWidget(text_edit)

        btn_row = QHBoxLayout()
        btn_kopieren = QPushButton("Kopieren")
        btn_kopieren.clicked.connect(self._kopieren)
        btn_row.addWidget(btn_kopieren)
        btn_speichern = QPushButton("Speichern...")
        btn_speichern.clicked.connect(self._speichern)
        btn_row.addWidget(btn_speichern)
        btn_schliessen = QPushButton("Schließen")
        btn_schliessen.clicked.connect(self.accept)
        btn_row.addWidget(btn_schliessen)
        layout.addLayout(btn_row)

        self._kopieren()

    def _kopieren(self):
        QApplication.clipboard().setText(self.text)

    def _speichern(self):
        default_name = f"auswertung_{self.gruppe.get('wochentag', 'gruppe')}.txt"
        fp, _ = QFileDialog.getSaveFileName(self, "Auswertung speichern", default_name, "Textdatei (*.txt)")
        if not fp:
            return
        try:
            Path(fp).write_text(self.text, encoding="utf-8")
            QMessageBox.information(self, "Gespeichert", f"Auswertung gespeichert: {fp}")
        except OSError as e:
            QMessageBox.critical(self, "Fehler", f"Speichern fehlgeschlagen:\n{e}")
