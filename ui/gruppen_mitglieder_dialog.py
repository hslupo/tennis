from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QListWidget, QListWidgetItem, QPushButton, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QMessageBox, QInputDialog,
)

import legacy_adapter


class SpielerAuswahlDialog(QDialog):
    """Durchsuchbare Auswahlliste, z.B. um einen Spieler zu einer Gruppe hinzuzufügen."""

    def __init__(self, parent, titel: str, kandidaten: list[tuple[int, str]]):
        super().__init__(parent)
        self.setWindowTitle(titel)
        self.resize(300, 400)
        self._alle_kandidaten = kandidaten
        self.gewaehlte_id = None

        layout = QVBoxLayout(self)
        such_row = QHBoxLayout()
        such_row.addWidget(QLabel("Suche:"))
        self.such_edit = QLineEdit()
        self.such_edit.textChanged.connect(self._filtern)
        such_row.addWidget(self.such_edit)
        layout.addLayout(such_row)

        self.listbox = QListWidget()
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

    def _filtern(self, text: str):
        self.listbox.clear()
        suche = text.strip().lower()
        for pid, name in self._alle_kandidaten:
            if suche and suche not in name.lower():
                continue
            item = QListWidgetItem(name)
            item.setData(Qt.UserRole, pid)
            self.listbox.addItem(item)
        if self.listbox.count():
            self.listbox.setCurrentRow(0)

    def _ok(self):
        item = self.listbox.currentItem()
        if item is not None:
            self.gewaehlte_id = item.data(Qt.UserRole)
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
            item = QListWidgetItem(eintrag["anzeige_name"])
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
        if dlg.exec() != QDialog.Accepted or dlg.gewaehlte_id is None:
            return

        pid = dlg.gewaehlte_id
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
