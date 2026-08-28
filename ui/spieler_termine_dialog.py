from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)
from datetime import datetime

import legacy_adapter
from services.termine_service import generiere_termine


class SpielerTermineDialog(QDialog):
    """Zeigt die Termine einer Zielgruppe und die Belastung aus anderen Gruppen."""

    def __init__(self, parent, saison: dict, spieler_namen: dict[int, str], spieler_id: int | None = None):
        super().__init__(parent)
        self.saison = saison
        self.spieler_namen = spieler_namen
        self.setWindowTitle("Spieler-Termine")
        self.resize(560, 620)

        layout = QVBoxLayout(self)
        auswahl_layout = QHBoxLayout()
        auswahl_layout.addWidget(QLabel("Spieler:"))
        self.spieler_combo = QComboBox()
        spieler = sorted(
            (
                pid,
                eintrag["anzeige_name"],
            )
            for gruppe in saison.get("groups", {}).values()
            for pid, eintrag in gruppe.get("players", {}).items()
        )
        spieler = list(dict(spieler).items())
        for pid, name in spieler:
            self.spieler_combo.addItem(name, pid)
        self.spieler_combo.currentIndexChanged.connect(self._aktualisieren)
        auswahl_layout.addWidget(self.spieler_combo, stretch=1)
        layout.addLayout(auswahl_layout)

        gruppen_layout = QHBoxLayout()
        gruppen_layout.addWidget(QLabel("Zielgruppe:"))
        self.gruppe_combo = QComboBox()
        gruppen = list(saison.get("groups", {}).items())
        for key, gruppe in gruppen:
            self.gruppe_combo.addItem(gruppe["wochentag"], key)
        freitag_index = next((index for index, (_, gruppe) in enumerate(gruppen) if gruppe["wochentag"].lower() == "freitag"), 0)
        self.gruppe_combo.setCurrentIndex(freitag_index)
        self.gruppe_combo.currentIndexChanged.connect(self._aktualisieren)
        gruppen_layout.addWidget(self.gruppe_combo, stretch=1)
        layout.addLayout(gruppen_layout)
        layout.addWidget(QLabel("Checkbox: leer = nicht eingeteilt, Haken = eingeteilt, halb = nicht möglich"))

        self.tabelle = QTableWidget(0, 5)
        self.tabelle.setHorizontalHeaderLabels(["Datum", "Für mich", "Andere Gruppen", "Gruppen diese Woche", "Bereits eingeteilt"])
        self.tabelle.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tabelle.setSortingEnabled(False)
        self.tabelle.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.tabelle)

        if spieler_id is not None:
            index = self.spieler_combo.findData(spieler_id)
            if index >= 0:
                self.spieler_combo.setCurrentIndex(index)
        self._aktualisieren()

    def _aktualisieren(self):
        spieler_id = self.spieler_combo.currentData()
        eintraege: list[tuple[str, str, dict]] = []
        ziel_key = self.gruppe_combo.currentData()
        zielgruppe = self.saison.get("groups", {}).get(ziel_key)
        if spieler_id is not None and zielgruppe is not None:
            termine = generiere_termine(
                self.saison["start_date"], self.saison["end_date"], zielgruppe["wochentag"]
            )
            andere_gruppen = [
                gruppe for key, gruppe in self.saison.get("groups", {}).items() if key != ziel_key
            ]
            for datum in termine:
                bereits = zielgruppe.get("verteilung", {}).get(datum, [])
                namen = [
                    zielgruppe["players"][pid]["anzeige_name"]
                    for pid in bereits
                    if pid in zielgruppe.get("players", {})
                ]
                datum_objekt = datetime.strptime(datum, "%d.%m.%Y").date()
                andere = [
                    gruppe["wochentag"]
                    for gruppe in andere_gruppen
                    if any(
                        spieler_id in gruppe.get("verteilung", {}).get(anderes_datum, [])
                        for anderes_datum in generiere_termine(
                            self.saison["start_date"], self.saison["end_date"], gruppe["wochentag"]
                        )
                        if datetime.strptime(anderes_datum, "%d.%m.%Y").date().isocalendar()[:2]
                        == datum_objekt.isocalendar()[:2]
                    )
                ]
                eintraege.append((datum, zielgruppe["wochentag"], {
                    "gruppe": zielgruppe,
                    "datum": datum,
                    "spieler_id": spieler_id,
                    "eingeteilt": spieler_id in bereits,
                    "nicht_moeglich": datum in zielgruppe["players"].get(spieler_id, {}).get("nicht_moeglich", []),
                    "namen": namen,
                    "andere": andere,
                }))

        def datum_sortwert(eintrag):
            return (eintrag[0][6:], eintrag[0][3:5], eintrag[0][:2], eintrag[1])

        eintraege.sort(key=datum_sortwert)
        self.tabelle.setRowCount(len(eintraege))
        for row, (datum, gruppe_name, daten) in enumerate(eintraege):
            self.tabelle.setItem(row, 0, QTableWidgetItem(datum))
            checkbox = QCheckBox()
            checkbox.setTristate(True)
            if daten["nicht_moeglich"]:
                checkbox.setCheckState(Qt.PartiallyChecked)
            elif daten["eingeteilt"]:
                checkbox.setCheckState(Qt.Checked)
            else:
                checkbox.setCheckState(Qt.Unchecked)
            checkbox.stateChanged.connect(lambda state, d=daten: self._status_geaendert(d, state))
            self.tabelle.setCellWidget(row, 1, checkbox)
            self.tabelle.setItem(row, 2, QTableWidgetItem(str(len(daten["andere"]))))
            self.tabelle.setItem(row, 3, QTableWidgetItem(", ".join(daten["andere"])))
            self.tabelle.setItem(row, 4, QTableWidgetItem(", ".join(daten["namen"])))
        self.tabelle.resizeColumnsToContents()

    def _status_geaendert(self, daten: dict, state: int):
        gruppe = daten["gruppe"]
        datum = daten["datum"]
        spieler_id = daten["spieler_id"]
        eintrag = gruppe["players"][spieler_id]
        nicht_moeglich = eintrag.setdefault("nicht_moeglich", [])
        verteilung = gruppe.setdefault("verteilung", {})
        spieler_ids = verteilung.setdefault(datum, [])

        if state == Qt.PartiallyChecked:
            if datum not in nicht_moeglich:
                nicht_moeglich.append(datum)
            if spieler_id in spieler_ids:
                spieler_ids.remove(spieler_id)
        elif state == Qt.Checked:
            if datum in nicht_moeglich:
                nicht_moeglich.remove(datum)
            if spieler_id not in spieler_ids:
                spieler_ids.append(spieler_id)
        else:
            if datum in nicht_moeglich:
                nicht_moeglich.remove(datum)
            if spieler_id in spieler_ids:
                spieler_ids.remove(spieler_id)
        if not spieler_ids:
            verteilung.pop(datum, None)
        legacy_adapter.speichere_saison(self.saison)
        self._aktualisieren()