from PySide6.QtWidgets import QTableWidget, QPushButton

import legacy_adapter
from services.termine_service import generiere_termine

# Zustandszyklus je Zelle: neutral -> kann nicht -> spielt -> neutral -> ...
_NEUTRAL = "neutral"
_KANN_NICHT = "kann_nicht"
_SPIELT = "spielt"
_NAECHSTER_ZUSTAND = {_NEUTRAL: _KANN_NICHT, _KANN_NICHT: _SPIELT, _SPIELT: _NEUTRAL}

_ANZEIGE = {
    _NEUTRAL: ("", "QPushButton { background-color: #c8c8c8; border: none; }"),
    _KANN_NICHT: (
        "✕",
        "QPushButton { background-color: #dc3545; color: white; border: none; "
        "font-weight: bold; font-size: 12pt; }",
    ),
    _SPIELT: (
        "✓",
        "QPushButton { background-color: #198754; color: white; border: none; "
        "font-weight: bold; font-size: 12pt; }",
    ),
}


class VerfuegbarkeitView(QTableWidget):
    """Matrix aller Termine × aller Gruppenmitglieder: je Zelle einer von drei Zuständen
    (neutral/noch nicht festgelegt, kann nicht, spielt), Klick schaltet weiter."""

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
                self.setCellWidget(row, col, self._zustands_button(termin, pid, self._zustand(termin, pid)))

        self.resizeColumnsToContents()

    def _zustand(self, termin: str, spieler_id: int) -> str:
        eintrag = self.gruppe["players"][spieler_id]
        if termin in eintrag.get("nicht_moeglich", []):
            return _KANN_NICHT
        if termin in eintrag.get("spielt", []):
            return _SPIELT
        if spieler_id in self.gruppe.get("verteilung", {}).get(termin, []):
            return _SPIELT
        return _NEUTRAL

    def _zustands_button(self, termin: str, spieler_id: int, zustand: str) -> QPushButton:
        text, style = _ANZEIGE[zustand]
        button = QPushButton(text)
        button.setStyleSheet(style)
        button.clicked.connect(lambda checked=False, t=termin, p=spieler_id, b=button: self._weiterschalten(t, p, b))
        return button

    def _weiterschalten(self, termin: str, spieler_id: int, button: QPushButton):
        neuer_zustand = _NAECHSTER_ZUSTAND[self._zustand(termin, spieler_id)]

        nm = self.gruppe["players"][spieler_id].setdefault("nicht_moeglich", [])
        sp = self.gruppe["players"][spieler_id].setdefault("spielt", [])
        if termin in nm:
            nm.remove(termin)
        if termin in sp:
            sp.remove(termin)
        if neuer_zustand == _KANN_NICHT:
            nm.append(termin)
        elif neuer_zustand == _SPIELT:
            sp.append(termin)

        text, style = _ANZEIGE[neuer_zustand]
        button.setText(text)
        button.setStyleSheet(style)

        legacy_adapter.speichere_saison(self.saison)

    def aktualisieren(self, saison: dict, wochentag_key: str):
        self.saison = saison
        self.wochentag_key = wochentag_key
        self.clear()
        self._aufbauen()
