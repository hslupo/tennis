from PySide6.QtCore import Qt, QAbstractTableModel, QModelIndex
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableView, QRadioButton, QPushButton,
    QMessageBox, QButtonGroup, QHeaderView, QLabel,
)

import legacy_adapter
from services.verteilung_service import ermittle_ersatzspieler, plane_verteilung, verteile_gruppe


class _SeedVergleichModel(QAbstractTableModel):
    def __init__(self, gruppe: dict, termine: list[str], seeds: tuple[int, ...], vorschlaege: dict, anzeige_namen: dict):
        super().__init__()
        self._gruppe = gruppe
        self._termine = termine
        self._seeds = seeds
        self._vorschlaege = vorschlaege
        self._anzeige_namen = anzeige_namen

    def rowCount(self, parent=QModelIndex()) -> int:
        return len(self._termine)

    def columnCount(self, parent=QModelIndex()) -> int:
        return len(self._seeds) * 2

    def data(self, index, role=Qt.DisplayRole):
        if role != Qt.DisplayRole:
            return None
        termin = self._termine[index.row()]
        seed = self._seeds[index.column() // 2]
        spieler_ids = self._vorschlaege[seed][termin]
        if index.column() % 2:
            spieler_ids = ermittle_ersatzspieler(self._gruppe, termin, spieler_ids)
        return ", ".join(self._anzeige_namen.get(pid, str(pid)) for pid in spieler_ids)

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role != Qt.DisplayRole:
            return None
        if orientation == Qt.Horizontal:
            seed = self._seeds[section // 2]
            return f"Seed {seed}" if section % 2 == 0 else "Ersatz"
        return self._termine[section]


class VerteilungDialog(QDialog):
    """Vergleicht mehrere Zufalls-Seeds für die ersten 4 Termine und übernimmt den
    gewählten Seed für die gesamte Gruppe (Ersatz für verteilen.py:PlanungsDialog)."""

    SEEDS = (2, 7, 9, 16, 54, 61)

    def __init__(self, parent, jahr: int, wochentag_key: str, saison: dict, anzeige_namen: dict, on_change):
        super().__init__(parent)
        self.jahr = jahr
        self.wochentag_key = wochentag_key
        self.saison = saison
        self.anzeige_namen = anzeige_namen
        self.on_change = on_change
        self.gruppe = saison["groups"][wochentag_key]

        self.setWindowTitle("Planungsmodus")
        self.resize(900, 400)

        layout = QVBoxLayout(self)

        termine, vorschlaege = plane_verteilung(self.gruppe, self.saison, self.SEEDS)
        self.model = _SeedVergleichModel(self.gruppe, termine, self.SEEDS, vorschlaege, self.anzeige_namen)

        table = QTableView()
        table.setModel(self.model)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(table)

        layout.addWidget(QLabel(
            "Beim Übernehmen werden nur die bisherigen Einsätze ersetzt. "
            "Die als 'kann nicht' markierten Termine bleiben erhalten."
        ))

        radio_row = QHBoxLayout()
        self.button_group = QButtonGroup(self)
        for i, seed in enumerate(self.SEEDS):
            radio = QRadioButton(f"Seed {seed}")
            if i == 0:
                radio.setChecked(True)
            self.button_group.addButton(radio, seed)
            radio_row.addWidget(radio)
        layout.addLayout(radio_row)

        btn_uebernehmen = QPushButton("Neue Verteilung übernehmen")
        btn_uebernehmen.clicked.connect(self._seed_uebernehmen)
        layout.addWidget(btn_uebernehmen)

    def _seed_uebernehmen(self):
        chosen_seed = self.button_group.checkedId()

        verteilung = verteile_gruppe(
            self.gruppe, self.saison["start_date"], self.saison["end_date"], seed=chosen_seed,
        )
        self.gruppe["seed"] = chosen_seed
        self.gruppe["verteilung"] = verteilung
        self.saison["groups"][self.wochentag_key] = self.gruppe

        legacy_adapter.speichere_saison(self.saison)

        QMessageBox.information(
            self, "Gespeichert", f"Seed {chosen_seed} wurde übernommen und Verteilung gespeichert."
        )
        self.accept()
        if self.on_change:
            self.on_change()
