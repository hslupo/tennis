"""
Einmalige Migration der bestehenden Jahres-JSON-Dateien (<jahr>.json) und des
globalen Spielerstamms (spieler.json) nach SQLite.

Aufruf (aus dem Projektwurzelverzeichnis):
    python -m db.migrate_json_to_sqlite [--db tennisverteilung.db] [--force]

Ohne explizit angegebene Saison-Dateien werden alle Dateien der Form
<jahr>.json (z.B. 2025.json, 2026.json) im Projektwurzelverzeichnis migriert.
Backup-/Altdateien wie "alt_2025.json" oder "2025 ori.json" matchen dieses
Muster nicht und werden bewusst ignoriert.
"""

import argparse
import json
import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path

from db.connection import connect, create_schema

WOCHENTAGE = {
    "montag": 0,
    "dienstag": 1,
    "mittwoch": 2,
    "donnerstag": 3,
    "freitag": 4,
    "samstag": 5,
    "sonntag": 6,
}


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def parse_datum(datum_str: str) -> str:
    return datetime.strptime(datum_str, "%d.%m.%Y").date().isoformat()


def find_default_season_files(root: Path) -> list[Path]:
    return sorted(p for p in root.glob("*.json") if re.fullmatch(r"\d{4}\.json", p.name))


def _wirkt_wie_voller_name(wert: str) -> bool:
    """Heuristik: enthält ein Leerzeichen und keine Ziffer -> vermutlich ein Name, keine Telefonnummer."""
    return bool(wert) and " " in wert and not any(zeichen.isdigit() for zeichen in wert)


def migrate_spieler(conn, spieler_json_path: Path) -> dict[str, int]:
    mapping: dict[str, int] = {}
    for eintrag in load_json(spieler_json_path):
        spitzname = eintrag["name"]
        telefon = eintrag.get("telefon", "")
        mobil = eintrag.get("mobil", "")
        voller_name = spitzname

        # In den bestehenden Daten steckt in Einzelfällen ein voller Name im
        # Telefon-/Mobil-Feld (vermutlich mangels eines eigenen Namensfelds).
        if _wirkt_wie_voller_name(telefon):
            print(f"  HINWEIS: Telefon-Feld von '{spitzname}' sieht nach einem vollen Namen aus "
                  f"('{telefon}') -> als Name übernommen, Telefon-Feld geleert")
            voller_name = telefon
            telefon = ""
        elif _wirkt_wie_voller_name(mobil):
            print(f"  HINWEIS: Mobil-Feld von '{spitzname}' sieht nach einem vollen Namen aus "
                  f"('{mobil}') -> als Name übernommen, Mobil-Feld geleert")
            voller_name = mobil
            mobil = ""

        email = eintrag.get("email", "")

        cur = conn.execute(
            "INSERT INTO spieler (name, spitzname, telefon, mobil, email) VALUES (?, ?, ?, ?, ?)",
            (voller_name, spitzname, telefon, mobil, email),
        )
        mapping[eintrag["id"]] = cur.lastrowid
    return mapping


def get_or_create_spieler_id(conn, spieler_map: dict[str, int], alt_id: str) -> int:
    if alt_id in spieler_map:
        return spieler_map[alt_id]
    print(f"  WARNUNG: Spieler-ID '{alt_id}' fehlt in spieler.json, lege Platzhalter-Datensatz an")
    cur = conn.execute(
        "INSERT INTO spieler (name, spitzname, telefon, mobil, email) VALUES (?, ?, '', '', '')",
        (alt_id, alt_id),
    )
    spieler_map[alt_id] = cur.lastrowid
    return cur.lastrowid


def migrate_saison_file(conn, path: Path, spieler_map: dict[str, int], stats: dict) -> None:
    data = load_json(path)

    cur = conn.execute(
        "INSERT INTO saison (jahr, start_date, end_date) VALUES (?, ?, ?)",
        (data["jahr"], data["start_date"], data["end_date"]),
    )
    saison_id = cur.lastrowid
    stats["saisons"] += 1

    for wochentag_key, gruppe in data.get("groups", {}).items():
        wochentag_int = WOCHENTAGE.get(wochentag_key)
        if wochentag_int is None:
            raise ValueError(f"{path.name}: unbekannter Wochentag-Key '{wochentag_key}'")
        anzeige_name = gruppe.get("wochentag", wochentag_key.capitalize())

        cur = conn.execute(
            """INSERT INTO gruppe (saison_id, name, wochentag, platz, startzeit, endzeit, seed)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                saison_id,
                anzeige_name,
                wochentag_int,
                gruppe.get("platz", ""),
                gruppe.get("startzeit", ""),
                gruppe.get("endzeit", ""),
                gruppe.get("seed"),
            ),
        )
        gruppe_id = cur.lastrowid
        stats["gruppen"] += 1

        # Termine = Vereinigung aus verteilung-Keys und allen nicht_moeglich-Daten.
        # Damit geht kein Termin verloren, unabhängig davon, ob er bereits eine
        # Verteilung hat oder bisher nur als Verfügbarkeitsabfrage existiert.
        alle_termine = set(gruppe.get("verteilung", {}).keys())
        for spieler_eintrag in gruppe.get("players", {}).values():
            alle_termine.update(spieler_eintrag.get("nicht_moeglich", []))

        termin_id_by_datum: dict[str, int] = {}
        for datum_str in alle_termine:
            cur = conn.execute(
                "INSERT INTO termin (gruppe_id, datum) VALUES (?, ?)",
                (gruppe_id, parse_datum(datum_str)),
            )
            termin_id_by_datum[datum_str] = cur.lastrowid
            stats["termine"] += 1

        for alt_spieler_id, eintrag in gruppe.get("players", {}).items():
            spieler_id = get_or_create_spieler_id(conn, spieler_map, alt_spieler_id)
            conn.execute(
                "INSERT OR IGNORE INTO gruppen_mitglied (gruppe_id, spieler_id) VALUES (?, ?)",
                (gruppe_id, spieler_id),
            )
            stats["mitgliedschaften"] += 1
            for datum_str in eintrag.get("nicht_moeglich", []):
                conn.execute(
                    "INSERT INTO nicht_verfuegbar (termin_id, spieler_id) VALUES (?, ?)",
                    (termin_id_by_datum[datum_str], spieler_id),
                )
                stats["nicht_verfuegbar"] += 1

        for datum_str, alt_spieler_ids in gruppe.get("verteilung", {}).items():
            termin_id = termin_id_by_datum[datum_str]
            for alt_spieler_id in alt_spieler_ids:
                spieler_id = get_or_create_spieler_id(conn, spieler_map, alt_spieler_id)
                conn.execute(
                    "INSERT INTO verteilung (termin_id, spieler_id) VALUES (?, ?)",
                    (termin_id, spieler_id),
                )
                stats["verteilungen"] += 1


def main() -> int:
    root = Path(__file__).resolve().parent.parent

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=root / "tennisverteilung.db")
    parser.add_argument("--spieler", type=Path, default=root / "spieler.json")
    parser.add_argument("--force", action="store_true", help="vorhandene DB-Datei überschreiben")
    parser.add_argument(
        "saison_files",
        nargs="*",
        type=Path,
        help="Saison-JSON-Dateien (Default: alle <jahr>.json im Projektwurzelverzeichnis)",
    )
    args = parser.parse_args()

    saison_files = args.saison_files or find_default_season_files(root)
    if not saison_files:
        print("Keine Saison-JSON-Dateien gefunden.")
        return 1

    if args.db.exists():
        if not args.force:
            print(f"FEHLER: {args.db} existiert bereits. --force zum Überschreiben verwenden.")
            return 1
        args.db.unlink()

    print(f"Migriere nach {args.db}")
    print(f"Spielerstamm: {args.spieler}")
    print("Saison-Dateien: " + ", ".join(f.name for f in saison_files))

    conn = connect(args.db)
    create_schema(conn)

    stats: dict = defaultdict(int)
    spieler_map = migrate_spieler(conn, args.spieler)
    stats["spieler (global)"] = len(spieler_map)

    for f in saison_files:
        migrate_saison_file(conn, f, spieler_map, stats)

    conn.commit()
    conn.close()

    print("\nMigration abgeschlossen:")
    for key, value in stats.items():
        print(f"  {key}: {value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
