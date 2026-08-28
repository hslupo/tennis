import sqlite3


class GruppeRepository:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def fuer_saison(self, saison_id: int) -> list[sqlite3.Row]:
        return self.conn.execute(
                """SELECT id, saison_id, name, wochentag, platz, startzeit, endzeit, seed, ist_importiert
               FROM gruppe WHERE saison_id = ? ORDER BY wochentag""",
            (saison_id,),
        ).fetchall()

    def get(self, gruppe_id: int) -> sqlite3.Row | None:
        return self.conn.execute(
                """SELECT id, saison_id, name, wochentag, platz, startzeit, endzeit, seed, ist_importiert
               FROM gruppe WHERE id = ?""",
            (gruppe_id,),
        ).fetchone()

    def get_by_wochentag(self, saison_id: int, wochentag: int) -> sqlite3.Row | None:
        return self.conn.execute(
                """SELECT id, saison_id, name, wochentag, platz, startzeit, endzeit, seed, ist_importiert
               FROM gruppe WHERE saison_id = ? AND wochentag = ?""",
            (saison_id, wochentag),
        ).fetchone()

    def upsert(
        self,
        saison_id: int,
        wochentag: int,
        name: str,
        platz: str,
        startzeit: str,
        endzeit: str,
        seed: int | None = None,
        ist_importiert: bool | None = None,
    ) -> int:
        """Legt die Gruppe für diesen Wochentag an oder überschreibt ihre Eckdaten
        (bildet das bisherige Verhalten nach, bei dem eine Gruppe je Wochentag pro
        Saison eindeutig war)."""
        vorhanden = self.get_by_wochentag(saison_id, wochentag)
        if vorhanden is None:
            cur = self.conn.execute(
                     """INSERT INTO gruppe
                         (saison_id, name, wochentag, platz, startzeit, endzeit, seed, ist_importiert)
                         VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                     (saison_id, name, wochentag, platz, startzeit, endzeit, seed, bool(ist_importiert)),
            )
            self.conn.commit()
            return cur.lastrowid

        if ist_importiert is None:
            self.conn.execute(
                """UPDATE gruppe SET name = ?, platz = ?, startzeit = ?, endzeit = ?, seed = ?
                   WHERE id = ?""",
                (name, platz, startzeit, endzeit, seed, vorhanden["id"]),
            )
        else:
            self.conn.execute(
                """UPDATE gruppe SET name = ?, platz = ?, startzeit = ?, endzeit = ?, seed = ?,
                           ist_importiert = ? WHERE id = ?""",
                (name, platz, startzeit, endzeit, seed, bool(ist_importiert), vorhanden["id"]),
            )
        self.conn.commit()
        return vorhanden["id"]

    def mitglieder_ids(self, gruppe_id: int) -> list[int]:
        rows = self.conn.execute(
            "SELECT spieler_id FROM gruppen_mitglied WHERE gruppe_id = ?", (gruppe_id,)
        ).fetchall()
        return [row["spieler_id"] for row in rows]

    def mitglieder_mit_spielerdaten(self, gruppe_id: int) -> list[sqlite3.Row]:
        """Mitglieder inkl. effektivem Anzeigenamen (Gruppen-Override, sonst globaler Spitzname)."""
        return self.conn.execute(
            """SELECT s.id AS spieler_id, s.name, s.spitzname, s.telefon, s.mobil,
                      gm.spitzname_override,
                      COALESCE(gm.spitzname_override, s.spitzname) AS anzeige_name
               FROM gruppen_mitglied gm
               JOIN spieler s ON s.id = gm.spieler_id
               WHERE gm.gruppe_id = ?
               ORDER BY anzeige_name COLLATE NOCASE""",
            (gruppe_id,),
        ).fetchall()

    def mitglied_hinzufuegen(self, gruppe_id: int, spieler_id: int) -> None:
        self.conn.execute(
            "INSERT OR IGNORE INTO gruppen_mitglied (gruppe_id, spieler_id) VALUES (?, ?)",
            (gruppe_id, spieler_id),
        )
        self.conn.commit()

    def mitglied_entfernen(self, gruppe_id: int, spieler_id: int) -> None:
        self.conn.execute(
            "DELETE FROM gruppen_mitglied WHERE gruppe_id = ? AND spieler_id = ?",
            (gruppe_id, spieler_id),
        )
        self.conn.commit()

    def spitzname_override_setzen(self, gruppe_id: int, spieler_id: int, override: str | None) -> None:
        self.conn.execute(
            "UPDATE gruppen_mitglied SET spitzname_override = ? WHERE gruppe_id = ? AND spieler_id = ?",
            (override or None, gruppe_id, spieler_id),
        )
        self.conn.commit()
