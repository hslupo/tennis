import sqlite3


class VerteilungRepository:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def fuer_gruppe(self, gruppe_id: int) -> dict[str, list[int]]:
        """Liefert {iso_datum: [spieler_id, ...]} für alle Termine der Gruppe mit Verteilung."""
        rows = self.conn.execute(
            """SELECT t.datum, v.spieler_id FROM verteilung v
               JOIN termin t ON t.id = v.termin_id
               WHERE t.gruppe_id = ?
               ORDER BY t.datum""",
            (gruppe_id,),
        ).fetchall()
        ergebnis: dict[str, list[int]] = {}
        for row in rows:
            ergebnis.setdefault(row["datum"], []).append(row["spieler_id"])
        return ergebnis

    def ersetzen_fuer_termin(self, termin_id: int, spieler_ids: list[int]) -> None:
        self.conn.execute("DELETE FROM verteilung WHERE termin_id = ?", (termin_id,))
        self.conn.executemany(
            "INSERT INTO verteilung (termin_id, spieler_id) VALUES (?, ?)",
            [(termin_id, spieler_id) for spieler_id in spieler_ids],
        )
        self.conn.commit()
