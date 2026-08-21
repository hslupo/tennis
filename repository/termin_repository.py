import sqlite3
from collections.abc import Iterable


class TerminRepository:
    """Arbeitet mit ISO-Datumsstrings (YYYY-MM-DD), wie sie in der Tabelle `termin`
    gespeichert sind. Die Umwandlung von/zu Anzeigeformaten übernimmt der Aufrufer."""

    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def ids_fuer_daten(self, gruppe_id: int, iso_daten: Iterable[str]) -> dict[str, int]:
        """Liefert termin_id je Datum, legt fehlende Termine bei Bedarf an."""
        ergebnis: dict[str, int] = {}
        for iso_datum in iso_daten:
            row = self.conn.execute(
                "SELECT id FROM termin WHERE gruppe_id = ? AND datum = ?", (gruppe_id, iso_datum)
            ).fetchone()
            if row is None:
                cur = self.conn.execute(
                    "INSERT INTO termin (gruppe_id, datum) VALUES (?, ?)", (gruppe_id, iso_datum)
                )
                ergebnis[iso_datum] = cur.lastrowid
            else:
                ergebnis[iso_datum] = row["id"]
        self.conn.commit()
        return ergebnis

    def nicht_verfuegbare_iso_daten_fuer_spieler(self, gruppe_id: int, spieler_id: int) -> set[str]:
        rows = self.conn.execute(
            """SELECT t.datum FROM nicht_verfuegbar nv
               JOIN termin t ON t.id = nv.termin_id
               WHERE t.gruppe_id = ? AND nv.spieler_id = ?""",
            (gruppe_id, spieler_id),
        ).fetchall()
        return {row["datum"] for row in rows}

    def nicht_verfuegbar_setzen(self, termin_id: int, spieler_id: int) -> None:
        self.conn.execute(
            "INSERT OR IGNORE INTO nicht_verfuegbar (termin_id, spieler_id) VALUES (?, ?)",
            (termin_id, spieler_id),
        )
        self.conn.commit()

    def nicht_verfuegbar_entfernen(self, termin_id: int, spieler_id: int) -> None:
        self.conn.execute(
            "DELETE FROM nicht_verfuegbar WHERE termin_id = ? AND spieler_id = ?",
            (termin_id, spieler_id),
        )
        self.conn.commit()
