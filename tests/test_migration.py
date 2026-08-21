import sqlite3
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from db.connection import connect, create_schema
from db.migrate_json_to_sqlite import migrate_saison_file, migrate_spieler

FIXTURES = Path(__file__).parent / "fixtures"


class MigrationTest(unittest.TestCase):
    def setUp(self):
        self._tmpdir = TemporaryDirectory()
        db_path = Path(self._tmpdir.name) / "test.db"
        self.conn = connect(db_path)
        create_schema(self.conn)
        self.spieler_map = migrate_spieler(self.conn, FIXTURES / "spieler_beispiel.json")
        self.stats: dict = {}
        for key in ("saisons", "gruppen", "termine", "mitgliedschaften", "nicht_verfuegbar", "verteilungen"):
            self.stats[key] = 0
        migrate_saison_file(self.conn, FIXTURES / "saison_beispiel.json", self.spieler_map, self.stats)
        self.conn.commit()

    def tearDown(self):
        self.conn.close()
        self._tmpdir.cleanup()

    def test_row_counts_match_source_json(self):
        self.assertEqual(len(self.spieler_map), 10)
        self.assertEqual(self.stats["saisons"], 1)
        self.assertEqual(self.stats["gruppen"], 2)
        self.assertEqual(self.stats["termine"], 32)
        self.assertEqual(self.stats["mitgliedschaften"], 8)
        self.assertEqual(self.stats["nicht_verfuegbar"], 22)
        self.assertEqual(self.stats["verteilungen"], 128)

    def test_foreign_keys_are_consistent(self):
        verletzungen = self.conn.execute("PRAGMA foreign_key_check").fetchall()
        self.assertEqual(verletzungen, [])

    def test_duplicate_display_names_stay_distinct_players(self):
        rows = self.conn.execute("SELECT id FROM spieler WHERE name = 'SpielerB'").fetchall()
        self.assertEqual(len(rows), 2)

    def test_empty_group_has_no_termine(self):
        gruppe = self.conn.execute("SELECT id FROM gruppe WHERE name = 'Dienstag'").fetchone()
        termine = self.conn.execute("SELECT * FROM termin WHERE gruppe_id = ?", (gruppe["id"],)).fetchall()
        self.assertEqual(termine, [])

    def test_verteilung_references_correct_players(self):
        termin = self.conn.execute("SELECT id FROM termin WHERE datum = '2025-09-19'").fetchone()
        namen = {
            row["name"]
            for row in self.conn.execute(
                """SELECT s.name FROM verteilung v
                   JOIN spieler s ON s.id = v.spieler_id
                   WHERE v.termin_id = ?""",
                (termin["id"],),
            )
        }
        self.assertEqual(namen, {"SpielerB", "SpielerD", "SpielerE", "SpielerJ"})


if __name__ == "__main__":
    unittest.main()
