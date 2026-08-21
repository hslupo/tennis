import datetime

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QComboBox, QMessageBox,
)

import legacy_adapter
from utils import ermittle_state
from ui.saison_dialog import SaisonDialog
from ui.gruppe_dialog import GruppeDialog
from ui.spieler_dialog import SpielerDialog
from ui.gruppen_mitglieder_dialog import GruppenMitgliederDialog
from ui.verfuegbarkeit_view import VerfuegbarkeitView
from ui.verteilung_dialog import VerteilungDialog
from ui.auswertung_dialog import AuswertungDialog

WOCHENTAGE = [
    "Montag", "Dienstag", "Mittwoch",
    "Donnerstag", "Freitag", "Samstag", "Sonntag",
]


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Tennisrunden Verwaltung")
        self.resize(1100, 750)

        self.jahr = datetime.date.today().year
        self.saison: dict | None = None
        self.wochentag_key: str | None = None
        self.spieler_namen: dict[int, str] = legacy_adapter.lade_spieler_namen()

        central = QWidget()
        self.setCentralWidget(central)
        root_layout = QHBoxLayout(central)

        root_layout.addWidget(self._baue_menue())

        self.main_area = QWidget()
        self.main_layout = QVBoxLayout(self.main_area)
        root_layout.addWidget(self.main_area, stretch=1)

        self.refresh()

    # ---------- Menü ----------
    def _baue_menue(self) -> QWidget:
        menu_widget = QWidget()
        menu_widget.setFixedWidth(220)
        menu_layout = QVBoxLayout(menu_widget)

        titel = QLabel("<b>Verwalten</b>")
        menu_layout.addWidget(titel)

        btn_spieler = QPushButton("Spieler")
        btn_spieler.clicked.connect(self._oeffne_spielerliste)
        menu_layout.addWidget(btn_spieler)

        menu_layout.addWidget(QLabel("<b>Gruppen:</b>"))

        self.gruppen_listbox = QListWidget()
        menu_layout.addWidget(self.gruppen_listbox)

        self.btn_gruppe_neu = QPushButton("Gruppe NEU")
        self.btn_gruppe_neu.clicked.connect(self._neue_gruppe)
        menu_layout.addWidget(self.btn_gruppe_neu)

        btn_saison = QPushButton("Saison")
        btn_saison.clicked.connect(self._oeffne_saison)
        menu_layout.addWidget(btn_saison)

        menu_layout.addStretch()
        return menu_widget

    # ---------- Zustand / Hauptbereich ----------
    def refresh(self):
        self._layout_leeren(self.main_layout)

        state, saison = ermittle_state(self.jahr)
        self.saison = saison

        vorhandene_keys = list(saison["groups"].keys()) if saison and "groups" in saison else []

        self.gruppen_listbox.clear()
        self.gruppen_listbox.setEnabled(state != "NO_SAISON")
        self.btn_gruppe_neu.setEnabled(state != "NO_SAISON")
        for tag in WOCHENTAGE:
            if tag.lower() not in vorhandene_keys:
                self.gruppen_listbox.addItem(tag)

        if state == "NO_SAISON":
            self.main_layout.addWidget(QLabel("Noch keine Saison angelegt"))
            return
        if state == "NO_GROUP":
            self.main_layout.addWidget(QLabel("Noch keine Gruppen vorhanden"))
            return

        key = saison.get("last_group") or (vorhandene_keys[0] if vorhandene_keys else "")
        if key and key in saison["groups"]:
            self._zeige_gruppe(key)
        else:
            self.main_layout.addWidget(QLabel("Keine Gruppen vorhanden"))

    def _layout_leeren(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                self._layout_leeren(item.layout())

    # ---------- Gruppe anzeigen ----------
    def _zeige_gruppe(self, wochentag_key: str):
        self._layout_leeren(self.main_layout)
        self.wochentag_key = wochentag_key
        gruppe = self.saison["groups"][wochentag_key]

        # last_group merken
        if self.saison.get("last_group") != wochentag_key:
            self.saison["last_group"] = wochentag_key
            legacy_adapter.set_last_group(self.jahr, wochentag_key)

        top_row = QHBoxLayout()
        self._gruppen_keys = list(self.saison["groups"].keys())
        self.gruppen_combo = QComboBox()
        for k in self._gruppen_keys:
            self.gruppen_combo.addItem(self.saison["groups"][k]["wochentag"])
        self.gruppen_combo.setCurrentIndex(self._gruppen_keys.index(wochentag_key))
        self.gruppen_combo.currentIndexChanged.connect(self._gruppen_wechsel)
        top_row.addWidget(self.gruppen_combo)
        top_row.addStretch()
        self.main_layout.addLayout(top_row)

        info_label = QLabel(f"<b>Platz {gruppe['platz']} – {gruppe['startzeit']} bis {gruppe['endzeit']}</b>")
        self.main_layout.addWidget(info_label)

        content_row = QHBoxLayout()
        self.main_layout.addLayout(content_row, stretch=1)

        # links: Spielerliste + Aktionen
        links_widget = QWidget()
        links_widget.setFixedWidth(240)
        links_layout = QVBoxLayout(links_widget)

        self.spieler_listbox = QListWidget()
        for pid, eintrag in sorted(gruppe["players"].items(), key=lambda kv: kv[1]["anzeige_name"].lower()):
            item = QListWidgetItem(eintrag["anzeige_name"])
            item.setData(Qt.UserRole, pid)
            self.spieler_listbox.addItem(item)
        links_layout.addWidget(self.spieler_listbox)

        btn_verwalten = QPushButton("Spieler verwalten")
        btn_verwalten.clicked.connect(self._spieler_verwalten)
        links_layout.addWidget(btn_verwalten)

        btn_auswertung = QPushButton("Auswertung")
        btn_auswertung.clicked.connect(self._auswertung_anzeigen)
        links_layout.addWidget(btn_auswertung)

        btn_verteilung = QPushButton("Verteilung planen")
        btn_verteilung.clicked.connect(self._verteilung_planen)
        links_layout.addWidget(btn_verteilung)

        links_layout.addStretch()
        content_row.addWidget(links_widget)

        # rechts: Verfügbarkeits-Matrix
        self.verfuegbarkeit_view = VerfuegbarkeitView(self.saison, wochentag_key)
        content_row.addWidget(self.verfuegbarkeit_view, stretch=1)

    def _gruppen_wechsel(self, index: int):
        key = self._gruppen_keys[index]
        if key != self.wochentag_key:
            self._zeige_gruppe(key)

    # ---------- Aktionen ----------
    def _oeffne_spielerliste(self):
        dlg = SpielerDialog(self, on_change=self._spieler_namen_neu_laden)
        dlg.exec()

    def _spieler_namen_neu_laden(self):
        self.spieler_namen = legacy_adapter.lade_spieler_namen()

    def _neue_gruppe(self):
        item = self.gruppen_listbox.currentItem()
        if item is None:
            QMessageBox.warning(self, "Hinweis", "Bitte zuerst einen Wochentag aus der Liste auswählen.")
            return
        dlg = GruppeDialog(self, self.jahr, item.text(), on_saved=self.refresh)
        dlg.exec()

    def _oeffne_saison(self):
        dlg = SaisonDialog(self, self.jahr, on_saved=self.refresh)
        dlg.exec()

    def _spieler_verwalten(self):
        def on_change(neue_saison):
            self.saison = neue_saison
            self._zeige_gruppe(self.wochentag_key)

        dlg = GruppenMitgliederDialog(self, self.jahr, self.wochentag_key, self.saison, self.spieler_namen, on_change)
        dlg.exec()
        # Für den Fall, dass der Dialog ohne Änderung geschlossen wurde, trotzdem konsistent anzeigen.
        self.saison = legacy_adapter.lade_saison(self.jahr)
        self._zeige_gruppe(self.wochentag_key)

    def _auswertung_anzeigen(self):
        gruppe = self.saison["groups"][self.wochentag_key]
        anzeige_namen = {pid: eintrag["anzeige_name"] for pid, eintrag in gruppe["players"].items()}
        dlg = AuswertungDialog(self, self.saison, gruppe, anzeige_namen)
        dlg.exec()

    def _verteilung_planen(self):
        gruppe = self.saison["groups"][self.wochentag_key]
        anzeige_namen = {pid: eintrag["anzeige_name"] for pid, eintrag in gruppe["players"].items()}

        def on_change():
            self.saison = legacy_adapter.lade_saison(self.jahr)
            self._zeige_gruppe(self.wochentag_key)

        dlg = VerteilungDialog(self, self.jahr, self.wochentag_key, self.saison, anzeige_namen, on_change)
        dlg.exec()
