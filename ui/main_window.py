import datetime

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QComboBox,
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
from ui.spieler_termine_dialog import SpielerTermineDialog

WOCHENTAGE = [
    "Montag", "Dienstag", "Mittwoch",
    "Donnerstag", "Freitag", "Samstag", "Sonntag",
]

NEU_MARKER = "* NEU *"


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Tennisrunden Verwaltung")
        self.resize(1100, 750)

        jahre = legacy_adapter.alle_saison_jahre()
        self.jahr = jahre[0] if jahre else datetime.date.today().year
        self.saison: dict | None = None
        self.wochentag_key: str | None = None
        self._gruppen_keys: list[str] = []
        self._saison_jahre: list[int] = []
        self.spieler_namen: dict[int, str] = legacy_adapter.lade_spieler_namen()

        central = QWidget()
        self.setCentralWidget(central)
        root_layout = QVBoxLayout(central)

        root_layout.addLayout(self._baue_topleiste())

        self.heading_label = QLabel()
        self.heading_label.setStyleSheet("font-size: 16pt; font-weight: bold;")
        root_layout.addWidget(self.heading_label)

        self.main_area = QWidget()
        self.main_layout = QVBoxLayout(self.main_area)
        root_layout.addWidget(self.main_area, stretch=1)

        self.refresh()

    # ---------- Menü-Leiste ----------
    def _baue_topleiste(self) -> QHBoxLayout:
        row = QHBoxLayout()

        btn_spieler = QPushButton("Spieler")
        btn_spieler.clicked.connect(self._oeffne_spielerliste)
        row.addWidget(btn_spieler)

        btn_spieler_termine = QPushButton("Spieler-Termine")
        btn_spieler_termine.clicked.connect(self._spieler_termine_anzeigen)
        row.addWidget(btn_spieler_termine)

        row.addWidget(QLabel("Saison:"))
        self.saison_combo = QComboBox()
        self.saison_combo.currentIndexChanged.connect(self._saison_combo_gewaehlt)
        row.addWidget(self.saison_combo)

        row.addWidget(QLabel("Gruppe:"))
        self.gruppe_combo = QComboBox()
        self.gruppe_combo.currentIndexChanged.connect(self._gruppe_combo_gewaehlt)
        row.addWidget(self.gruppe_combo)

        row.addStretch()
        return row

    def _saison_text(self) -> str:
        if not self.saison:
            return f"Saison {self.jahr}"
        return f"Saison {self.saison['start_date'][:4]}/{self.saison['end_date'][:4]}"

    # ---------- Zustand / Hauptbereich ----------
    def refresh(self):
        self._layout_leeren(self.main_layout)

        state, saison = ermittle_state(self.jahr)
        self.saison = saison

        vorhandene_keys = list(saison["groups"].keys()) if saison and "groups" in saison else []
        ziel_key = None
        if state == "SHOW_GROUP":
            ziel_key = saison.get("last_group") or vorhandene_keys[0]
            if ziel_key not in saison["groups"]:
                ziel_key = vorhandene_keys[0]

        self._aktualisiere_saison_combo()
        self._aktualisiere_gruppe_combo(vorhandene_keys, ziel_key, state)

        if state == "NO_SAISON":
            self.wochentag_key = None
            self.heading_label.setText(f"{self._saison_text()}: noch nicht angelegt")
            self.main_layout.addWidget(QLabel("Noch keine Saison angelegt"))
            return
        if state == "NO_GROUP":
            self.wochentag_key = None
            self.heading_label.setText(f"{self._saison_text()} – neue Gruppe anlegen")
            self._zeige_wochentag_auswahl()
            return

        self._zeige_gruppe(ziel_key)

    def _layout_leeren(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                self._layout_leeren(item.layout())

    # ---------- Saison-Auswahl ----------
    def _aktualisiere_saison_combo(self):
        self._saison_jahre = legacy_adapter.alle_saison_jahre()
        self.saison_combo.blockSignals(True)
        self.saison_combo.clear()
        self.saison_combo.addItem(NEU_MARKER)
        for jahr in self._saison_jahre:
            self.saison_combo.addItem(str(jahr))
        if self.jahr in self._saison_jahre:
            self.saison_combo.setCurrentIndex(self._saison_jahre.index(self.jahr) + 1)
        else:
            self.saison_combo.setCurrentIndex(-1)
        self.saison_combo.blockSignals(False)

    def _saison_combo_gewaehlt(self, index: int):
        if index < 0:
            return
        text = self.saison_combo.itemText(index)
        if text == NEU_MARKER:
            self._neue_saison()
            return
        jahr = int(text)
        if jahr != self.jahr:
            self.jahr = jahr
            self.refresh()

    def _neue_saison(self):
        vorschlag_jahr = (max(self._saison_jahre) + 1) if self._saison_jahre else datetime.date.today().year

        def on_saved():
            self.jahr = vorschlag_jahr

        dlg = SaisonDialog(self, vorschlag_jahr, on_saved=on_saved)
        dlg.exec()
        self.refresh()

    # ---------- Gruppen-Auswahl ----------
    def _aktualisiere_gruppe_combo(self, vorhandene_keys: list[str], ziel_key: str | None, state: str):
        self._gruppen_keys = vorhandene_keys
        self.gruppe_combo.blockSignals(True)
        self.gruppe_combo.clear()
        for key in vorhandene_keys:
            self.gruppe_combo.addItem(self.saison["groups"][key]["wochentag"])
        self.gruppe_combo.addItem(NEU_MARKER)
        self.gruppe_combo.setEnabled(state != "NO_SAISON")
        if ziel_key in vorhandene_keys:
            self.gruppe_combo.setCurrentIndex(vorhandene_keys.index(ziel_key))
        elif state != "NO_SAISON":
            self.gruppe_combo.setCurrentIndex(len(vorhandene_keys))
        else:
            self.gruppe_combo.setCurrentIndex(-1)
        self.gruppe_combo.blockSignals(False)

    def _gruppe_combo_gewaehlt(self, index: int):
        if index < 0:
            return

        if index >= len(self._gruppen_keys):
            self.wochentag_key = None
            self.heading_label.setText(f"{self._saison_text()} – neue Gruppe anlegen")
            self._zeige_wochentag_auswahl()
            return

        key = self._gruppen_keys[index]
        if key != self.wochentag_key:
            self._zeige_gruppe(key)

    # ---------- Wochentag-Auswahl für neue Gruppe ----------
    def _zeige_wochentag_auswahl(self):
        self._layout_leeren(self.main_layout)
        self.main_layout.addWidget(QLabel("<b>Bitte Wochentag wählen, um eine neue Gruppe anzulegen:</b>"))

        vorhandene = set(self.saison.get("groups", {}).keys()) if self.saison else set()
        liste = QListWidget()
        for tag in WOCHENTAGE:
            if tag.lower() not in vorhandene:
                liste.addItem(tag)
        liste.itemClicked.connect(self._wochentag_gewaehlt)
        self.main_layout.addWidget(liste)

    def _wochentag_gewaehlt(self, item: QListWidgetItem):
        wochentag = item.text()
        dlg = GruppeDialog(self, self.jahr, wochentag, on_saved=self.refresh)
        dlg.exec()
        self.refresh()

    # ---------- Gruppe anzeigen ----------
    def _zeige_gruppe(self, wochentag_key: str):
        self._layout_leeren(self.main_layout)
        self.wochentag_key = wochentag_key
        gruppe = self.saison["groups"][wochentag_key]

        # last_group merken
        if self.saison.get("last_group") != wochentag_key:
            self.saison["last_group"] = wochentag_key
            legacy_adapter.set_last_group(self.jahr, wochentag_key)

        self.heading_label.setText(f"{self._saison_text()} – Gruppe {gruppe['wochentag']}")

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

    # ---------- Aktionen ----------
    def _oeffne_spielerliste(self):
        dlg = SpielerDialog(self, on_change=self._spieler_namen_neu_laden)
        dlg.exec()

    def _spieler_namen_neu_laden(self):
        self.spieler_namen = legacy_adapter.lade_spieler_namen()

    def _spieler_termine_anzeigen(self):
        spieler_id = next(
            (
                pid
                for gruppe in self.saison.get("groups", {}).values()
                for pid, eintrag in gruppe.get("players", {}).items()
                if eintrag.get("name") == "Horst Schmidt"
            ),
            None,
        ) if self.saison else None
        dlg = SpielerTermineDialog(self, self.saison or {}, self.spieler_namen, spieler_id)
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
