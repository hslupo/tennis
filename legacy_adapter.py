"""
Brücke zwischen der SQLite-Datenbank (repository/*) und der verschachtelten
Dict-Struktur, die die bestehenden Tk-Dialoge bisher direkt aus JSON gelesen
haben. So mussten die Dialoge nur ihre Lade-/Speicherfunktion anpassen, nicht
ihre interne Logik.

Erweiterung gegenüber dem alten JSON-Format: jeder Spieler-Eintrag in
gruppe["players"][spieler_id] trägt zusätzlich "anzeige_name" (effektiver
Spitzname: Gruppen-Override, sonst globaler Spitzname) und
"spitzname_override" (roher Override-Wert oder None), damit die UI keinen
separaten globalen Namens-Lookup mehr braucht, um Gruppenmitglieder korrekt
anzuzeigen.

last_group ist reiner UI-Zustand und wird bewusst nicht in der Datenbank
gespeichert (siehe Migrationsplan), sondern lokal in ui_state.json.
"""

import datetime
import json
import os
from pathlib import Path

from db.connection import connect, create_schema
from db.migrate_json_to_sqlite import WOCHENTAGE
from repository.gruppe_repository import GruppeRepository
from repository.saison_repository import SaisonRepository
from repository.spieler_repository import SpielerRepository
from repository.termin_repository import TerminRepository
from repository.verteilung_repository import VerteilungRepository
from services.termine_service import generiere_termine

WOCHENTAGE_UMKEHR = {wert: key for key, wert in WOCHENTAGE.items()}
WOCHENTAG_NAMEN = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"]

_ROOT = Path(__file__).parent
# Für isolierte Tests per TENNISVERTEILUNG_DB_PATH überschreibbar (vor dem Import setzen).
_DB_PATH = Path(os.environ.get("TENNISVERTEILUNG_DB_PATH", str(_ROOT / "tennisverteilung.db")))
_UI_STATE_PATH = _ROOT / "ui_state.json"

_neu = not _DB_PATH.exists()
_conn = connect(_DB_PATH)
if _neu:
    create_schema(_conn)

_saison_repo = SaisonRepository(_conn)
_gruppe_repo = GruppeRepository(_conn)
_spieler_repo = SpielerRepository(_conn)
_termin_repo = TerminRepository(_conn)
_verteilung_repo = VerteilungRepository(_conn)


def _iso_zu_dmy(iso_datum: str) -> str:
    return datetime.date.fromisoformat(iso_datum).strftime("%d.%m.%Y")


def _dmy_zu_iso(dmy_datum: str) -> str:
    return datetime.datetime.strptime(dmy_datum, "%d.%m.%Y").date().isoformat()


def _lade_ui_state() -> dict:
    if not _UI_STATE_PATH.exists():
        return {}
    try:
        return json.loads(_UI_STATE_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def _speichere_ui_state(state: dict) -> None:
    _UI_STATE_PATH.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")


def get_last_group(jahr: int) -> str:
    return _lade_ui_state().get(str(jahr), "")


def set_last_group(jahr: int, wochentag_key: str) -> None:
    state = _lade_ui_state()
    state[str(jahr)] = wochentag_key
    _speichere_ui_state(state)


def lade_saison(jahr: int) -> dict | None:
    saison_row = _saison_repo.get_by_jahr(jahr)
    if saison_row is None:
        return None

    groups: dict = {}
    for g in _gruppe_repo.fuer_saison(saison_row["id"]):
        wochentag_key = WOCHENTAGE_UMKEHR[g["wochentag"]]

        termine_dmy = generiere_termine(
            saison_row["start_date"], saison_row["end_date"], WOCHENTAG_NAMEN[g["wochentag"]]
        )
        termin_ids = _termin_repo.ids_fuer_daten(g["id"], (_dmy_zu_iso(d) for d in termine_dmy))

        players = {}
        for m in _gruppe_repo.mitglieder_mit_spielerdaten(g["id"]):
            nicht_verf_iso = _termin_repo.nicht_verfuegbare_iso_daten_fuer_spieler(g["id"], m["spieler_id"])
            players[m["spieler_id"]] = {
                "nicht_moeglich": [_iso_zu_dmy(iso) for iso in sorted(nicht_verf_iso)],
                "anzeige_name": m["anzeige_name"],
                "spitzname_override": m["spitzname_override"],
            }

        verteilung_iso = _verteilung_repo.fuer_gruppe(g["id"])
        verteilung_dmy = {_iso_zu_dmy(iso): sp_ids for iso, sp_ids in verteilung_iso.items()}

        groups[wochentag_key] = {
            "wochentag": g["name"],
            "platz": g["platz"],
            "startzeit": g["startzeit"],
            "endzeit": g["endzeit"],
            "seed": g["seed"],
            "players": players,
            "verteilung": verteilung_dmy,
        }
        del termin_ids  # nur zum Anlegen fehlender Termine gebraucht

    return {
        "jahr": saison_row["jahr"],
        "start_date": saison_row["start_date"],
        "end_date": saison_row["end_date"],
        "last_group": get_last_group(jahr),
        "groups": groups,
    }


def speichere_saison(saison: dict) -> None:
    jahr = saison["jahr"]
    saison_id = _saison_repo.upsert(jahr, saison["start_date"], saison["end_date"])
    set_last_group(jahr, saison.get("last_group") or "")

    for wochentag_key, gruppe in saison.get("groups", {}).items():
        wochentag_int = WOCHENTAGE[wochentag_key]
        gruppe_id = _gruppe_repo.upsert(
            saison_id,
            wochentag_int,
            name=gruppe.get("wochentag", wochentag_key.capitalize()),
            platz=gruppe.get("platz", ""),
            startzeit=gruppe.get("startzeit", ""),
            endzeit=gruppe.get("endzeit", ""),
            seed=gruppe.get("seed"),
        )

        gewuenschte_mitglieder = set(gruppe.get("players", {}).keys())
        aktuelle_mitglieder = set(_gruppe_repo.mitglieder_ids(gruppe_id))
        for spieler_id in gewuenschte_mitglieder - aktuelle_mitglieder:
            _gruppe_repo.mitglied_hinzufuegen(gruppe_id, spieler_id)
        for spieler_id in aktuelle_mitglieder - gewuenschte_mitglieder:
            _gruppe_repo.mitglied_entfernen(gruppe_id, spieler_id)

        for spieler_id, eintrag in gruppe.get("players", {}).items():
            if "spitzname_override" in eintrag:
                _gruppe_repo.spitzname_override_setzen(gruppe_id, spieler_id, eintrag.get("spitzname_override"))

        alle_dmy = set(gruppe.get("verteilung", {}).keys())
        for eintrag in gruppe.get("players", {}).values():
            alle_dmy.update(eintrag.get("nicht_moeglich", []))
        termin_ids = _termin_repo.ids_fuer_daten(gruppe_id, (_dmy_zu_iso(d) for d in alle_dmy))

        for spieler_id, eintrag in gruppe.get("players", {}).items():
            gewuenscht_iso = {_dmy_zu_iso(d) for d in eintrag.get("nicht_moeglich", [])}
            vorhanden_iso = _termin_repo.nicht_verfuegbare_iso_daten_fuer_spieler(gruppe_id, spieler_id)
            for iso in gewuenscht_iso - vorhanden_iso:
                _termin_repo.nicht_verfuegbar_setzen(termin_ids[iso], spieler_id)
            for iso in vorhanden_iso - gewuenscht_iso:
                _termin_repo.nicht_verfuegbar_entfernen(termin_ids[iso], spieler_id)

        for datum_dmy, spieler_ids in gruppe.get("verteilung", {}).items():
            _verteilung_repo.ersetzen_fuer_termin(termin_ids[_dmy_zu_iso(datum_dmy)], spieler_ids)


def lade_spieler_namen() -> dict[int, str]:
    """id -> globaler Spitzname (ohne Gruppen-Override), für Übersichten über alle Spieler."""
    return {row["id"]: row["spitzname"] for row in _spieler_repo.alle()}


def spieler_alle() -> list[dict]:
    return [dict(row) for row in _spieler_repo.alle()]


def spieler_erstellen(name: str = "", spitzname: str = "", telefon: str = "", mobil: str = "", email: str = "") -> int:
    return _spieler_repo.erstellen(name, spitzname, telefon, mobil, email)


def spieler_aktualisieren(spieler_id: int, name: str, spitzname: str, telefon: str, mobil: str, email: str = "") -> None:
    _spieler_repo.aktualisieren(spieler_id, name, spitzname, telefon, mobil, email)


def spieler_loeschen(spieler_id: int) -> None:
    _spieler_repo.loeschen(spieler_id)
