import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from db.connection import connect, create_schema
from repository.gruppe_repository import GruppeRepository
from repository.saison_repository import SaisonRepository
from repository.spieler_repository import SpielerRepository
from repository.termin_repository import TerminRepository
from repository.verteilung_repository import VerteilungRepository


class RepositoryTest(unittest.TestCase):
    def setUp(self):
        self._tmpdir = TemporaryDirectory()
        conn = connect(Path(self._tmpdir.name) / "test.db")
        create_schema(conn)
        self.conn = conn
        self.spieler_repo = SpielerRepository(conn)
        self.saison_repo = SaisonRepository(conn)
        self.gruppe_repo = GruppeRepository(conn)
        self.termin_repo = TerminRepository(conn)
        self.verteilung_repo = VerteilungRepository(conn)

    def tearDown(self):
        self.conn.close()
        self._tmpdir.cleanup()

    def test_spieler_crud(self):
        sid = self.spieler_repo.erstellen("Erna Muster", "Erna", "0123", "0456")
        row = self.spieler_repo.get(sid)
        self.assertEqual(row["name"], "Erna Muster")
        self.assertEqual(row["email"], "")

        self.spieler_repo.aktualisieren(sid, "Erna Neu", "ErnaN", "999", "888", "erna@example.com")
        row = self.spieler_repo.get(sid)
        self.assertEqual(row["name"], "Erna Neu")
        self.assertEqual(row["spitzname"], "ErnaN")
        self.assertEqual(row["email"], "erna@example.com")

        self.spieler_repo.loeschen(sid)
        self.assertIsNone(self.spieler_repo.get(sid))

    def test_saison_upsert_ist_idempotent(self):
        id1 = self.saison_repo.upsert(2025, "2025-09-15", "2026-04-26")
        id2 = self.saison_repo.upsert(2025, "2025-09-16", "2026-04-27")
        self.assertEqual(id1, id2)
        row = self.saison_repo.get_by_jahr(2025)
        self.assertEqual(row["start_date"], "2025-09-16")

    def test_gruppe_upsert_pro_wochentag_eindeutig(self):
        saison_id = self.saison_repo.upsert(2025, "2025-09-15", "2026-04-26")
        g1 = self.gruppe_repo.upsert(saison_id, 4, "Freitag", "3", "16:00", "17:30")
        g2 = self.gruppe_repo.upsert(saison_id, 4, "Freitag", "5", "18:00", "19:30")
        self.assertEqual(g1, g2)
        row = self.gruppe_repo.get(g1)
        self.assertEqual(row["platz"], "5")

    def test_gruppen_mitgliedschaft_und_override(self):
        saison_id = self.saison_repo.upsert(2025, "2025-09-15", "2026-04-26")
        gruppe_id = self.gruppe_repo.upsert(saison_id, 4, "Freitag", "3", "16:00", "17:30")
        horst1 = self.spieler_repo.erstellen("Horst Eins", "Horst")
        horst2 = self.spieler_repo.erstellen("Horst Zwei", "Horst")

        self.gruppe_repo.mitglied_hinzufuegen(gruppe_id, horst1)
        self.gruppe_repo.mitglied_hinzufuegen(gruppe_id, horst2)
        self.gruppe_repo.spitzname_override_setzen(gruppe_id, horst2, "Horst S.")

        mitglieder = {m["spieler_id"]: m["anzeige_name"] for m in self.gruppe_repo.mitglieder_mit_spielerdaten(gruppe_id)}
        self.assertEqual(mitglieder[horst1], "Horst")
        self.assertEqual(mitglieder[horst2], "Horst S.")

        self.gruppe_repo.mitglied_entfernen(gruppe_id, horst1)
        self.assertEqual(self.gruppe_repo.mitglieder_ids(gruppe_id), [horst2])

    def test_termin_get_or_create_ist_idempotent(self):
        saison_id = self.saison_repo.upsert(2025, "2025-09-15", "2026-04-26")
        gruppe_id = self.gruppe_repo.upsert(saison_id, 4, "Freitag", "3", "16:00", "17:30")

        ids1 = self.termin_repo.ids_fuer_daten(gruppe_id, ["2025-09-19", "2025-09-26"])
        ids2 = self.termin_repo.ids_fuer_daten(gruppe_id, ["2025-09-19"])
        self.assertEqual(ids1["2025-09-19"], ids2["2025-09-19"])
        self.assertEqual(len(ids1), 2)

    def test_nicht_verfuegbar_setzen_und_entfernen(self):
        saison_id = self.saison_repo.upsert(2025, "2025-09-15", "2026-04-26")
        gruppe_id = self.gruppe_repo.upsert(saison_id, 4, "Freitag", "3", "16:00", "17:30")
        spieler_id = self.spieler_repo.erstellen("Erna", "Erna")
        termin_ids = self.termin_repo.ids_fuer_daten(gruppe_id, ["2025-09-19", "2025-09-26"])

        self.termin_repo.nicht_verfuegbar_setzen(termin_ids["2025-09-19"], spieler_id)
        daten = self.termin_repo.nicht_verfuegbare_iso_daten_fuer_spieler(gruppe_id, spieler_id)
        self.assertEqual(daten, {"2025-09-19"})

        self.termin_repo.nicht_verfuegbar_entfernen(termin_ids["2025-09-19"], spieler_id)
        daten = self.termin_repo.nicht_verfuegbare_iso_daten_fuer_spieler(gruppe_id, spieler_id)
        self.assertEqual(daten, set())

    def test_verteilung_ersetzen_fuer_termin(self):
        saison_id = self.saison_repo.upsert(2025, "2025-09-15", "2026-04-26")
        gruppe_id = self.gruppe_repo.upsert(saison_id, 4, "Freitag", "3", "16:00", "17:30")
        s1 = self.spieler_repo.erstellen("A", "A")
        s2 = self.spieler_repo.erstellen("B", "B")
        termin_id = self.termin_repo.ids_fuer_daten(gruppe_id, ["2025-09-19"])["2025-09-19"]

        self.verteilung_repo.ersetzen_fuer_termin(termin_id, [s1, s2])
        self.assertEqual(self.verteilung_repo.fuer_gruppe(gruppe_id), {"2025-09-19": [s1, s2]})

        self.verteilung_repo.ersetzen_fuer_termin(termin_id, [s1])
        self.assertEqual(self.verteilung_repo.fuer_gruppe(gruppe_id), {"2025-09-19": [s1]})

    def test_spieler_loeschen_kaskadiert_auf_mitgliedschaft(self):
        saison_id = self.saison_repo.upsert(2025, "2025-09-15", "2026-04-26")
        gruppe_id = self.gruppe_repo.upsert(saison_id, 4, "Freitag", "3", "16:00", "17:30")
        spieler_id = self.spieler_repo.erstellen("Erna", "Erna")
        self.gruppe_repo.mitglied_hinzufuegen(gruppe_id, spieler_id)

        self.spieler_repo.loeschen(spieler_id)

        self.assertEqual(self.gruppe_repo.mitglieder_ids(gruppe_id), [])


if __name__ == "__main__":
    unittest.main()
