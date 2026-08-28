"""Importiert Tennis-Verteilungen aus den PDF-Tabellen im Ordner ``import``.

Beispiel:
    python import_pdf_verteilung.py "import/Tennis Dienstag 2026 - 2027.pdf" \
        --map "Viktor=Victor" --map "Göhlig=Horst Göhlig"

Ohne ``--create-missing`` werden unbekannte oder mehrdeutige Namen bewusst als
Fehler gemeldet. Dadurch entstehen keine versehentlichen doppelten Spieler.
"""

from __future__ import annotations

import argparse
import re
from datetime import datetime
from pathlib import Path

from pypdf import PdfReader

from db.connection import connect, create_schema, migrate


WOCHENTAGE = {"dienstag": 1, "sonntag": 6}
DATUM_RE = re.compile(r"^(\d{2}\.\d{2}\.\d{4})\s+(.+)$")
RED_FILL_RE = re.compile(
    r"(?:/Cs6 cs\s+)?\.75294 0 0 scn\s+"
    r"([0-9.]+)\s+([0-9.]+)\s+([0-9.]+)\s+([0-9.]+)\s+re\s+f"
)
RECT_RE = re.compile(r"([0-9.]+)\s+([0-9.]+)\s+([0-9.]+)\s+([0-9.]+)\s+re")
PLAYER_X_CENTERS = {
    "dienstag": (165.6, 210.96, 252.96, 298.74, 346.38, 394.62, 452.58),
    "sonntag": (151.97, 184.83, 217.68, 251.79, 286.23, 325.74, 370.26),
}


def red_cells(path: Path, row_count: int) -> list[set[int]]:
    """Liest rote Tabellenzellen aus dem PDF-Zeichenstrom."""
    data = b"".join(
        page.get_contents().get_data() for page in PdfReader(str(path)).pages
    ).decode("latin1")
    red_rects = [tuple(float(value) for value in match.groups()) for match in RED_FILL_RE.finditer(data)]
    row_ys = sorted(
        {
            round(float(match.group(2)), 2)
            for match in RECT_RE.finditer(data)
            if abs(float(match.group(4)) - 14.64) < 0.3
        },
        reverse=True,
    )
    if len(row_ys) > row_count:
        row_ys = row_ys[-row_count:]
    day_name = next(day for day in WOCHENTAGE if day in path.stem.lower())
    player_centers = PLAYER_X_CENTERS[day_name]
    result: list[set[int]] = []
    for row_y in row_ys:
        result.append(
            {
                column
                for column, center_x in enumerate(player_centers)
                if any(x <= center_x <= x + width and y <= row_y <= y + height for x, y, width, height in red_rects)
            }
        )
    return result


def parse_pdf(path: Path) -> tuple[list[str], list[tuple[str, list[int], set[int]]]]:
    lines: list[str] = []
    for page in PdfReader(str(path)).pages:
        lines.extend((page.extract_text() or "").splitlines())

    rows: list[tuple[str, list[int]]] = []
    header: list[str] | None = None
    for line in lines:
        line = " ".join(line.split())
        match = DATUM_RE.match(line)
        if match:
            compact = re.sub(r"\s+", "", match.group(2))
            if not compact.endswith("4"):
                raise ValueError(f"{path.name}: Kontrollsumme fehlt in Zeile: {line}")
            statuses = compact[:-1]
            if not statuses or any(value not in "01" for value in statuses):
                raise ValueError(f"{path.name}: unbekannte Zellwerte in Zeile: {line}")
            rows.append((match.group(1), [int(value) for value in statuses]))
        elif line and "Stand:" not in line and not line.startswith("20.08.2026"):
            if header is None and not line.startswith(("Dienstag", "Sonntag", "Tennis", "-Tennis", "Wintersaison")):
                header = line.split()

    if header is None or not rows:
        raise ValueError(f"{path.name}: Spieler-Kopfzeile oder Runden fehlen")
    red_by_row = red_cells(path, len(rows))
    if len(red_by_row) != len(rows):
        raise ValueError(f"{path.name}: Tabellenhintergründe konnten nicht vollständig gelesen werden")
    for date_text, statuses in rows:
        if len(statuses) > len(header):
            raise ValueError(f"{path.name}: zu viele Zellwerte am {date_text}")
        if len(statuses) < len(header):
            fehlend = len(header) - len(statuses)
            print(
                f"WARNUNG: {path.name}, {date_text}: {fehlend} fehlender Zellwert "
                "wird als 0 behandelt"
            )
            statuses.extend([0] * fehlend)
    return header, [
        (date_text, statuses, red_by_row[row])
        for row, (date_text, statuses) in enumerate(rows)
    ]


def parse_mapping(values: list[str]) -> dict[str, str]:
    mapping = {}
    for value in values:
        if "=" not in value:
            raise ValueError(f"Ungültige Zuordnung '{value}', erwartet PDF-Name=Projekt-Name")
        source, target = value.split("=", 1)
        mapping[source.strip()] = target.strip()
    return mapping


def resolve_player(conn, source_name: str, mapping: dict[str, str], create_missing: bool) -> int:
    target_name = mapping.get(source_name, source_name)
    rows = conn.execute(
        """SELECT id FROM spieler
           WHERE name = ? COLLATE NOCASE OR spitzname = ? COLLATE NOCASE""",
        (target_name, target_name),
    ).fetchall()
    ids = {row["id"] for row in rows}
    if len(ids) == 1:
        return next(iter(ids))
    if len(ids) > 1:
        raise ValueError(f"Spieler '{source_name}' ist mehrdeutig; bitte --map verwenden")
    if not create_missing:
        raise ValueError(f"Spieler '{source_name}' fehlt; bitte --map oder --create-missing verwenden")
    cur = conn.execute(
        "INSERT INTO spieler (name, spitzname) VALUES (?, ?)",
        (target_name, target_name),
    )
    return cur.lastrowid


def import_pdf(conn, path: Path, mapping: dict[str, str], create_missing: bool) -> int:
    names, rows = parse_pdf(path)
    day_name = next((day for day in WOCHENTAGE if day in path.stem.lower()), None)
    if day_name is None:
        raise ValueError(f"{path.name}: Wochentag nicht im Dateinamen gefunden")

    player_ids = [resolve_player(conn, name, mapping, create_missing) for name in names]
    season_year = datetime.strptime(rows[0][0], "%d.%m.%Y").year
    season = conn.execute("SELECT id FROM saison WHERE jahr = ?", (season_year,)).fetchone()
    dates = [datetime.strptime(value, "%d.%m.%Y").date() for value, _, _ in rows]
    if season is None:
        cur = conn.execute(
            "INSERT INTO saison (jahr, start_date, end_date) VALUES (?, ?, ?)",
            (season_year, min(dates).isoformat(), max(dates).isoformat()),
        )
        season_id = cur.lastrowid
    else:
        season_id = season["id"]

    group = conn.execute(
        "SELECT id FROM gruppe WHERE saison_id = ? AND wochentag = ?",
        (season_id, WOCHENTAGE[day_name]),
    ).fetchone()
    if group is None:
        cur = conn.execute(
            """INSERT INTO gruppe (saison_id, name, wochentag, platz, startzeit, endzeit)
               VALUES (?, ?, ?, '', '', '')""",
            (season_id, day_name.capitalize(), WOCHENTAGE[day_name]),
        )
        group_id = cur.lastrowid
    else:
        group_id = group["id"]

    conn.executemany(
        "INSERT OR IGNORE INTO gruppen_mitglied (gruppe_id, spieler_id) VALUES (?, ?)",
        [(group_id, player_id) for player_id in player_ids],
    )
    for date_text, statuses, red_indices in rows:
        iso_date = datetime.strptime(date_text, "%d.%m.%Y").date().isoformat()
        conn.execute("INSERT OR IGNORE INTO termin (gruppe_id, datum) VALUES (?, ?)", (group_id, iso_date))
        termin = conn.execute(
            "SELECT id FROM termin WHERE gruppe_id = ? AND datum = ?", (group_id, iso_date)
        ).fetchone()
        conn.execute("DELETE FROM verteilung WHERE termin_id = ?", (termin["id"],))
        conn.execute(
            "DELETE FROM nicht_verfuegbar WHERE termin_id = ? AND spieler_id IN ({})".format(",".join("?" * len(player_ids))),
            [termin["id"], *player_ids],
        )
        conn.executemany(
            "INSERT INTO nicht_verfuegbar (termin_id, spieler_id) VALUES (?, ?)",
            [
                (termin["id"], player_id)
                for index, player_id in enumerate(player_ids)
                if statuses[index] == 0 and index in red_indices
            ],
        )
        conn.executemany(
            "INSERT INTO verteilung (termin_id, spieler_id) VALUES (?, ?)",
            [(termin["id"], player_id) for player_id, status in zip(player_ids, statuses) if status == 1],
        )
    conn.commit()
    return len(rows)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf", nargs="+", type=Path)
    parser.add_argument("--db", type=Path, default=Path("tennisverteilung.db"))
    parser.add_argument("--map", action="append", default=[], metavar="PDF=PROJEKT")
    parser.add_argument("--create-missing", action="store_true")
    args = parser.parse_args()

    db_exists = args.db.exists()
    conn = connect(args.db)
    if not db_exists:
        create_schema(conn)
    else:
        migrate(conn)
    try:
        mapping = parse_mapping(args.map)
        for path in args.pdf:
            print(f"{path}: {import_pdf(conn, path, mapping, args.create_missing)} Runden importiert")
    except (OSError, ValueError) as error:
        conn.rollback()
        print(f"FEHLER: {error}")
        return 1
    finally:
        conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())