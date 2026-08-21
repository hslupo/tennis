from PySide6.QtCore import Qt
from PySide6.QtWidgets import QTableWidget, QTableWidgetItem, QWidget, QCheckBox, QHBoxLayout

import legacy_adapter
from services.termine_service import generiere_termine


class VerfuegbarkeitView(QTableWidget):
    """Matrix aller Termine × aller Gruppenmitglieder: Checkbox angehakt = nicht verfügbar.
    Ersetzt die bisherige Tk-Ansicht, in der nur ein Spieler gleichzeitig sichtbar war."""

    def __init__(self, saison: dict, wochentag_key: str, parent=None):
        super().__init__(parent)
        self.saison = saison
        self.wochentag_key = wochentag_key
        self._aufbauen()

    @property
    def gruppe(self) -> dict:
        return self.saison["groups"][self.wochentag_key]

    def _aufbauen(self):
        gruppe = self.gruppe
        termine = generiere_termine(self.saison["start_date"], self.saison["end_date"], gruppe["wochentag"])
        spieler_ids = sorted(gruppe["players"].keys(), key=lambda pid: gruppe["players"][pid]["anzeige_name"].lower())

        self.setRowCount(len(termine))
        self.setColumnCount(len(spieler_ids))
        self.setHorizontalHeaderLabels([gruppe["players"][pid]["anzeige_name"] for pid in spieler_ids])
        self.setVerticalHeaderLabels(termine)
        self.verticalHeader().setDefaultSectionSize(24)

        self._termine = termine
        self._spieler_ids = spieler_ids

        for row, termin in enumerate(termine):
            for col, pid in enumerate(spieler_ids):
                nicht_moeglich = gruppe["players"][pid]["nicht_moeglich"]
                self.setCellWidget(row, col, self._checkbox_zelle(termin, pid, termin in nicht_moeglich))

        self.resizeColumnsToContents()

    def _checkbox_zelle(self, termin: str, spieler_id: int, checked: bool) -> QWidget:
        container = QWidget()
        checkbox = QCheckBox()
        checkbox.setChecked(checked)
        checkbox.stateChanged.connect(lambda state, t=termin, p=spieler_id: self._toggle(t, p, state))
        layout = QHBoxLayout(container)
        layout.addWidget(checkbox)
        layout.setAlignment(Qt.AlignCenter)
        layout.setContentsMargins(0, 0, 0, 0)
        return container

    def _toggle(self, termin: str, spieler_id: int, state):
        nm = self.gruppe["players"][spieler_id]["nicht_moeglich"]
        if state:
            if termin not in nm:
                nm.append(termin)
        else:
            if termin in nm:
                nm.remove(termin)
        legacy_adapter.speichere_saison(self.saison)

    def aktualisieren(self, saison: dict, wochentag_key: str):
        self.saison = saison
        self.wochentag_key = wochentag_key
        self.clear()
        self._aufbauen()
