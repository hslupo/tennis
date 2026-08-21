from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QListWidget, QListWidgetItem, QPushButton, QVBoxLayout, QMessageBox,
    QFormLayout, QLineEdit, QMenu,
)

import legacy_adapter


class SpielerBearbeitenDialog(QDialog):
    def __init__(self, parent, spieler: dict):
        super().__init__(parent)
        self.spieler = spieler
        self.setWindowTitle("Spieler bearbeiten")

        layout = QVBoxLayout(self)
        form = QFormLayout()
        layout.addLayout(form)

        self.name_edit = QLineEdit(spieler["name"])
        form.addRow("Vollständiger Name:", self.name_edit)

        self.spitzname_edit = QLineEdit(spieler["spitzname"])
        form.addRow("Spitzname:", self.spitzname_edit)

        self.telefon_edit = QLineEdit(spieler["telefon"])
        form.addRow("Telefon:", self.telefon_edit)

        self.mobil_edit = QLineEdit(spieler["mobil"])
        form.addRow("Mobil:", self.mobil_edit)

        btn_speichern = QPushButton("Speichern")
        btn_speichern.clicked.connect(self._speichern)
        layout.addWidget(btn_speichern)

    def _speichern(self):
        spitzname = self.spitzname_edit.text().strip()
        if not spitzname:
            QMessageBox.warning(self, "Fehler", "Bitte einen Spitznamen angeben.")
            return
        legacy_adapter.spieler_aktualisieren(
            self.spieler["id"],
            name=self.name_edit.text().strip(),
            spitzname=spitzname,
            telefon=self.telefon_edit.text().strip(),
            mobil=self.mobil_edit.text().strip(),
        )
        self.accept()


class SpielerDialog(QDialog):
    """Verwaltung des globalen Spielerstamms (Ersatz für tennisspieler.py)."""

    def __init__(self, parent, on_change=None):
        super().__init__(parent)
        self.on_change = on_change
        self.setWindowTitle("Spielerliste verwalten")
        self.resize(400, 500)

        layout = QVBoxLayout(self)

        btn_neu = QPushButton("Neuer Spieler")
        btn_neu.clicked.connect(self._neuer_spieler)
        layout.addWidget(btn_neu)

        self.listbox = QListWidget()
        self.listbox.itemDoubleClicked.connect(self._bearbeiten)
        self.listbox.setContextMenuPolicy(Qt.CustomContextMenu)
        self.listbox.customContextMenuRequested.connect(self._kontextmenue)
        layout.addWidget(self.listbox)

        self._aktualisiere_liste()

    def _aktualisiere_liste(self):
        self.listbox.clear()
        for sp in legacy_adapter.spieler_alle():
            if sp["name"] and sp["name"] != sp["spitzname"]:
                text = f"{sp['spitzname']} ({sp['name']})"
            else:
                text = sp["spitzname"] or "(ohne Spitznamen)"
            item = QListWidgetItem(text)
            item.setData(Qt.UserRole, sp["id"])
            self.listbox.addItem(item)
        if self.on_change:
            self.on_change()

    def _neuer_spieler(self):
        neue_id = legacy_adapter.spieler_erstellen(name="", spitzname="", telefon="", mobil="")
        spieler = next(sp for sp in legacy_adapter.spieler_alle() if sp["id"] == neue_id)
        dlg = SpielerBearbeitenDialog(self, spieler)
        dlg.exec()
        self._aktualisiere_liste()

    def _bearbeiten(self, item: QListWidgetItem):
        spieler_id = item.data(Qt.UserRole)
        spieler = next(sp for sp in legacy_adapter.spieler_alle() if sp["id"] == spieler_id)
        dlg = SpielerBearbeitenDialog(self, spieler)
        dlg.exec()
        self._aktualisiere_liste()

    def _kontextmenue(self, pos):
        item = self.listbox.itemAt(pos)
        if item is None:
            return
        menu = QMenu(self)
        loeschen_action = menu.addAction("Löschen")
        action = menu.exec(self.listbox.mapToGlobal(pos))
        if action == loeschen_action:
            self._loeschen(item)

    def _loeschen(self, item: QListWidgetItem):
        spieler_id = item.data(Qt.UserRole)
        if QMessageBox.question(
            self, "Löschen",
            f"Soll Spieler '{item.text()}' wirklich gelöscht werden?\n"
            "Er wird dabei auch aus allen Gruppen entfernt.",
        ) == QMessageBox.Yes:
            legacy_adapter.spieler_loeschen(spieler_id)
            self._aktualisiere_liste()
