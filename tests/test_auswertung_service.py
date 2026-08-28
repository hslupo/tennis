import unittest

from services.auswertung_service import erstelle_auswertungstext


class AuswertungServiceTest(unittest.TestCase):
    def setUp(self):
        self.saison = {"start_date": "2025-09-15", "end_date": "2025-09-26"}
        self.gruppe = {
            "wochentag": "Freitag",
            "players": {
                1: {"nicht_moeglich": []},
                2: {"nicht_moeglich": ["19.09.2025"]},
            },
        }
        self.spieler_namen = {1: "Anna", 2: "Bert"}

    def test_enthaelt_beide_spieler_im_kopfbereich(self):
        text = erstelle_auswertungstext(self.saison, self.gruppe, self.spieler_namen)
        self.assertIn("Anna: —", text)
        self.assertIn("Bert: 19.09.2025", text)

    def test_termin_mit_allen_verfuegbar(self):
        text = erstelle_auswertungstext(self.saison, self.gruppe, self.spieler_namen)
        self.assertIn("26.09.2025: alle können", text)

    def test_termin_mit_teilweiser_verfuegbarkeit(self):
        text = erstelle_auswertungstext(self.saison, self.gruppe, self.spieler_namen)
        self.assertIn("19.09.2025: Anna", text)

    def test_termin_ohne_verfuegbare_spieler(self):
        gruppe = {
            "wochentag": "Freitag",
            "players": {1: {"nicht_moeglich": ["19.09.2025"]}, 2: {"nicht_moeglich": ["19.09.2025"]}},
        }
        text = erstelle_auswertungstext(self.saison, gruppe, self.spieler_namen)
        self.assertIn("19.09.2025: keiner kann", text)

    def test_fehlende_saison_daten(self):
        text = erstelle_auswertungstext({}, self.gruppe, self.spieler_namen)
        self.assertIn("Keine Saison-Daten", text)

    def test_erstellt_einsatz_und_paarungsstatistik(self):
        gruppe = {
            "wochentag": "Freitag",
            "players": {
                1: {"nicht_moeglich": []},
                2: {"nicht_moeglich": []},
                3: {"nicht_moeglich": []},
            },
            "verteilung": {
                "19.09.2025": [1, 2],
                "26.09.2025": [1, 2, 3],
            },
        }

        text = erstelle_auswertungstext(self.saison, gruppe, self.spieler_namen)

        self.assertIn("Anna: 2 Einsätze; zusammen mit 3: 1, Bert: 2", text)
        self.assertIn("Bert: 2 Einsätze; zusammen mit 3: 1, Anna: 2", text)
        self.assertIn("3: 1 Einsatz; zusammen mit Anna: 1, Bert: 1", text)


if __name__ == "__main__":
    unittest.main()
