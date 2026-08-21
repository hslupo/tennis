import unittest

from services.termine_service import generiere_termine


class TermineServiceTest(unittest.TestCase):
    def test_reproduziert_bekannte_saison_2025_freitag(self):
        """Regressionstest gegen die real migrierten Daten der Saison 2025 (Gruppe Freitag)."""
        termine = generiere_termine("2025-09-15", "2026-04-26", "Freitag")
        self.assertEqual(len(termine), 32)
        self.assertEqual(termine[0], "19.09.2025")
        self.assertEqual(termine[-1], "24.04.2026")
        self.assertIn("31.10.2025", termine)

    def test_start_faellt_bereits_auf_wochentag(self):
        termine = generiere_termine("2025-09-19", "2025-09-19", "Freitag")
        self.assertEqual(termine, ["19.09.2025"])

    def test_end_vor_start_liefert_leere_liste(self):
        termine = generiere_termine("2025-09-19", "2025-09-01", "Freitag")
        self.assertEqual(termine, [])

    def test_unbekannter_wochentag_liefert_leere_liste(self):
        termine = generiere_termine("2025-09-15", "2026-04-26", "Feiertag")
        self.assertEqual(termine, [])

    def test_alle_termine_liegen_auf_dem_gewaehlten_wochentag(self):
        termine = generiere_termine("2025-01-01", "2025-12-31", "Mittwoch")
        for t in termine:
            tag, monat, jahr = t.split(".")
            import datetime
            self.assertEqual(datetime.date(int(jahr), int(monat), int(tag)).weekday(), 2)


if __name__ == "__main__":
    unittest.main()
