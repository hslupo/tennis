import sqlite3


class SaisonRepository:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def get_by_jahr(self, jahr: int) -> sqlite3.Row | None:
        return self.conn.execute(
            "SELECT id, jahr, start_date, end_date FROM saison WHERE jahr = ?", (jahr,)
        ).fetchone()

    def alle(self) -> list[sqlite3.Row]:
        return self.conn.execute(
            "SELECT id, jahr, start_date, end_date FROM saison ORDER BY jahr DESC"
        ).fetchall()

    def upsert(self, jahr: int, start_date: str, end_date: str) -> int:
        """Legt die Saison an oder aktualisiert Start-/Enddatum, falls sie bereits existiert."""
        vorhanden = self.get_by_jahr(jahr)
        if vorhanden is None:
            cur = self.conn.execute(
                "INSERT INTO saison (jahr, start_date, end_date) VALUES (?, ?, ?)",
                (jahr, start_date, end_date),
            )
            self.conn.commit()
            return cur.lastrowid

        self.conn.execute(
            "UPDATE saison SET start_date = ?, end_date = ? WHERE id = ?",
            (start_date, end_date, vorhanden["id"]),
        )
        self.conn.commit()
        return vorhanden["id"]
