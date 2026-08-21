import sqlite3


class SpielerRepository:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def alle(self) -> list[sqlite3.Row]:
        return self.conn.execute(
            "SELECT id, name, spitzname, telefon, mobil, email FROM spieler ORDER BY spitzname COLLATE NOCASE"
        ).fetchall()

    def get(self, spieler_id: int) -> sqlite3.Row | None:
        return self.conn.execute(
            "SELECT id, name, spitzname, telefon, mobil, email FROM spieler WHERE id = ?", (spieler_id,)
        ).fetchone()

    def erstellen(self, name: str, spitzname: str, telefon: str = "", mobil: str = "", email: str = "") -> int:
        cur = self.conn.execute(
            "INSERT INTO spieler (name, spitzname, telefon, mobil, email) VALUES (?, ?, ?, ?, ?)",
            (name, spitzname, telefon, mobil, email),
        )
        self.conn.commit()
        return cur.lastrowid

    def aktualisieren(self, spieler_id: int, name: str, spitzname: str, telefon: str, mobil: str, email: str = "") -> None:
        self.conn.execute(
            "UPDATE spieler SET name = ?, spitzname = ?, telefon = ?, mobil = ?, email = ? WHERE id = ?",
            (name, spitzname, telefon, mobil, email, spieler_id),
        )
        self.conn.commit()

    def loeschen(self, spieler_id: int) -> None:
        self.conn.execute("DELETE FROM spieler WHERE id = ?", (spieler_id,))
        self.conn.commit()
