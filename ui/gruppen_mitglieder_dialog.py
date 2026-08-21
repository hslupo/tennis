from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QListWidget, QListWidgetItem, QPushButton, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QMessageBox, QInputDialog, QAbstractItemView,
)

import legacy_adapter


class SpielerAuswahlDialog(QDialog):
    """Durchsuchbare Mehrfachauswahl, z.B. um mehrere Spieler auf einmal zu einer
    Gruppe hinzuzufügen (Strg/Shift+Klick oder Ziehen für mehrere Einträge)."""

    def __init__(self, parent, titel: str, kandidaten: list[tuple[int, str]]):
        super().__init__(parent)
        self.setWindowTitle(titel)
        self.resize(300, 400)
        self._alle_kandidaten = kandidaten
        self._ausgewaehlte_ids: set[int] = set()
        self.gewaehlte_ids: list[int] = []

        layout = QVBoxLayout(self)
        such_row = QHBoxLayout()
        such_row.addWidget(QLabel("Suche:"))
        self.such_edit = QLineEdit()
        self.such_edit.textChanged.connect(self._filtern)
        such_row.addWidget(self.such_edit)
        layout.addLayout(such_row)

        layout.addWidget(QLabel("Mehrfachauswahl möglich (Strg/Shift+Klick)."))

        self.listbox = QListWidget()
        self.listbox.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.listbox.itemSelectionChanged.connect(self._auswahl_gemerkt)
        self.listbox.itemDoubleClicked.connect(lambda _: self._ok())
        layout.addWidget(self.listbox)

        btn_row = QHBoxLayout()
        btn_ok = QPushButton("OK")
        btn_ok.clicked.connect(self._ok)
        btn_row.addWidget(btn_ok)
        btn_abbrechen = QPushButton("Abbrechen")
        btn_abbrechen.clicked.connect(self.reject)
        btn_row.addWidget(btn_abbrechen)
        layout.addLayout(btn_row)

        self._filtern("")
        self.such_edit.setFocus()

    def _auswahl_gemerkt(self):
        """Merkt sich die Auswahl auch über Suchtext-Änderungen (Listeneinträge werden
        dabei neu aufgebaut) hinweg."""
        sichtbare_ids = {self.listbox.item(i).data(Qt.UserRole) for i in range(self.listbox.count())}
        neu_ausgewaehlt = {item.data(Qt.UserRole) for item in self.listbox.selectedItems()}
        self._ausgewaehlte_ids = (self._ausgewaehlte_ids - sichtbare_ids) | neu_ausgewaehlt

    def _filtern(self, text: str):
        self.listbox.blockSignals(True)
        self.listbox.clear()
        suche = text.strip().lower()
        for pid, name in self._alle_kandidaten:
            if suche and suche not in name.lower():
                continue
            item = QListWidgetItem(name)
            item.setData(Qt.UserRole, pid)
            self.listbox.addItem(item)
            if pid in self._ausgewaehlte_ids:
                item.setSelected(True)
        self.listbox.blockSignals(False)

    def _ok(self):
        self._auswahl_gemerkt()
        self.gewaehlte_ids = list(self._ausgewaehlte_ids)
        self.accept()


class GruppenMitgliederDialog(QDialog):
    """Spieler einer Gruppe hinzufügen/entfernen, Spitzname pro Gruppe anpassen
    (Ersatz für spieler_verwalten_dialog.py)."""

    def __init__(self, parent, jahr: int, wochentag_key: str, saison: dict, spieler_namen: dict, on_change):
        super().__init__(parent)
        self.jahr = jahr
        self.wochentag_key = wochentag_key
        self.saison = saison
        self.spieler_namen = spieler_namen
        self.on_change = on_change
        self.gruppe = saison["groups"][wochentag_key]

        self.setWindowTitle("Gruppenspieler verwalten")
        self.resize(400, 500)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(f"<b>Gruppe {self.gruppe['wochentag']}</b>"))

        self.listbox = QListWidget()
        self.listbox.itemDoubleClicked.connect(self._spitzname_anpassen)
        layout.addWidget(self.listbox)

        layout.addWidget(QLabel(
            "Doppelklick auf einen Spieler, um seinen Spitznamen\n"
            "nur für diese Gruppe anzupassen."
        ))

        btn_row = QHBoxLayout()
        btn_hinzufuegen = QPushButton("Hinzufügen")
        btn_hinzufuegen.clicked.connect(self._hinzufuegen)
        btn_row.addWidget(btn_hinzufuegen)
        btn_loeschen = QPushButton("Löschen")
        btn_loeschen.clicked.connect(self._loeschen)
        btn_row.addWidget(btn_loeschen)
        layout.addLayout(btn_row)

        self._refresh_list()

    def _refresh_list(self):
        self.listbox.clear()
        for pid, eintrag in sorted(self.gruppe["players"].items(), key=lambda kv: kv[1]["anzeige_name"].lower()):
            anzeige_name = eintrag["anzeige_name"]
            voller_name = eintrag.get("name", "")
            if voller_name and voller_name != anzeige_name:
                text = f"{anzeige_name} ({voller_name})"
            else:
                text = anzeige_name
            item = QListWidgetItem(text)
            item.setData(Qt.UserRole, pid)
            self.listbox.addItem(item)

    def _hinzufuegen(self):
        kandidaten = [
            (pid, name) for pid, name in self.spieler_namen.items()
            if pid not in self.gruppe["players"]
        ]
        if not kandidaten:
            QMessageBox.information(self, "Hinweis", "Alle Spieler sind bereits in dieser Gruppe.")
            return

        dlg = SpielerAuswahlDialog(self, "Spieler hinzufügen", kandidaten)
        if dlg.exec() != QDialog.Accepted or not dlg.gewaehlte_ids:
            return

        for pid in dlg.gewaehlte_ids:
            self.gruppe["players"][pid] = {
                "nicht_moeglich": [],
                "anzeige_name": self.spieler_namen.get(pid, str(pid)),
                "spitzname_override": None,
            }
        self._speichern_und_neu_laden()

    def _loeschen(self):
        item = self.listbox.currentItem()
        if item is None:
            QMessageBox.warning(self, "Hinweis", "Bitte einen Spieler auswählen.")
            return
        pid = item.data(Qt.UserRole)
        anzeige_name = self.gruppe["players"][pid]["anzeige_name"]
        if QMessageBox.question(
            self, "Bestätigen", f"Soll Spieler {anzeige_name} wirklich entfernt werden?"
        ) == QMessageBox.Yes:
            del self.gruppe["players"][pid]
            self._speichern_und_neu_laden()

    def _spitzname_anpassen(self, item: QListWidgetItem):
        pid = item.data(Qt.UserRole)
        eintrag = self.gruppe["players"][pid]
        global_spitzname = self.spieler_namen.get(pid, str(pid))

        neuer_wert, ok = QInputDialog.getText(
            self, "Spitzname für diese Gruppe",
            f"Anzeigename in dieser Gruppe (leer = Standard '{global_spitzname}'):",
            text=eintrag.get("spitzname_override") or "",
        )
        if not ok:
            return

        eintrag["spitzname_override"] = neuer_wert.strip() or None
        self._speichern_und_neu_laden()

    def _speichern_und_neu_laden(self):
        legacy_adapter.speichere_saison(self.saison)
        self.saison = legacy_adapter.lade_saison(self.jahr)
        self.gruppe = self.saison["groups"][self.wochentag_key]
        self._refresh_list()
        self.on_change(self.saison)
